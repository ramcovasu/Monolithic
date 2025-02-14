import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any
import json
from sqldataeng import SQLChunk
import os
import torch
from sentence_transformers import SentenceTransformer

# Patch torch._classes to avoid Streamlit file watcher error
import sys
import torch._classes
if not hasattr(torch._classes, '__path__'):
    torch._classes.__path__ = []

class VectorStoreManager:
    def __init__(self, 
                 persist_directory: str = "chroma_db",
                 embedding_model_name: str = 'BAAI/bge-small-en-v1.5',
                 cache_folder: str = './embedding_models'):
        self.persist_directory = persist_directory
        
        # Create cache folder if it doesn't exist
        os.makedirs(cache_folder, exist_ok=True)
        
        # Set device
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Using device: {self.device}")
        
        # Initialize the embedding model
        self.embedding_model = SentenceTransformer(
            embedding_model_name,
            cache_folder=cache_folder
        ).to(self.device)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Create or get collections
        self.chunks_collection = self.client.get_or_create_collection(
            name="sql_chunks"
        )
        
        self.lineage_collection = self.client.get_or_create_collection(
            name="sql_lineage"
        )

    def _prepare_chunk_metadata(self, chunk: SQLChunk) -> Dict[str, Any]:
        """Convert chunk metadata to format suitable for ChromaDB"""
        return {
            "chunk_type": chunk.chunk_type,
            "name": chunk.name,
            "start_line": str(chunk.start_line),
            "end_line": str(chunk.end_line),
            "dependencies": json.dumps(chunk.dependencies),
            "parent_chunk": chunk.parent_chunk if chunk.parent_chunk else ""
        }

    def add_chunks(self, chunks: List[SQLChunk], batch_size: int = 100) -> None:
        """Add SQL chunks to the vector store with batch processing"""
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            ids = []
            documents = []
            metadatas = []
            embeddings = []
            
            for chunk in batch:
                chunk_id = f"chunk_{len(ids)}_{chunk.name.lower().replace(' ', '_')}"
                # Generate embedding using sentence transformer
                embedding = self.embedding_model.encode(
                    chunk.content,
                    device=self.device
                ).tolist()
                
                ids.append(chunk_id)
                documents.append(chunk.content)
                metadatas.append(self._prepare_chunk_metadata(chunk))
                embeddings.append(embedding)

            # Add to ChromaDB
            self.chunks_collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )

    def build_lineage_graph(self, chunks: List[SQLChunk]) -> None:
        """Build and store dependency relationships"""
        nodes = set()
        edges = set()
        
        for chunk in chunks:
            nodes.add(chunk.name)
            for dep in chunk.dependencies:
                nodes.add(dep)
                edges.add((chunk.name, dep))
        
        lineage_entries = []
        for node in nodes:
            incoming = [edge[0] for edge in edges if edge[1] == node]
            outgoing = [edge[1] for edge in edges if edge[0] == node]
            
            lineage_info = {
                "object": node,
                "incoming_dependencies": incoming,
                "outgoing_dependencies": outgoing
            }
            
            # Generate embedding for lineage info
            embedding = self.embedding_model.encode(
                json.dumps(lineage_info),
                device=self.device
            ).tolist()
            
            lineage_entries.append({
                "id": f"lineage_{node.lower().replace(' ', '_')}",
                "document": json.dumps(lineage_info),
                "metadata": {
                    "object_name": node,
                    "dependency_count": str(len(incoming) + len(outgoing))
                },
                "embedding": embedding
            })
        
        if lineage_entries:
            self.lineage_collection.add(
                ids=[entry["id"] for entry in lineage_entries],
                documents=[entry["document"] for entry in lineage_entries],
                metadatas=[entry["metadata"] for entry in lineage_entries],
                embeddings=[entry["embedding"] for entry in lineage_entries]
            )

    def query_similar_chunks(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Query for similar chunks based on text"""
        query_embedding = self.embedding_model.encode(
            query_text,
            device=self.device
        ).tolist()
        
        results = self.chunks_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        return [
            {
                "chunk_content": doc,
                "metadata": meta,
                "distance": distance
            }
            for doc, meta, distance in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )
        ]

    def get_object_lineage(self, object_name: str) -> Dict[str, Any]:
        """Get lineage information for a specific object"""
        query_embedding = self.embedding_model.encode(
            object_name,
            device=self.device
        ).tolist()
        
        results = self.lineage_collection.query(
            query_embeddings=[query_embedding],
            n_results=1
        )
        
        if results["documents"]:
            return json.loads(results["documents"][0][0])
        return {}

    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """Retrieve all stored chunks"""
        results = self.chunks_collection.get()
        return [
            {
                "id": id,
                "content": doc,
                "metadata": meta
            }
            for id, doc, meta in zip(
                results["ids"],
                results["documents"],
                results["metadatas"]
            )
        ]

    def clear_collections(self) -> None:
        """Clear all data from collections"""
        self.client.delete_collection("sql_chunks")
        self.client.delete_collection("sql_lineage")
        
        # Recreate collections
        self.chunks_collection = self.client.get_or_create_collection(name="sql_chunks")
        self.lineage_collection = self.client.get_or_create_collection(name="sql_lineage")

def process_chunks(chunks: List[SQLChunk], persist_dir: str = "chroma_db") -> VectorStoreManager:
    """Process SQL chunks and store in vector database"""
    vector_store = VectorStoreManager(persist_dir)
    vector_store.clear_collections()
    vector_store.add_chunks(chunks)
    vector_store.build_lineage_graph(chunks)
    return vector_store