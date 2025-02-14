from typing import Dict, Any
import json
from datetime import datetime
import graphviz
from pathlib import Path

class DocumentationGenerator:
    def __init__(self, analysis_results: Dict[str, Any]):
        self.results = analysis_results
        self.chunk_analyses = analysis_results.get("chunk_analyses", {})
        self.overall_summary = analysis_results.get("overall_summary", "")

    def generate_html_doc(self) -> str:
        """Generate HTML documentation with improved styling and structure"""
        doc = []
        
        # Header with CSS
        doc.append("""
        <html>
        <head>
            <title>SQL Code Documentation</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 40px;
                    line-height: 1.6;
                    color: #333;
                    background-color: #fff;
                }
                .section { 
                    margin-bottom: 30px;
                    background: #fff;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .object-card { 
                    border: 1px solid #e1e4e8;
                    padding: 20px;
                    margin: 15px 0;
                    border-radius: 6px;
                    background: #f8f9fa;
                }
                .metadata { 
                    color: #666;
                    font-size: 0.9em;
                    margin: 10px 0;
                    padding: 10px;
                    background: #f1f1f1;
                    border-radius: 4px;
                }
                .summary { margin: 15px 0; }
                .summary h3 { color: #0366d6; }
                .lineage { 
                    margin-top: 15px;
                    padding-top: 15px;
                    border-top: 1px solid #e1e4e8;
                }
                h1, h2 { 
                    color: #24292e;
                    border-bottom: 2px solid #e1e4e8;
                    padding-bottom: 0.3em;
                }
                h3, h4 { color: #24292e; }
                pre {
                    background: #f6f8fa;
                    padding: 16px;
                    border-radius: 6px;
                    overflow-x: auto;
                }
                .toc {
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 6px;
                    margin: 20px 0;
                }
                .toc ul { padding-left: 20px; }
                .toc li { margin: 5px 0; }
            </style>
        </head>
        <body>
        """)

        # Title and Overview
        doc.append(f"""
        <div class="section">
            <h1>SQL Code Documentation</h1>
            <h2>Overview</h2>
            <div class="summary">
                {self._format_content(self.overall_summary)}
            </div>
        </div>
        """)

        # Table of Contents
        doc.append('<div class="section toc"><h2>Table of Contents</h2><ul>')
        # Group by type
        types = {}
        for chunk_id, chunk_data in self.chunk_analyses.items():
            chunk_type = chunk_data["metadata"]["chunk_type"]
            if chunk_type not in types:
                types[chunk_type] = []
            types[chunk_type].append(chunk_data)
        
        for chunk_type in sorted(types.keys()):
            doc.append(f'<li><a href="#{chunk_type.lower()}">{chunk_type}s</a></li>')
        doc.append("</ul></div>")

        # Detailed Documentation by Type
        for chunk_type, chunks in sorted(types.items()):
            doc.append(f"""
            <div class="section" id="{chunk_type.lower()}">
                <h2>{chunk_type}s</h2>
            """)

            for chunk_data in chunks:
                metadata = chunk_data["metadata"]
                analysis = chunk_data["analysis"]
                
                doc.append(f"""
                <div class="object-card">
                    <h3>{metadata["name"]}</h3>
                    <div class="metadata">
                        <p><strong>Lines:</strong> {metadata["start_line"]} - {metadata["end_line"]}</p>
                        <p><strong>Dependencies:</strong> {metadata["dependencies"]}</p>
                    </div>
                    <div class="summary">
                        <h4>Summary</h4>
                        {self._format_content(analysis["summary"])}
                    </div>
                    <div class="lineage">
                        <h4>Lineage Analysis</h4>
                        {self._format_content(analysis["lineage_analysis"])}
                    </div>
                </div>
                """)

            doc.append("</div>")

        # Footer
        doc.append(f"""
        <div class="section" style="text-align: center; color: #666;">
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        </body>
        </html>
        """)

        return "\n".join(doc)

    def _format_content(self, content: str) -> str:
        """Format markdown content to proper HTML with consistent formatting"""
        if not content:
            return "<p>No content available.</p>"
            
        lines = content.split('\n')
        formatted_lines = []
        list_level = 0
        in_code_block = False
        
        for line in lines:
            line = line.rstrip()
            
            # Handle code blocks
            if line.startswith('```'):
                if in_code_block:
                    formatted_lines.append('</pre></code>')
                    in_code_block = False
                else:
                    formatted_lines.append('<code><pre class="code-block">')
                    in_code_block = True
                continue
                
            if in_code_block:
                formatted_lines.append(line)
                continue
            
            # Handle headers
            if line.startswith('# '):
                line = f'<h1>{line[2:]}</h1>'
            elif line.startswith('## '):
                line = f'<h2>{line[3:]}</h2>'
            elif line.startswith('### '):
                line = f'<h3>{line[4:]}</h3>'
            elif line.startswith('#### '):
                line = f'<h4>{line[5:]}</h4>'
            
            # Handle lists
            elif line.strip().startswith('* '):
                indent = len(line) - len(line.lstrip())
                new_level = indent // 2
                
                # Close lists if needed
                while list_level > new_level:
                    formatted_lines.append('</ul>')
                    list_level -= 1
                
                # Open new lists if needed
                while list_level < new_level:
                    formatted_lines.append('<ul class="nested-list">')
                    list_level += 1
                
                line = f'<li>{line.strip()[2:]}</li>'
            
            # Handle regular paragraphs
            elif line.strip():
                if list_level > 0:
                    formatted_lines.append('</ul>' * list_level)
                    list_level = 0
                line = f'<p>{line}</p>'
            
            if line.strip():
                formatted_lines.append(line)
        
        # Close any open lists
        if list_level > 0:
            formatted_lines.append('</ul>' * list_level)
        
        return '\n'.join(formatted_lines)
        
def generate_documentation(analysis_results: Dict[str, Any]) -> str:
    """Generate documentation"""
    doc_generator = DocumentationGenerator(analysis_results)
    return doc_generator.generate_html_doc()