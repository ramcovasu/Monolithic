from typing import List, Dict, Any, Tuple
from openai import OpenAI
from sqldataeng import SQLChunk
from vectorstore import VectorStoreManager
import json
from tqdm import tqdm
import time

class LLMProcessor:
    def __init__(self, base_url: str = "http://localhost:1234/v1", max_tokens_per_batch: int = 5000):
        """Initialize LLM processor using OpenAI-style API for LMStudio"""
        self.client = OpenAI(
            base_url=base_url,
            api_key="lm-studio"
        )
        self.max_tokens_per_batch = max_tokens_per_batch

    def _estimate_tokens(self, text: str) -> int:
        """Estimate tokens (chars/4 is a common approximation)"""
        return len(text) // 4

    def _batch_chunks(self, chunks: List[Tuple[str, SQLChunk, Dict]]) -> List[List[Tuple[str, SQLChunk, Dict]]]:
        """Batch chunks together while respecting token limits"""
        print(f"\nStarting to batch {len(chunks)} total chunks...")
        batches = []
        current_batch = []
        current_token_count = 0
        
        # Initial prompt tokens
        base_prompt_tokens = self._estimate_tokens(
            """Analyze the following SQL code chunks. For each chunk, provide:
            1. Main purpose and functionality
            2. Key operations and business logic
            3. Error handling approach
            4. Dependencies and interactions
            """
        )
        
        for chunk_id, chunk, lineage in chunks:
            # Calculate tokens for this chunk
            content_tokens = self._estimate_tokens(chunk.content)
            chunk_overhead = self._estimate_tokens(
                f"\n--- BEGIN CHUNK: {chunk.name} ({chunk.chunk_type}) ---\n" +
                f"Dependencies: {json.dumps(lineage, indent=2)}\n" +
                "Code:\n" +
                f"--- END CHUNK: {chunk.name} ---\n"
            )
            total_chunk_tokens = content_tokens + chunk_overhead
            
            print(f"Chunk {chunk.name}: {total_chunk_tokens} estimated tokens")
            
            # If adding this chunk would exceed token limit, start new batch
            if current_token_count + total_chunk_tokens + base_prompt_tokens > self.max_tokens_per_batch:
                if current_batch:
                    batches.append(current_batch)
                    print(f"Created batch of {len(current_batch)} chunks with {current_token_count} estimated tokens")
                current_batch = [(chunk_id, chunk, lineage)]
                current_token_count = total_chunk_tokens + base_prompt_tokens
            else:
                current_batch.append((chunk_id, chunk, lineage))
                current_token_count += total_chunk_tokens
        
        if current_batch:
            batches.append(current_batch)
            print(f"Created final batch of {len(current_batch)} chunks with {current_token_count} estimated tokens")
        
        print(f"Created {len(batches)} total batches")
        return batches

    def _create_chunk_analysis_prompt(self, chunk: SQLChunk, lineage: Dict) -> str:
        """Create a prompt for analyzing a SQL chunk"""
        if chunk.chunk_type == 'PACKAGE':
            return self._create_package_analysis_prompt(chunk, lineage)
        else:
            return self._create_procedure_analysis_prompt(chunk, lineage)

    def _create_package_analysis_prompt(self, chunk: SQLChunk, lineage: Dict) -> str:
        """Create analysis prompt for package"""
        return f"""Analyze this SQL package and provide a high-level overview with proper markdown formatting.

# Package Overview

Provide a brief introduction to {chunk.name}'s main purpose and responsibilities.

## Architecture and Design
* Modular Structure
* Design Patterns
* Code Organization

## Key Components
* Package Specification
  - Public Procedures
  - Public Functions
  - Types and Constants
* Package Body
  - Implementation Details
  - Error Handling Approach
  - Validation Strategy

## Business Logic
* Main Operations
* Data Flow
* Integration Points

## Technical Analysis
* Dependencies: {json.dumps(lineage, indent=2)}
* Error Handling Strategy
* Performance Considerations

Please ensure:
1. Use proper markdown headers (# for main sections, ## for subsections)
2. Use bullet points (*) with consistent indentation
3. Keep paragraphs properly aligned
4. Use code blocks for SQL examples

Code to analyze:
{chunk.content}"""

    def _create_procedure_analysis_prompt(self, chunk: SQLChunk, lineage: Dict) -> str:
        """Create analysis prompt for procedure"""
        return f"""Analyze this {chunk.chunk_type.lower()} from package {chunk.parent_chunk} using this format:

### {chunk.chunk_type} Overview
[Provide a brief introduction to {chunk.name}'s purpose]

### Parameters
[List and describe each parameter]

### Business Logic
- Main Operations:
  [Describe the key operations performed]
- Validation Rules:
  [List input validation and business rules]
- Error Handling:
  [Explain specific error handling]

### Technical Implementation
- Database Operations:
  [Describe interactions with database objects]
- Dependencies:
  [List dependencies: {json.dumps(lineage, indent=2)}]
- Performance Considerations:
  [Note any performance-related aspects]

Code to analyze:
{chunk.content}

Please provide a detailed analysis focusing on this specific {chunk.chunk_type.lower()}."""

    def _get_llm_response(self, prompt: str, max_retries: int = 3, timeout: int = 300) -> str:
        """Get response from local LLM with retries and timeout"""
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="local-model",
                    messages=[
                        {"role": "system", "content": "You are a helpful SQL code analysis assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    timeout=timeout
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    raise

    def process_all_chunks(self, vector_store: VectorStoreManager) -> Dict[str, Any]:
        """Process all chunks and generate comprehensive analysis"""
        try:
            all_chunks = vector_store.get_all_chunks()
            results = {}
            
            print(f"\nFound {len(all_chunks)} chunks to process")
            
            # Process chunks one at a time for better reliability
            for chunk_data in all_chunks:
                try:
                    chunk_id = chunk_data["id"]
                    chunk_content = chunk_data["content"]
                    metadata = chunk_data["metadata"]
                    
                    print(f"\nProcessing chunk: {metadata['name']}")
                    
                    chunk = SQLChunk(
                        chunk_type=metadata["chunk_type"],
                        name=metadata["name"],
                        content=chunk_content,
                        start_line=int(metadata["start_line"]),
                        end_line=int(metadata["end_line"]),
                        dependencies=json.loads(metadata["dependencies"]),
                        parent_chunk=metadata["parent_chunk"] if metadata["parent_chunk"] else None
                    )
                    
                    # Get lineage information
                    lineage_info = vector_store.get_object_lineage(chunk.name)
                    
                    # Generate analysis for this chunk
                    prompt = self._create_chunk_analysis_prompt(chunk, lineage_info)
                    print(f"Sending prompt to LLM for {chunk.name}")
                    response = self._get_llm_response(prompt)
                    print(f"Received response for {chunk.name}")
                    
                    # Store results with correct structure
                    results[chunk_id] = {
                        "metadata": metadata,
                        "analysis": {
                            "summary": response,
                            "lineage_analysis": json.dumps(lineage_info, indent=2)
                        }
                    }
                    print(f"Stored results for {chunk.name}")
                    
                except Exception as e:
                    print(f"Error processing chunk {metadata['name']}: {str(e)}")
                    results[chunk_id] = {
                        "metadata": metadata,
                        "analysis": {
                            "summary": f"Error during analysis: {str(e)}",
                            "lineage_analysis": "Error during analysis"
                        }
                    }
            
            print(f"\nProcessed {len(results)} chunks successfully")
            
            # Create final results with required structure
            final_results = {
                "chunk_analyses": results,
                "overall_summary": self.generate_overall_summary(results)
            }
            
            return final_results
            
        except Exception as e:
            print(f"Error in process_all_chunks: {str(e)}")
            # Return minimal valid structure
            return {
                "chunk_analyses": {},
                "overall_summary": f"Error during analysis: {str(e)}"
            }

    def generate_overall_summary(self, chunk_results: Dict[str, Any]) -> str:
        """Generate overall summary of the entire SQL codebase"""
        try:
            overview = "Analyze this SQL codebase summary and provide a comprehensive overview:\n\n"
            
            # Add summaries by type
            for chunk_id, chunk_data in chunk_results.items():
                chunk_type = chunk_data["metadata"]["chunk_type"]
                chunk_name = chunk_data["metadata"]["name"]
                chunk_summary = chunk_data["analysis"]["summary"][:200]  # First 200 chars
                overview += f"\n{chunk_type}: {chunk_name}\n{chunk_summary}...\n"
            
            prompt = f"""{overview}

Provide a comprehensive overview including:
1. Overall architecture and design patterns
2. Key business processes
3. Data flow patterns
4. Notable features and complexities
5. Potential areas of interest

Focus on high-level insights and architectural patterns."""

            return self._get_llm_response(prompt)
        except Exception as e:
            return f"Error generating overall summary: {str(e)}"

def process_with_llm(vector_store: VectorStoreManager) -> Dict[str, Any]:
    """Main processing function"""
    llm = LLMProcessor()
    return llm.process_all_chunks(vector_store)  # Already returns correct structure