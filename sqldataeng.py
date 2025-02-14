import re
from dataclasses import dataclass
from typing import List, Dict, Optional
import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, DML, DDL

@dataclass
class SQLChunk:
    chunk_type: str  # PACKAGE, PROCEDURE, etc.
    name: str
    content: str
    start_line: int
    end_line: int
    dependencies: List[str]
    parent_chunk: Optional[str] = None

class SQLParser:
    def __init__(self, sql_content: str):
        self.sql_content = sql_content
        self.original_lines = sql_content.split('\n')
        print("Initializing SQL Parser...")

    def _get_statement_type(self, stmt: Statement) -> Optional[str]:
        """Get the type of SQL statement"""
        for token in stmt.tokens:
            if token.is_group:
                for subtoken in token.tokens:
                    if subtoken.ttype is Keyword and subtoken.value.upper() in ['CREATE', 'ALTER', 'DROP']:
                        next_token = self._find_next_keyword(token)
                        if next_token:
                            return next_token.upper()
            elif token.ttype is Keyword and token.value.upper() in ['PACKAGE', 'PACKAGE BODY', 'PROCEDURE', 'FUNCTION']:
                return token.value.upper()
        return None

    def _find_next_keyword(self, token_list) -> Optional[str]:
        """Find next keyword in token list"""
        for token in token_list.tokens:
            if token.ttype is Keyword and token.value.upper() in ['PACKAGE', 'PACKAGE BODY', 'PROCEDURE', 'FUNCTION']:
                return token.value
        return None

    def _extract_object_name(self, stmt: Statement) -> str:
        """Extract object name from statement"""
        for token in stmt.tokens:
            if token.ttype is None and not token.is_whitespace:
                return token.value.strip('"')
        return "UNKNOWN"

    def _extract_dependencies_from_content(self, content: str) -> List[str]:
        """Extract all dependencies from SQL content"""
        dependencies = set()
        
        # Tables in FROM/JOIN/UPDATE/INTO clauses
        table_pattern = r'\b(?:FROM|JOIN|UPDATE|INTO)\s+([a-zA-Z_]\w*)'
        for match in re.finditer(table_pattern, content, re.IGNORECASE):
            table_name = match.group(1)
            if table_name.upper() not in ['DUAL']:
                dependencies.add(table_name)

        # Package/Procedure references
        ref_pattern = r'\b(?:CALL|EXECUTE)\s+([a-zA-Z_]\w*\.[a-zA-Z_]\w*)'
        for match in re.finditer(ref_pattern, content, re.IGNORECASE):
            dependencies.add(match.group(1))

        return list(dependencies)

    def _get_line_number(self, content: str, position: int) -> int:
        """Get line number for a position in content"""
        return content[:position].count('\n') + 1

    def _extract_procedures_from_body(self, body_content: str, start_line: int, package_name: str) -> List[SQLChunk]:
        """Extract all procedures from package body"""
        procedures = []
        print(f"\n=== Extracting procedures from {package_name} ===")
        
        # Pattern to match complete procedure definitions including content
        proc_pattern = r'(?:CREATE\s+OR\s+REPLACE\s+)?PROCEDURE\s+(\w+)\s*\([^;]*?(?:\bAS\b|\bIS\b).*?(?=\s+(?:PROCEDURE|FUNCTION|END\s+' + re.escape(package_name) + r')\b|\Z)'
        
        for match in re.finditer(proc_pattern, body_content, re.DOTALL | re.IGNORECASE):
            proc_name = match.group(1)
            proc_content = match.group(0)
            
            print(f"Found procedure: {proc_name}")
            print(f"Content length: {len(proc_content)} characters")
            
            # Calculate exact line numbers
            start_pos = match.start()
            end_pos = match.end()
            proc_start_line = start_line + body_content[:start_pos].count('\n')
            proc_end_line = proc_start_line + proc_content.count('\n')
            
            # Extract dependencies specific to this procedure
            proc_dependencies = self._extract_dependencies_from_content(proc_content)
            
            procedures.append(SQLChunk(
                chunk_type='PROCEDURE',
                name=proc_name,
                content=proc_content,
                start_line=proc_start_line,
                end_line=proc_end_line,
                dependencies=proc_dependencies,
                parent_chunk=package_name
            ))
            print(f"Added procedure: {proc_name} (lines {proc_start_line}-{proc_end_line})")
        
        return procedures

    def parse_sql(self) -> List[SQLChunk]:
        """Parse SQL content into logical chunks"""
        print("\nStarting SQL parsing...")
        chunks = []
        packages = {}
        
        # First split by package boundaries
        package_pattern = r'CREATE\s+OR\s+REPLACE\s+PACKAGE\s+(?:BODY\s+)?(\w+)(?:\s+AS\s*|\s+IS\s*)?'
        package_matches = list(re.finditer(package_pattern, self.sql_content, re.IGNORECASE | re.MULTILINE))
        
        if not package_matches:
            print("No packages found!")
            return []
        
        # Process each package
        for i, match in enumerate(package_matches):
            package_name = match.group(1)
            start_pos = match.start()
            # End is either next package or end of content
            end_pos = package_matches[i+1].start() if i < len(package_matches)-1 else len(self.sql_content)
            package_content = self.sql_content[start_pos:end_pos].strip()
            
            print(f"\nProcessing package: {package_name}")
            print(f"Content length: {len(package_content)} characters")
            
            # Determine if spec or body
            is_body = bool(re.search(r'PACKAGE\s+BODY', package_content[:50], re.IGNORECASE))
            
            if package_name not in packages:
                packages[package_name] = {'spec': None, 'body': None, 'spec_lines': None, 'body_lines': None}
            
            start_line = self._get_line_number(self.sql_content, start_pos)
            end_line = self._get_line_number(self.sql_content, end_pos)
            
            if is_body:
                print(f"Processing body of {package_name}")
                packages[package_name]['body'] = package_content
                packages[package_name]['body_lines'] = (start_line, end_line)
                
                # Extract procedures
                procedures = self._extract_procedures_from_body(package_content, start_line, package_name)
                chunks.extend(procedures)
            else:
                print(f"Processing spec of {package_name}")
                packages[package_name]['spec'] = package_content
                packages[package_name]['spec_lines'] = (start_line, end_line)
        
        # Create package chunks
        for name, pkg in packages.items():
            spec = pkg['spec'] or ''
            body = pkg['body'] or ''
            if spec and body:
                content = f"{spec}\n{body}"
                start_line = pkg['spec_lines'][0]
                end_line = pkg['body_lines'][1]
            elif spec:
                content = spec
                start_line = pkg['spec_lines'][0]
                end_line = pkg['spec_lines'][1]
            else:
                content = body
                start_line = pkg['body_lines'][0]
                end_line = pkg['body_lines'][1]
            
            package_chunk = SQLChunk(
                chunk_type='PACKAGE',
                name=name,
                content=content,
                start_line=start_line,
                end_line=end_line,
                dependencies=self._extract_dependencies_from_content(content)
            )
            chunks.append(package_chunk)
            print(f"Added package chunk: {name}")
        
        print(f"\nTotal chunks created: {len(chunks)}")
        for chunk in chunks:
            print(f"- {chunk.chunk_type}: {chunk.name}")
        
        return chunks

    def get_chunk_content(self, start_line: int, end_line: int) -> str:
        """Get content between line numbers"""
        return '\n'.join(self.original_lines[start_line-1:end_line])