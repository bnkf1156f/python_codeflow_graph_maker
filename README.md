# 🔄 Python Code Flow Graph Maker

A comprehensive Python code analysis and visualization tool that automatically generates dependency graphs for Python codebases. This tool analyzes import dependencies, tracks I/O operations, and creates interactive visualizations to help developers understand code structure and dependencies across pre-built libraries and custom modules.

## 🎯 Features

- **Static Code Analysis**: Analyzes Python files using AST (Abstract Syntax Tree) parsing
- **Dependency Tracking**: Maps import relationships between custom modules and external libraries
- **Advanced I/O Operation Detection**: Identifies 100+ file operations, data loading/saving, and I/O patterns across 50+ libraries
- **Interactive Visualization**: Generates dependency graphs with color-coded nodes and edges
- **Web-based GUI**: Streamlit-powered interface with step-by-step workflow
- **Export Capabilities**: Save analysis results as JSON and generate detailed dependencies report for *main_file* only
- **Flexible Configuration**: Customizable exclusions for directories and files
- **Comprehensive Reporting**: Detailed statistics, file information, and I/O operation tracking
- **Error Handling**: Robust error handling for malformed files and encoding issues

## 🏗️ Architecture & Algorithms

### Core Analysis Algorithm

The tool uses a **two-pass AST parsing approach**:

1. **First Pass - Import Analysis**:
   - Parses all import statements using Python's `ast` module
   - Handles multiple import types:
     - Direct imports: `import module`
     - Aliased imports: `import module as alias`
     - From imports: `from module import item`
     - Relative imports: `from . import item`
     - Star imports: `from module import *`
     - Future imports: `from __future__ import feature`
   - Builds alias mapping for function/class usage tracking

2. **Second Pass - Function & I/O Analysis**:
   - Traverses AST to find function calls and attribute access
   - Maps function calls to their source modules using alias mapping
   - Detects I/O operations through comprehensive pattern matching
   - Records specific I/O operations with line numbers for debugging

### Dependency Graph Generation Algorithm

The graph generation follows a **recursive dependency resolution** approach for *main_file* dependencies' visualization:

```python
Algorithm: RecursiveDependencyGraph
Input: main_file, dependency_store, prebuilt_libs
Output: Directed graph G

1. Initialize empty directed graph G
2. Add main_file as root node (yellow, square shape)
3. For each import in main_file:
   a. Try to map module to local file path
   b. If found (custom module):
      - Add as red node (circle shape)
      - Recursively process its dependencies
   c. If in prebuilt_libs or stdlib:
      - Add as green node (circle shape)
   d. If unknown:
      - Add as purple node (circle shape)
4. Add edges from dependent to dependency
5. Apply shell layout with main file at center
```

### Advanced I/O Operation Detection

The system maintains a comprehensive database of **100+ I/O operations** across **50+ libraries**:

#### **Basic File Operations**
- `open()`, `gzip.open()`, `bz2.open()`, `lzma.open()`

#### **Data Science Libraries**
- **Pandas**: `read_csv`, `read_json`, `read_excel`, `read_parquet`, `read_sql`, `read_html`, `read_xml`
- **NumPy**: `load`, `save`, `loadtxt`, `savetxt`, `fromfile`, `tofile`, `genfromtxt`
- **PyTorch**: `load`, `save`, `load_state_dict`, `save_state_dict`, `DataLoader`
- **Scikit-learn**: `load_svmlight_file`, `joblib.load`, `joblib.dump`

#### **Serialization & Configuration**
- **JSON**: `json.load`, `json.dump`, `json.loads`, `json.dumps`
- **Pickle**: `pickle.load`, `pickle.dump`, `pickle.loads`, `pickle.dumps`
- **CSV**: `csv.reader`, `csv.writer`, `csv.DictReader`, `csv.DictWriter`
- **YAML**: `yaml.safe_load`, `yaml.dump`, `yaml.safe_dump`
- **TOML**: `toml.load`, `toml.dump`, `toml.loads`, `toml.dumps`
- **ConfigParser**: `ConfigParser.read`, `ConfigParser.write`

#### **Database & Network Operations**
- **SQLite**: `sqlite3.connect`
- **SQLAlchemy**: `create_engine`
- **Requests**: `requests.get`, `requests.post`, `requests.put`, `requests.delete`
- **urllib**: `urllib.request.urlopen`, `urllib.request.urlretrieve`

