"""
Codebase Scanner - Context Gathering for AI Legend

Scans the project directory to gather relevant context for prompt optimization.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class CodebaseScanner:
    """Scans codebase to gather context for AI prompt optimization"""
    
    def __init__(self, project_root: str):
        """
        Initialize scanner
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root).resolve()
        self.max_depth = 3  # Limit directory traversal depth
        
    def scan_directory_structure(self, max_files: int = 50) -> Dict[str, List[str]]:
        """
        Scan directory structure and categorize files
        
        Args:
            max_files: Maximum files to include per category
            
        Returns:
            Dictionary with categorized file paths
        """
        structure = {
            "python_files": [],
            "config_files": [],
            "folders": [],
            "other_files": []
        }
        
        try:
            for root, dirs, files in os.walk(self.project_root):
                # Skip virtual environments and cache directories
                dirs[:] = [d for d in dirs if d not in ['.venv', '__pycache__', '.git', 'node_modules', 'chrome_data_video_0', 'chrome_data_video_1', 'chrome_data_video_2', 'chrome_data_video_3']]
                
                # Check depth
                depth = len(Path(root).relative_to(self.project_root).parts)
                if depth > self.max_depth:
                    continue
                
                # Collect folders
                rel_root = str(Path(root).relative_to(self.project_root))
                if rel_root != "." and len(structure["folders"]) < max_files:
                    structure["folders"].append(rel_root)
                
                # Categorize files
                for file in files:
                    file_path = str(Path(root, file).relative_to(self.project_root))
                    
                    if file.endswith('.py') and len(structure["python_files"]) < max_files:
                        structure["python_files"].append(file_path)
                    elif file in ['.env', 'requirements.txt', 'Dockerfile', 'docker-compose.yml', 'go.mod'] and len(structure["config_files"]) < max_files:
                        structure["config_files"].append(file_path)
                    elif len(structure["other_files"]) < max_files // 2:
                        structure["other_files"].append(file_path)
                        
        except Exception as e:
            logger.error(f"Error scanning directory: {e}")
            
        return structure
    
    def find_relevant_files(self, keywords: List[str]) -> List[str]:
        """
        Find files matching keywords
        
        Args:
            keywords: List of keywords to search for in filenames
            
        Returns:
            List of matching file paths
        """
        matching_files = []
        keywords_lower = [k.lower() for k in keywords]
        
        try:
            for root, dirs, files in os.walk(self.project_root):
                # Skip certain directories
                dirs[:] = [d for d in dirs if d not in ['.venv', '__pycache__', '.git', 'node_modules']]
                
                depth = len(Path(root).relative_to(self.project_root).parts)
                if depth > self.max_depth:
                    continue
                
                for file in files:
                    file_lower = file.lower()
                    if any(keyword in file_lower for keyword in keywords_lower):
                        file_path = str(Path(root, file).relative_to(self.project_root))
                        matching_files.append(file_path)
                        
        except Exception as e:
            logger.error(f"Error finding relevant files: {e}")
            
        return matching_files[:20]  # Limit results
    
    def read_error_logs(self, log_file: str = "error_log.txt") -> List[str]:
        """
        Read recent errors from log file
        
        Args:
            log_file: Name of the error log file
            
        Returns:
            List of recent error messages (last 5)
        """
        errors = []
        log_path = self.project_root / log_file
        
        try:
            if log_path.exists():
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    # Get last 5 error blocks (simplified parsing)
                    error_lines = [line.strip() for line in lines if 'error' in line.lower() or 'traceback' in line.lower()]
                    errors = error_lines[-5:]
        except Exception as e:
            logger.error(f"Error reading error log: {e}")
            
        return errors
    
    def get_project_metadata(self) -> Dict[str, str]:
        """
        Detect project type and metadata
        
        Returns:
            Dictionary with project information
        """
        metadata = {
            "project_type": "unknown",
            "framework": "none",
            "has_docker": False,
            "has_genkit": False
        }
        
        try:
            # Check for specific markers
            if (self.project_root / "genkit-service").exists():
                metadata["has_genkit"] = True
            
            if (self.project_root / "Dockerfile").exists():
                metadata["has_docker"] = True
            
            if (self.project_root / "flowchart").exists():
                metadata["project_type"] = "video_automation"
            elif (self.project_root / "app.py").exists() or (self.project_root / "main.py").exists():
                metadata["project_type"] = "web_application"
                
            # Check for requirements.txt to detect frameworks
            requirements_path = self.project_root / "requirements.txt"
            if requirements_path.exists():
                with open(requirements_path, 'r') as f:
                    content = f.read().lower()
                    if 'flask' in content:
                        metadata["framework"] = "Flask"
                    elif 'django' in content:
                        metadata["framework"] = "Django"
                    elif 'fastapi' in content:
                        metadata["framework"] = "FastAPI"
                        
        except Exception as e:
            logger.error(f"Error getting project metadata: {e}")
            
        return metadata
    
    def gather_context(self, goal: str) -> Dict:
        """
        Gather comprehensive context for a given goal
        
        Args:
            goal: User's high-level goal
            
        Returns:
            Dictionary with all gathered context
        """
        # Extract keywords from goal
        keywords = [word.lower() for word in goal.split() if len(word) > 3]
        
        context = {
            "files": self.find_relevant_files(keywords),
            "open_files": [],  # Will be populated by AI Legend main script
            "project_type": self.get_project_metadata()["project_type"],
            "recent_errors": self.read_error_logs(),
            "directory_tree": {}
        }
        
        # Add simplified directory tree
        structure = self.scan_directory_structure()
        context["directory_tree"] = {
            "key_folders": structure["folders"][:10],
            "python_files_count": len(structure["python_files"]),
            "config_files": structure["config_files"]
        }
        
        return context


if __name__ == "__main__":
    # Test the scanner
    logging.basicConfig(level=logging.INFO)
    
    scanner = CodebaseScanner(".")
    
    print("=== Project Structure ===")
    structure = scanner.scan_directory_structure()
    print(f"Python files: {len(structure['python_files'])}")
    print(f"Folders: {structure['folders'][:5]}")
    
    print("\n=== Project Metadata ===")
    metadata = scanner.get_project_metadata()
    print(json.dumps(metadata, indent=2))
    
    print("\n=== Relevant Files (keyword: 'parallel') ===")
    files = scanner.find_relevant_files(['parallel'])
    print(files)
