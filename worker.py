import os
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import sys
from analyzer import analyze_file
from dependency_store import DependencyStore

def find_py_files(path, exclude_dirs=None, exclude_files=None):
    if exclude_dirs is None:
        exclude_dirs = ["venv", ".git", "__pycache__"]
    if exclude_files is None:
        exclude_files = []
    count = 0
    py_files = []
    for root, dirs, files in os.walk(path):
        # Exclude unwanted directories in-place
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file in exclude_files:
                continue
            if file.endswith((".py", ".pyw")):
                count += 1
                py_files.append(os.path.join(root, file))
    return py_files, count

def dependency_store_maker(folder_path, exclude_dirs=None, exclude_files=None):
    """
    Function from where works start
    here we call other funcs to analyze the whole codebase py/.pyw files
    where either pre-built or custom module are imported and save in DependencyStore() and return
    SO whole codebase dependencies are checked and can be further used
    for "downstream tasks like better prompting, troubleshoot, etc."

    Args:
        * folder_path (str): Path to repoistory/codebase/folder
        * exclude_dirs (list): List of directory names to exclude
        * exclude_files (list): List of file names to exclude
    """
    # Initialize dependency store
    store = DependencyStore()
    
    #find number of files in folder_path -- assumed that main is one of them
    py_files, num_py_files = find_py_files(folder_path, exclude_dirs=exclude_dirs, exclude_files=exclude_files)
    
    # Normalize all file paths to be relative to codebase root and use forward slashes
    codebase_root = os.path.abspath(folder_path)
    for file in py_files:
        rel_path = os.path.relpath(file, codebase_root).replace("\\", "/")
        print(f"\nAnalyzing file: {file}")
        try:
            dependencies = analyze_file(file)
            # Store dependencies with normalized relative path
            store.add_file_dependencies(rel_path, dependencies)
            
            # Print analysis results
            print("Dependencies found:")
            print(f"Imports: {dependencies['imports']}")
            print(f"I/O Operations: {dependencies['io_call_count']}")
            
            # Print file information if available
            if 'file_info' in dependencies:
                file_info = dependencies['file_info']
                print(f"File Info: {file_info.get('lines', 'unknown')} lines, {file_info.get('size', 'unknown')} bytes")
            
            # Print I/O operations if available
            if 'io_operations' in dependencies and dependencies['io_operations']:
                print("I/O Operations Details:")
                for op in dependencies['io_operations']:
                    print(f"  - {op}")
            
            print("\nFunction/Class Usage:")
            has_functions = False
            for module, functions in dependencies['function_usage'].items():
                if functions:  # If there are functions used
                    has_functions = True
                    print(f"  {module}:")
                    for func in sorted(functions):
                        print(f"    - {func}")
            if not has_functions:
                print("  NONE")
                
        except Exception as e:
            print(f"Error analyzing {file}: {e}")
            continue
    
    # Print summary statistics
    summary = store.get_summary()
    print(f"\n{'='*50}")
    print("ANALYSIS SUMMARY")
    print(f"{'='*50}")
    print(f"Total files analyzed: {summary['total_files']}")
    print(f"Total imports found: {summary['total_imports']}")
    print(f"Total I/O operations: {summary['total_io_operations']}")
    print(f"Total lines of code: {summary['total_lines']}")
    print(f"Empty files: {summary['empty_files']}")
    
    # Show top statistics
    print(f"\nTop 5 largest files:")
    for file_path, lines in store.get_largest_files(5):
        print(f"  {file_path}: {lines} lines")
    
    print(f"\nTop 5 most imported modules:")
    for module, count in store.get_most_imported_modules(5):
        print(f"  {module}: imported by {count} files")
    
    print(f"\nTop 5 files with most I/O operations:")
    for file_path, count in store.get_files_by_io_count(5):
        print(f"  {file_path}: {count} I/O operations")
    
    # Save dependencies to file
    codebase_name = os.path.basename(os.path.abspath(folder_path)).replace(' ', '_')
    output_filename = f"dependencies_{codebase_name}.json"
    output_path = store.save(filename=output_filename)
    print(f"\nDependencies saved to: {output_path}")
    
    return store, num_py_files