#### **File System & Archives**
- **Pathlib**: `Path.open`, `Path.read_text`, `Path.write_text`, `Path.mkdir`, `Path.rmdir`
- **Shutil**: `shutil.copy`, `shutil.copy2`, `shutil.copyfile`, `shutil.copytree`, `shutil.move`, `shutil.rmtree`
- **Zipfile**: `zipfile.ZipFile`, `zipfile.PyZipFile`, `zipfile.open`
- **Tarfile**: `tarfile.open`, `tarfile.TarFile`
- **Rarfile**: `rarfile.RarFile`, `rarfile.RarFile.extract`

#### **Specialized Libraries**
- **Image Processing**: `PIL.Image.open`, `PIL.Image.save`, `cv2.imread`, `cv2.imwrite`
- **Audio Processing**: `librosa.load`, `librosa.output.write_wav`
- **HDF5**: `h5py.File`, `h5py.Group.create_dataset`, `h5py.Dataset.read`
- **Excel**: `openpyxl.load_workbook`, `openpyxl.Workbook.save`
- **XML**: `xml.etree.ElementTree.parse`, `lxml.etree.parse`
- **PDF**: `PyPDF2.PdfReader`, `PyPDF2.PdfWriter.write`

#### **Cloud Storage**
- **AWS**: `boto3.client`
- **Google Cloud**: `google.cloud.storage.Client`
- **Azure**: `azure.storage.blob.BlobServiceClient`

#### **Visualization Libraries**
- **Matplotlib**: `matplotlib.pyplot.savefig`, `matplotlib.pyplot.imsave`
- **Plotly**: `plotly.io.write_html`, `plotly.io.write_image`
- **Seaborn**: `seaborn.savefig`
- **Altair**: `altair.save`, `altair.renderer.save`

#### **Web Frameworks**
- **Streamlit**: `streamlit.file_uploader`, `streamlit.download_button`

## 🛠️ Technical Implementation

### Key Components

1. **`analyzer.py`**: Enhanced AST parsing and analysis engine with comprehensive I/O detection
2. **`dependency_store.py`**: Advanced data persistence with summary statistics and analytics
3. **`worker.py`**: Orchestration and graph generation logic with detailed reporting
4. **`gui.py`**: Streamlit-based web interface with step-by-step workflow
5. **`non_interactive_main.py`**: Command-line interface for automation

### Enhanced Data Structures

```python
DependencyStore = {
    "files": {file_path: {
        "imports": [module_names],
        "io_count": int,
        "function_usage": {module: [functions]}
    }},
    "modules": {module_name: [dependent_files]},
    "io_operations": {file_path: [detailed_operations_with_line_numbers]},
    "function_usage": {file_path: {module: [functions]}},
    "file_info": {file_path: {
        "path": str,
        "size": int,
        "lines": int,
        "empty": bool
    }},
    "summary": {
        "total_files": int,
        "total_imports": int,
        "total_io_operations": int,
        "total_lines": int,
        "empty_files": int
    }
}
```

### Advanced Analytics Methods

The dependency store provides comprehensive analytics:

- **`get_summary()`**: Overall statistics for the codebase
- **`get_files_with_io()`**: Files containing I/O operations
- **`get_largest_files(limit)`**: Largest files by line count
- **`get_most_imported_modules(limit)`**: Most frequently imported modules
- **`get_files_by_io_count(limit)`**: Files with most I/O operations
- **`get_file_io_operations(file_path)`**: Detailed I/O operations for specific files
- **`get_file_info(file_path)`**: File metadata and statistics

### Visualization Features

- **Node Types**:
  - 🟡 Yellow Square: Main entry file
  - 🔴 Red Circle: Custom/local modules
  - 🟢 Green Circle: Pre-built/external libraries
  - 🟣 Purple Circle: Unknown/unresolved modules

- **Layout**: Shell layout with main file at center
- **Edge Labels**: Show dependency relationships
- **Interactive**: Zoom, pan, and export capabilities
- **High Resolution**: 300 DPI PNG export support

## 📋 Requirements

### System Requirements
- Python 3.8+
- 4GB+ RAM (for large codebases)
- 100MB+ disk space

