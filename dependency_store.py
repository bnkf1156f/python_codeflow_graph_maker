import json
from pathlib import Path
from typing import Dict, Set, List, Any
import os

class DependencyStore:
    def __init__(self, output_dir: str = "output_files"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.dependencies = {
            "files": {},  # file -> dependencies
            "modules": {},  # module -> files that import it
            "io_operations": {},  # file -> list of I/O operations
            "function_usage": {},  # file -> {module -> set of functions}
            "file_info": {},  # file -> basic file information
            "summary": {  # overall summary statistics
                "total_files": 0,
                "total_imports": 0,
                "total_io_operations": 0,
                "total_lines": 0,
                "empty_files": 0
            }
        }
    
    def add_file_dependencies(self, file_path: str, analysis_result: Dict[str, Any]):
        """Add dependencies for a single file to the store."""
        # file_path is already normalized and relative
        self.dependencies["files"][file_path] = {
            "imports": list(analysis_result["imports"].keys()),
            "io_count": analysis_result["io_call_count"],
            "function_usage": {
                module: list(functions) 
                for module, functions in analysis_result["function_usage"].items()
            }
        }
        
        # Store I/O operations
        if "io_operations" in analysis_result:
            self.dependencies["io_operations"][file_path] = analysis_result["io_operations"]
        
        # Store file information
        if "file_info" in analysis_result:
            self.dependencies["file_info"][file_path] = analysis_result["file_info"]
        
        # Update module dependencies
        for module in analysis_result["imports"]:
            if module not in self.dependencies["modules"]:
                self.dependencies["modules"][module] = []
            if file_path not in self.dependencies["modules"][module]:
                self.dependencies["modules"][module].append(file_path)
        
        # Update summary statistics
        self._update_summary(file_path, analysis_result)
    
    def _update_summary(self, file_path: str, analysis_result: Dict[str, Any]):
        """Update summary statistics."""
        summary = self.dependencies["summary"]
        summary["total_files"] += 1
        summary["total_imports"] += len(analysis_result["imports"])
        summary["total_io_operations"] += analysis_result["io_call_count"]
        
        if "file_info" in analysis_result:
            file_info = analysis_result["file_info"]
            summary["total_lines"] += file_info.get("lines", 0)
            if file_info.get("empty", False):
                summary["empty_files"] += 1
    
    def save(self, filename: str = "dependencies.json"):
        """Save dependencies to a JSON file."""
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.dependencies, f, indent=2)
        return output_path
    
    def load(self, filename: str = "dependencies.json"):
        """Load dependencies from a JSON file."""
        input_path = self.output_dir / filename
        if input_path.exists():
            with open(input_path, 'r', encoding='utf-8') as f:
                self.dependencies = json.load(f)
            return True
        return False
    
    def get_file_dependencies(self, file_path: str) -> Dict[str, Any]:
        """Get dependencies for a specific file."""
        # file_path is already normalized and relative
        return self.dependencies["files"].get(file_path, {})
    
    def get_file_io_operations(self, file_path: str) -> List[str]:
        """Get I/O operations for a specific file."""
        return self.dependencies["io_operations"].get(file_path, [])
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information for a specific file."""
        return self.dependencies["file_info"].get(file_path, {})
    
    def get_module_dependents(self, module: str) -> List[str]:
        """Get all files that depend on a specific module."""
        return self.dependencies["modules"].get(module, [])
    
    def get_all_dependencies(self) -> Dict[str, Any]:
        """Get all stored dependencies."""
        return self.dependencies
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        return self.dependencies["summary"]
    
    def get_all_files(self) -> List[str]:
        """Get all file paths that have been analyzed."""
        return list(self.dependencies["files"].keys())
    
    def get_files_with_io(self) -> List[str]:
        """Get all files that have I/O operations."""
        return [file_path for file_path, operations in self.dependencies["io_operations"].items() 
                if operations]
    
    def get_largest_files(self, limit: int = 10) -> List[tuple]:
        """Get the largest files by line count."""
        file_sizes = []
        for file_path, file_info in self.dependencies["file_info"].items():
            file_sizes.append((file_path, file_info.get("lines", 0)))
        return sorted(file_sizes, key=lambda x: x[1], reverse=True)[:limit]
    
    def get_most_imported_modules(self, limit: int = 10) -> List[tuple]:
        """Get the most imported modules."""
        module_counts = []
        for module, files in self.dependencies["modules"].items():
            module_counts.append((module, len(files)))
        return sorted(module_counts, key=lambda x: x[1], reverse=True)[:limit]
    
    def get_files_by_io_count(self, limit: int = 10) -> List[tuple]:
        """Get files with the most I/O operations."""
        io_counts = []
        for file_path, file_data in self.dependencies["files"].items():
            io_counts.append((file_path, file_data.get("io_count", 0)))
        return sorted(io_counts, key=lambda x: x[1], reverse=True)[:limit] 