def load_prebuilt_libs(filepath="prebuilt_libs.txt"):
    if not os.path.exists(filepath):
        return set()
    with open(filepath, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def graph_maker(dependency_store, main_folder_path, main_file_path, prebuilt_libs_path="prebuilt_libs.txt"):
    """
    Shows main file's dependencies, recursively following custom modules, coloring unknowns purple. Edges and nodes for custom modules use the import string as in the source code.
    """
    G = nx.DiGraph()
    stdlib_modules = set(sys.stdlib_module_names)
    main_file_rel = main_file_path
    prebuilt_libs = load_prebuilt_libs(prebuilt_libs_path)
    all_deps = dependency_store.get_all_dependencies()["files"]

    def normalize_path(p):
        p = p.replace("\\", "/")
        while p.startswith("./") or p.startswith("../"):
            p = p[p.find("/")+1:]
        return p.lower()

    normalized_all_deps = {normalize_path(k): k for k in all_deps}

    def module_to_file_path(module_name, parent_file=None):
        # Try root-level first
        for ext in ('.py', '.pyw'):
            candidate = module_name.replace('.', '/') + ext
            norm_candidate = normalize_path(candidate)
            if norm_candidate in normalized_all_deps:
                return normalized_all_deps[norm_candidate]
            # Try relative to parent file's directory
            if parent_file:
                parent_dir = os.path.dirname(parent_file)
                candidate2 = os.path.join(parent_dir, candidate)
                norm_candidate2 = normalize_path(candidate2)
                if norm_candidate2 in normalized_all_deps:
                    return normalized_all_deps[norm_candidate2]
        return None

    visited = set()
    def add_dependencies(node, file_path_lookup=None):
        # node: the node label in the graph (import string or main file path)
        # file_path_lookup: the file path to look up dependencies (None for main file)
        if node in visited:
            return
        visited.add(node)
        file_path = file_path_lookup if file_path_lookup else node
        deps = all_deps.get(file_path, {})
        imports = deps.get("imports", [])
        for module in imports:
            target_file = module_to_file_path(module, file_path)
            if target_file:
                G.add_edge(node, module)
                G.nodes[module]['type'] = 'custom'
                add_dependencies(module, target_file)
            else:
                base_module = module.split('.')[0]
                is_prebuilt = base_module in stdlib_modules or base_module in prebuilt_libs
                if is_prebuilt:
                    G.add_edge(node, module)
                    G.nodes[module]['type'] = 'prebuilt'
                else:
                    G.add_edge(node, module)
                    G.nodes[module]['type'] = 'unknown'

    # Start from main file
    add_dependencies(main_file_rel)

    # --- Add node attributes ---
    all_imports = set(imp for deps in all_deps.values() for imp in deps.get("imports", []))
    for node in G.nodes():
        if node == main_file_rel:
            G.nodes[node]['name'] = os.path.basename(node)
            G.nodes[node]['color'] = 'yellow'
        elif G.nodes[node].get('type') == 'custom':
            G.nodes[node]['name'] = node  # import string
            G.nodes[node]['color'] = 'red'
        elif G.nodes[node].get('type') == 'prebuilt':
            G.nodes[node]['name'] = node
            G.nodes[node]['color'] = 'green'
        elif G.nodes[node].get('type') == 'unknown':
            G.nodes[node]['name'] = node
            G.nodes[node]['color'] = 'purple'
        else:
            G.nodes[node]['name'] = node
            G.nodes[node]['color'] = 'lightblue'

    # --- Visualization ---
    plt.figure(figsize=(32, 20))
    # Use shell_layout to put main file in center, others in shells
    shells = [[main_file_rel], [n for n in G.nodes() if n != main_file_rel]]
    pos = nx.shell_layout(G, shells)

    # Draw nodes individually to control shape
    for node in G.nodes():
        marker_shape = 's' if node == main_file_rel else 'o' # 's' for square, 'o' for circle
        node_size = 3500 if node == main_file_rel else 3000
        node_color = G.nodes[node]['color']
        nx.draw_networkx_nodes(G, pos, nodelist=[node], node_color=node_color, node_size=node_size, 
                              edgecolors='black', linewidths=1, node_shape=marker_shape)

    nx.draw_networkx_edges(G, pos, arrows=False, width=1.5, 
                          connectionstyle='arc3,rad=0.2', edge_color='black', alpha=0.9)
    
    # Add edge labels
    edge_labels = {(u, v): f"{G.nodes[u]['name'][:4]} --> {G.nodes[v]['name'][:4]}" for u, v in G.edges()}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='blue', font_size=8)

    nx.draw_networkx_labels(G, pos, labels={node: G.nodes[node]['name'] for node in G.nodes()}, font_size=12, font_weight='bold')

    import matplotlib.patches as mpatches
    legend_handles = [
        mpatches.Patch(color='yellow', label='Main File'),
        mpatches.Patch(color='red', label='Custom Module'),
        mpatches.Patch(color='green', label='Pre-built Module'),
        mpatches.Patch(color='purple', label='Unknown Module'),
        mpatches.Patch(color='blue', label='Edge Label: DEP-->MOD/LIB \n(Dependent --> On which it depends)')
    ]
    plt.legend(handles=legend_handles, loc='upper left', fontsize=10)  # Smaller font, top left

    try:
        plt.gcf().canvas.manager.set_window_title('Main File Dependency Path')
    except Exception:
        pass

    plt.axis('off')
    plt.tight_layout()
    # plt.show() # This is non-interactive and will be removed.

    print("Graph nodes:", G.nodes())
    print("Graph edges:", G.edges())

    # Output detailed dependencies to a text file
    main_file_basename = os.path.basename(main_folder_path).replace(".py", "").replace(".pyw", "")
    output_filename = f"detailed_deps_{main_file_basename}.txt"
    output_filepath = os.path.join("output_files", output_filename)

    with open(output_filepath, 'w') as f:
        f.write("--- Detailed Dependencies ---\n")
        f.write(f"Main File: {main_file_rel}\n")
        f.write(f"Total Dependencies: {len(G.nodes()) - 1}\n\n")
        
        # Add summary statistics
        summary = dependency_store.get_summary()
        f.write("--- Analysis Summary ---\n")
        f.write(f"Total files analyzed: {summary['total_files']}\n")
        f.write(f"Total imports found: {summary['total_imports']}\n")
        f.write(f"Total I/O operations: {summary['total_io_operations']}\n")
        f.write(f"Total lines of code: {summary['total_lines']}\n\n")
        
        f.write("--- Dependency Relationships ---\n")
        for u, v in G.edges():
            u_name = G.nodes[u].get('name', u)
            v_name = G.nodes[v].get('name', v)
            v_type = G.nodes[v].get('type', 'unknown')
            f.write(f"{u_name} depends on {v_name} ({v_type})\n")
        
        # Add I/O operations for main file
        main_file_io = dependency_store.get_file_io_operations(main_file_rel)
        if main_file_io:
            f.write(f"\n--- I/O Operations in {main_file_rel} ---\n")
            for op in main_file_io:
                f.write(f"{op}\n")
        
        f.write("---------------------------\n")
    print(f"Detailed dependencies saved to: {output_filepath}")

    return output_filepath, plt.gcf()