### Dependencies
See `requirements.txt` for complete dependency list.

## 🚀 Installation & Usage

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/python_codeflow_graphmaker.git
   cd python_codeflow_graphmaker
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the GUI**:
   ```bash
   streamlit run gui.py
   ```

4. **Or use command line**:
   ```bash
   python non_interactive_main.py
   ```

### Configuration

#### Excluding Directories/Files
```python
exclude_dirs = ["venv", ".git", "__pycache__", "node_modules"]
exclude_files = ["test_file.py", "temp.py"]
```

#### Custom Pre-built Libraries
Edit `prebuilt_libs.txt` to add your commonly used libraries.

## 📊 Output Formats

### JSON Analysis Results
```json
{
  "files": {
    "main.py": {
      "imports": ["pandas", "numpy", "custom_module"],
      "io_count": 5,
      "function_usage": {
        "pandas": ["read_csv", "DataFrame"],
        "numpy": ["array", "mean"]
      }
    }
  },
  "modules": {
    "pandas": ["main.py", "utils.py"],
    "custom_module": ["main.py"]
  },
  "io_operations": {
    "main.py": [
      "pandas.read_csv() at line 15",
      "numpy.save() at line 23"
    ]
  },
  "file_info": {
    "main.py": {
      "path": "main.py",
      "size": 2048,
      "lines": 50,
      "empty": false
    }
  },
  "summary": {
    "total_files": 10,
    "total_imports": 25,
    "total_io_operations": 15,
    "total_lines": 500,
    "empty_files": 0
  }
}
```

### Detailed Text Reports
- **Dependency relationships** with module types
- **I/O operation counts** with line numbers
- **Function usage statistics** by module
- **Module dependency chains** with categorization
- **Analysis summary** with comprehensive statistics
- **Top 5 lists** for largest files, most imported modules, and I/O-heavy files

### Visual Graphs
- **High-resolution PNG exports** (300 DPI)
- **Interactive matplotlib figures** with zoom/pan
- **Color-coded dependency visualization** with legend
- **Edge labels** showing dependency relationships

## ⚠️ Assumptions & Limitations

### Assumptions
1. **File Structure**: Assumes script runs from the codebase root directory
2. **Python Files**: Only analyzes `.py` and `.pyw` files
3. **Import Resolution**: Relies on file naming conventions for module mapping
4. **AST Parsing**: Assumes syntactically correct Python code
5. **Encoding**: Assumes UTF-8 encoding for all source files

### Limitations
1. **Dynamic Imports**: Cannot detect `importlib.import_module()` or `__import__()` calls
2. **String-based Imports**: Misses imports constructed from strings
3. **Runtime Dependencies**: Only analyzes static dependencies, not runtime behavior
4. **Circular Dependencies**: May not handle complex circular import scenarios gracefully
5. **Large Codebases**: Performance may degrade with very large repositories (>1000 files)
6. **External Dependencies**: Cannot resolve dependencies of external packages
7. **Conditional Imports**: May miss imports within conditional blocks if not executed

### Known Issues
- Relative imports with complex parent directory structures
- Module aliasing in complex scenarios
- Some edge cases in star import analysis
- Limited support for namespace packages

## 🔧 Customization

### Adding New I/O Patterns
Edit the `_is_io_operation()` function in `analyzer.py`:

```python
def _is_io_operation(full_name: str) -> bool:
    io_patterns = {
        # Add your custom patterns here
        "your_library.read_data",
        "your_library.save_data",
        # ... existing patterns
    }
    return full_name in io_patterns
```

### Custom Node Colors
Modify the color mapping in `worker.py`:

```python
node_colors = {
    'main': 'yellow',
    'custom': 'red', 
    'prebuilt': 'green',
    'unknown': 'purple'
}
```

### Extending Analysis
Add new analysis functions to `analyzer.py` and integrate them into the main analysis pipeline.

## 🧑‍💻 Concepts/DS/Libraries Used

- **Python AST Module**: For static code analysis capabilities
- **NetworkX**: For graph generation and layout algorithms
- **Matplotlib**: For visualization and plotting
- **Streamlit**: For the web-based user interface
- **Pandas & NumPy**: For data manipulation and analysis

---

**Made with ❤️ for the Python community. If there is a problem in any part, please don't hesitate to open issue!** 
