import ast
import os
from typing import Dict, Set, Any, Tuple, List

class AnalyzeError(Exception):
    pass

def analyze_file(file_path: str) -> Dict[str, Any]:
    """
    Analyze a Python file for imports, file I/O calls, and function/class usage from imported modules.

    Args:
        file_path: Path to the Python file to analyze

    Returns:
        Dict containing:
        - imports: dict mapping module -> set of import statements
        - io_call_count: total number of file I/O calls detected
        - function_usage: dict mapping module -> set of used functions/classes
        - io_operations: list of specific I/O operations found
        - file_info: basic file information
    """
    # Initialize data structures
    imports: Dict[str, Set[str]] = {}
    alias_map: Dict[str, str] = {}  # alias -> real module name
    io_call_count: int = 0
    function_usage: Dict[str, Set[str]] = {}  # module -> set of used functions/classes
    io_operations: List[str] = []  # List of specific I/O operations found

    def _record_import(module: str, stmt: str) -> None:
        """Record an import statement for a module."""
        imports.setdefault(module, set()).add(stmt)
        function_usage.setdefault(module, set())

    def _record_function_usage(module: str, function_name: str) -> None:
        """Record a function/class usage from a module."""
        if module in function_usage:
            function_usage[module].add(function_name)

    def _record_io_operation(operation: str) -> None:
        """Record a specific I/O operation."""
        io_operations.append(operation)

    def _handle_import(node: ast.Import) -> None:
        """Handle direct imports (import x)."""
        for alias in node.names:
            real_mod = alias.name
            asname = alias.asname or alias.name
            alias_map[asname] = real_mod
            stmt = f"import {real_mod}" if asname == real_mod else f"import {real_mod} as {asname}"
            _record_import(real_mod, stmt)

    def _handle_import_from(node: ast.ImportFrom) -> None:
        """Handle from imports (from x import y)."""
        module = node.module or ""
        
        # Handle future imports
        if module == "__future__":
            for alias in node.names:
                _record_import("__future__", f"from __future__ import {alias.name}")
                _record_function_usage("__future__", alias.name)
            return

        # Handle star imports
        if any(alias.name == "*" for alias in node.names):
            _record_import(module, f"from {module} import *")
            _record_function_usage(module, "ALL")
            return

        # Handle regular from imports
        for alias in node.names:
            real_name = alias.name
            asname = alias.asname or alias.name
            # Handle relative imports
            if module.startswith('.'):
                module = f"<relative>{module}"
            alias_map[asname] = f"{module}.{real_name}" if module else real_name
            stmt = f"from {module} import {real_name}"
            if alias.asname:
                stmt += f" as {alias.asname}"
            _record_import(module or "<local>", stmt)
            _record_function_usage(module or "<local>", real_name)

    def _is_io_operation(full_name: str) -> bool:
        """Check if a function call is an I/O operation."""
        io_patterns = {
            # Basic file operations
            "open", "gzip.open", "bz2.open", "lzma.open",
            # CSV operations
            "csv.reader", "csv.writer", "csv.DictReader", "csv.DictWriter",
            # JSON operations
            "json.load", "json.dump", "json.loads", "json.dumps",
            # Pickle operations
            "pickle.load", "pickle.dump", "pickle.loads", "pickle.dumps",
            # Pandas operations
            "pandas.read_csv", "pandas.read_json", "pandas.read_excel",
            "pandas.read_parquet", "pandas.read_feather", "pandas.read_hdf",
            "pandas.read_sql", "pandas.read_html", "pandas.read_xml",
            "pandas.to_csv", "pandas.to_json", "pandas.to_excel",
            "pandas.to_parquet", "pandas.to_feather", "pandas.to_hdf",
            "pandas.to_sql", "pandas.to_html", "pandas.to_xml",
            # PyTorch operations
            "torch.load", "torch.save", "torch.load_state_dict", "torch.save_state_dict",
            "torch.utils.data.DataLoader",
            # NumPy operations
            "numpy.load", "numpy.save", "numpy.loadtxt", "numpy.savetxt",
            "numpy.fromfile", "numpy.tofile", "numpy.genfromtxt",
            # Pathlib operations
            "Path.open", "Path.read_text", "Path.write_text",
            "Path.read_bytes", "Path.write_bytes", "Path.mkdir",
            "Path.rmdir", "Path.unlink", "Path.touch",
            # IO module operations
            "io.open", "io.StringIO", "io.BytesIO", "io.TextIOWrapper",
            # Shutil operations
            "shutil.copy", "shutil.copy2", "shutil.copyfile",
            "shutil.copytree", "shutil.move", "shutil.rmtree",
            # Zipfile operations
            "zipfile.ZipFile", "zipfile.PyZipFile", "zipfile.open",
            # Tarfile operations
            "tarfile.open", "tarfile.TarFile",
            # Database operations
            "sqlite3.connect", "sqlite3.connect", "sqlalchemy.create_engine",
            # Network operations
            "requests.get", "requests.post", "requests.put", "requests.delete",
            "urllib.request.urlopen", "urllib.request.urlretrieve",
            # Configuration operations
            "configparser.ConfigParser.read", "configparser.ConfigParser.write",
            "yaml.safe_load", "yaml.dump", "yaml.safe_dump",
            "toml.load", "toml.dump", "toml.loads", "toml.dumps",
            # Image operations
            "PIL.Image.open", "PIL.Image.save", "cv2.imread", "cv2.imwrite",
            # Audio operations
            "librosa.load", "librosa.output.write_wav",
            # Machine Learning operations
            "sklearn.model_selection.load_svmlight_file",
            "joblib.load", "joblib.dump",
            # HDF5 operations
            "h5py.File", "h5py.Group.create_dataset", "h5py.Dataset.read",
            # Excel operations
            "openpyxl.load_workbook", "openpyxl.Workbook.save",
            # XML operations
            "xml.etree.ElementTree.parse", "xml.etree.ElementTree.write",
            "lxml.etree.parse", "lxml.etree.write",
            # PDF operations
            "PyPDF2.PdfReader", "PyPDF2.PdfWriter.write",
            # Archive operations
            "rarfile.RarFile", "rarfile.RarFile.extract",
            # Cloud storage operations
            "boto3.client", "google.cloud.storage.Client",
            "azure.storage.blob.BlobServiceClient",
            # Streamlit operations
            "streamlit.file_uploader", "streamlit.download_button",
            # Matplotlib operations
            "matplotlib.pyplot.savefig", "matplotlib.pyplot.imsave",
            # Plotly operations
            "plotly.io.write_html", "plotly.io.write_image",
            # Seaborn operations
            "seaborn.savefig",
            # Altair operations
            "altair.save", "altair.renderer.save"
        }
        return full_name in io_patterns

    def _get_node_location(node: ast.AST) -> str:
        """Get the line number of an AST node."""
        return f"line {getattr(node, 'lineno', 'unknown')}"

    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise AnalyzeError(f"File not found: {file_path}")
        
        # Read and parse the file
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        if not source.strip():
            return {
                "imports": {},
                "io_call_count": 0,
                "function_usage": {},
                "io_operations": [],
                "file_info": {
                    "path": file_path,
                    "size": len(source),
                    "lines": len(source.splitlines()),
                    "empty": True
                }
            }
        
        tree = ast.parse(source, filename=file_path)
        
        # First pass: Process all imports
        for node in tree.body:
            if isinstance(node, ast.Import):
                _handle_import(node)
            elif isinstance(node, ast.ImportFrom):
                _handle_import_from(node)

        # Second pass: Process function calls and attribute access
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Handle basic open() call
                if isinstance(node.func, ast.Name) and node.func.id == "open":
                    io_call_count += 1
                    _record_io_operation(f"open() at {_get_node_location(node)}")
                
                # Handle pathlib.Path.open() and other pathlib operations
                elif isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Attribute):
                        if isinstance(node.func.value.value, ast.Name):
                            if node.func.value.value.id == "Path" and node.func.attr == "open":
                                io_call_count += 1
                                _record_io_operation(f"Path.open() at {_get_node_location(node)}")
                    
                    # Handle module.method() calls
                    base = node.func.value
                    if isinstance(base, ast.Name):
                        alias = base.id
                        real_mod = alias_map.get(alias, alias)
                        full = f"{real_mod}.{node.func.attr}"
                        _record_function_usage(real_mod, node.func.attr)
                        
                        # Check for I/O operations
                        if _is_io_operation(full):
                            io_call_count += 1
                            _record_io_operation(f"{full} at {_get_node_location(node)}")
                
                # Handle DataLoader instantiation and other ML operations
                elif isinstance(node.func, ast.Name):
                    if node.func.id in ["DataLoader", "load_model", "save_model"]:
                        io_call_count += 1
                        _record_io_operation(f"{node.func.id}() at {_get_node_location(node)}")

            # Track attribute access (e.g., pd.DataFrame, torch.tensor)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    alias = node.value.id
                    real_mod = alias_map.get(alias, alias)
                    _record_function_usage(real_mod, node.attr)

        # Get file information
        file_info = {
            "path": file_path,
            "size": len(source),
            "lines": len(source.splitlines()),
            "empty": False
        }

        return {
            "imports": imports,
            "io_call_count": io_call_count,
            "function_usage": function_usage,
            "io_operations": io_operations,
            "file_info": file_info
        }
    except SyntaxError as e:
        raise AnalyzeError(f"Syntax error in {file_path} at line {e.lineno}: {e.text}")
    except UnicodeDecodeError as e:
        raise AnalyzeError(f"Encoding error in {file_path}: {e}")
    except Exception as e:
        raise AnalyzeError(f"Error analyzing {file_path}: {e}")
