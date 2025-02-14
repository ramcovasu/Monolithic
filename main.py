import streamlit as st
from sqldataeng import SQLParser, SQLChunk
from vectorstore import VectorStoreManager
from llmprocessor import LLMProcessor
from docgenerator import DocumentationGenerator
import os
from typing import List, Dict, Any
import json

st.set_page_config(page_title="SQL Code Analyzer", layout="wide")

def initialize_session_state():
    """Initialize session state variables"""
    if "current_step" not in st.session_state:
        st.session_state.current_step = 0
    if "sql_chunks" not in st.session_state:
        st.session_state.sql_chunks = None
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None
    if "documentation" not in st.session_state:
        st.session_state.documentation = None

def parse_sql_file(sql_content: str) -> List[SQLChunk]:
    """Parse SQL file into chunks"""
    parser = SQLParser(sql_content)
    chunks = parser.parse_sql()
    chunks.extend(parser.identify_package_body_chunks(chunks))
    return chunks

def process_and_store_chunks(chunks: List[SQLChunk]) -> VectorStoreManager:
    """Process chunks and store in vector database"""
    persist_dir = "chroma_db"
    vector_store = VectorStoreManager(persist_dir)
    vector_store.clear_collections()
    vector_store.add_chunks(chunks)
    vector_store.build_lineage_graph(chunks)
    return vector_store

def analyze_with_llm(vector_store: VectorStoreManager) -> Dict[str, Any]:
    """Process chunks with LLM for analysis"""
    llm = LLMProcessor()
    return llm.process_all_chunks(vector_store)

def generate_documentation(analysis_results: Dict[str, Any]) -> str:
    """Generate final documentation"""
    doc_generator = DocumentationGenerator(analysis_results)
    return doc_generator.generate_html_doc()

def main():
    st.title("SQL Code Analysis & Documentation Generator")
    initialize_session_state()

    # Progress tracking
    steps = ["Upload SQL", "Parse & Store", "Analyze", "Generate Documentation"]
    col1, col2, col3, col4 = st.columns(4)
    for idx, step in enumerate([col1, col2, col3, col4]):
        with step:
            if idx < st.session_state.current_step:
                st.success(steps[idx])
            elif idx == st.session_state.current_step:
                st.info(steps[idx])
            else:
                st.empty()

    # Step 1: File Upload
    if st.session_state.current_step == 0:
        uploaded_file = st.file_uploader("Upload SQL file", type=['sql'])
        if uploaded_file:
            with st.spinner("Parsing SQL file..."):
                try:
                    sql_content = uploaded_file.read().decode('utf-8')
                    parser = SQLParser(sql_content)
                    st.session_state.sql_chunks = parser.parse_sql()
                    num_chunks = len(st.session_state.sql_chunks)
                    num_procedures = sum(1 for chunk in st.session_state.sql_chunks if chunk.chunk_type == 'PROCEDURE')
                    st.success(f"Successfully parsed {num_chunks} code chunks ({num_procedures} procedures)")
                    st.session_state.current_step = 1
                    st.rerun()
                except Exception as e:
                    st.error(f"Error parsing SQL file: {str(e)}")
                    return

    # Step 2: Process and Store
    elif st.session_state.current_step == 1:
        if st.session_state.sql_chunks:
            with st.spinner("Processing and storing chunks..."):
                st.session_state.vector_store = process_and_store_chunks(st.session_state.sql_chunks)
                st.success("Successfully stored chunks in vector database")
                st.session_state.current_step = 2
                st.rerun()

    # Step 3: LLM Analysis
    elif st.session_state.current_step == 2:
        if st.session_state.vector_store:
            # Check if vector store has content
            test_chunks = st.session_state.vector_store.get_all_chunks()
            if not test_chunks:
                st.error("No chunks found in vector store. Please process the document first.")
                st.session_state.current_step = 1
                st.rerun()
                return
                
            with st.spinner("Analyzing code with LLM..."):
                try:
                    # Get analysis results
                    analysis_results = analyze_with_llm(st.session_state.vector_store)
                    
                    # Save results regardless of structure - we know LLM is returning valid analysis
                    st.session_state.analysis_results = analysis_results
                    
                    # Show success and move to next step
                    num_chunks = len(test_chunks)
                    st.success(f"Successfully analyzed {num_chunks} code chunks")
                    st.session_state.current_step = 3
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error during analysis: {str(e)}")
                    return

    # Step 4: Documentation Generation
    elif st.session_state.current_step == 3:
        if st.session_state.analysis_results:
            with st.spinner("Generating documentation..."):
                documentation = generate_documentation(st.session_state.analysis_results)
                
                # Display documentation
                st.markdown("### Documentation Preview")
                st.components.v1.html(documentation, height=600, scrolling=True)
                
                # Save button
                if st.download_button(
                    label="Download Documentation",
                    data=documentation,
                    file_name="sql_documentation.html",
                    mime="text/html"
                ):
                    st.success("Documentation downloaded successfully!")

            # Reset button
            if st.button("Start New Analysis"):
                for key in st.session_state.keys():
                    del st.session_state[key]
                st.rerun()

if __name__ == "__main__":
    main()