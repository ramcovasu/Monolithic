# SQL Code Analysis and Documentation Generator

A powerful tool for analyzing, documenting, and visualizing SQL codebase structure and dependencies. This project combines modern language models with vector storage to provide comprehensive insights into SQL code architecture.

## Features

- **Intelligent SQL Parsing**: Automatically breaks down SQL files into logical chunks (packages, procedures, functions)
- **Dependency Analysis**: Identifies and visualizes relationships between different SQL objects
- **Vector-Based Storage**: Uses ChromaDB for efficient storage and retrieval of code chunks
- **LLM-Powered Analysis**: Leverages language models to provide detailed code analysis and insights
- **Interactive Documentation**: Generates comprehensive HTML documentation with interactive components
- **Streamlit Interface**: User-friendly web interface for uploading and analyzing SQL files

## Architecture

The project consists of several key components:

- `sqldataeng.py`: SQL parsing and chunk extraction
- `vectorstore.py`: Vector storage implementation using ChromaDB
- `llmprocessor.py`: Language model integration for code analysis
- `docgenerator.py`: Documentation generation and formatting
- `main.py`: Streamlit web interface

## Prerequisites

- Python 3.8+
- CUDA-capable GPU (optional, for faster processing)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/sql-code-analysis.git
cd sql-code-analysis
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Streamlit application:
```bash
streamlit run main.py --server.fileWatcherType none
```

2. Open your browser and navigate to `http://localhost:8501`

3. Upload your SQL file through the web interface

4. Follow the step-by-step process:
   - Parse SQL code
   - Process and store chunks
   - Generate analysis
   - View and download documentation

## Key Features

### SQL Parsing
- Intelligent package and procedure detection
- Accurate dependency tracking
- Support for complex SQL structures

### Vector Storage
- Efficient code chunk storage
- Semantic similarity search
- Dependency graph construction

### Documentation Generation
- Comprehensive HTML reports
- Interactive visualizations
- Detailed code analysis
- Dependency diagrams

## Technical Details

### Embedding Model
- Uses BAAI/bge-small-en-v1.5 for embeddings
- Supports GPU acceleration when available
- Efficient batch processing

### Vector Storage
- ChromaDB for persistent storage
- Optimized for code similarity search
- Efficient metadata handling

### LLM Integration
- Local LLM support via LM Studio
- Batched processing for large codebases
- Error handling and retry logic

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- ChromaDB for vector storage
- Sentence Transformers for embeddings
- Streamlit for the web interface
- SQLParse for SQL parsing

## Project Structure

```
sql-code-analysis/
├── main.py              # Streamlit application
├── sqldataeng.py       # SQL parsing engine
├── vectorstore.py      # Vector storage management
├── llmprocessor.py     # LLM integration
├── docgenerator.py     # Documentation generator
├── requirements.txt    # Project dependencies
└── README.md          # This file
```

## Future Enhancements

- Support for additional SQL dialects
- Enhanced visualization options
- Code quality metrics
- Performance optimization suggestions
- Batch processing for multiple files

## Contact

Create an issue in the repository for bug reports, feature requests, or general questions.