import streamlit as st
import os
import json
from pathlib import Path
from worker import dependency_store_maker, graph_maker
import matplotlib.pyplot as plt
import io
import base64
import tkinter as tk
from tkinter import filedialog

def get_file_icon(file_path):
    """Return appropriate icon for file type"""
    if file_path.endswith('.py'):
        return "🐍"
    elif file_path.endswith('.pyw'):
        return "🐍"
    else:
        return "📄"

def get_directory_structure(path, exclude_dirs=None, exclude_files=None):
    """Get directory structure for display"""
    if exclude_dirs is None:
        exclude_dirs = ["venv", ".git", "__pycache__"]
    if exclude_files is None:
        exclude_files = []
    
    structure = []
    try:
        for root, dirs, files in os.walk(path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            # Get relative path from the base path
            rel_path = os.path.relpath(root, path)
            if rel_path == '.':
                rel_path = ''
            
            # Add directories
            for dir_name in sorted(dirs):
                dir_path = os.path.join(rel_path, dir_name) if rel_path else dir_name
                structure.append({
                    'type': 'directory',
                    'name': dir_name,
                    'path': dir_path,
                    'icon': '📁'
                })
            
            # Add files
            for file_name in sorted(files):
                if file_name not in exclude_files and file_name.endswith(('.py', '.pyw')):
                    file_path = os.path.join(rel_path, file_name) if rel_path else file_name
                    structure.append({
                        'type': 'file',
                        'name': file_name,
                        'path': file_path,
                        'icon': get_file_icon(file_name)
                    })
    except Exception as e:
        st.error(f"Error reading directory structure: {e}")
    
    return structure

def save_graph_as_image(fig):
    """Save the provided matplotlib figure as an image"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    return buf

def main():
    st.set_page_config(
        page_title="Code Flow Graph Maker",
        page_icon="🔄",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .info-box {
        background-color: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.25rem;
        color: black;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.25rem;
        color: black;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.25rem;
        color: black;
    }
    .step-indicator {
        display: flex;
        justify-content: space-between;
        margin-bottom: 2rem;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 0.5rem;
    }
    .step {
        text-align: center;
        flex: 1;
        padding: 0.5rem;
        margin: 0 0.25rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .step.active {
        background-color: #007bff;
        color: white;
    }
    .step.completed {
        background-color: #28a745;
        color: white;
    }
    .step.pending {
        background-color: #6c757d;
        color: white;
        opacity: 0.6;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
    st.markdown('<h1 class="main-header">🔄 Code Flow Graph Maker</h1>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    if 'codebase_path' not in st.session_state:
        st.session_state.codebase_path = ""
    if 'main_file' not in st.session_state:
        st.session_state.main_file = ""
    if 'exclude_as_per_rqst_dirs' not in st.session_state:
        st.session_state.exclude_as_per_rqst_dirs = []
    if 'exclude_as_per_rqst_files' not in st.session_state:
        st.session_state.exclude_as_per_rqst_files = []
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'dependency_store' not in st.session_state:
        st.session_state.dependency_store = None
    if 'num_py_files' not in st.session_state:
        st.session_state.num_py_files = 0
    if 'dependency_graph_fig' not in st.session_state:
        st.session_state.dependency_graph_fig = None
    
    # Step indicator
    steps = ["1. Select Codebase", "2. Choose Main File", "3. Configure Exclusions", "4. Analysis & Results", "5. Save & Export"]
    
    st.markdown('<div class="step-indicator">', unsafe_allow_html=True)
    for i, step_name in enumerate(steps, 1):
        if i == st.session_state.current_step:
            st.markdown(f'<div class="step active">{step_name}</div>', unsafe_allow_html=True)
        elif i < st.session_state.current_step:
            st.markdown(f'<div class="step completed">{step_name}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="step pending">{step_name}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.session_state.current_step > 1:
            if st.button("⬅️ Previous", use_container_width=True):
                st.session_state.current_step -= 1
                st.rerun()
    
    with col3:
        if st.session_state.current_step < 5 and st.session_state.analysis_complete:
            if st.button("Next ➡️", use_container_width=True):
                st.session_state.current_step += 1
                st.rerun()
    
    # Step 1: Select Codebase
    if st.session_state.current_step == 1:
        st.markdown('<h2 class="section-header">📁 Step 1: Select Your Codebase</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("Enter the full path to your Python codebase folder or use the browse button.")
            
            # Path input
            codebase_path = st.text_input(
                "📂 Codebase Path:",
                value=st.session_state.codebase_path,
                placeholder="e.g., C:/Users/YourName/Projects/my_python_project"
            )
            st.session_state.codebase_path = codebase_path

            if st.button("Browse..."):
                root = tk.Tk()
                root.withdraw() # Hide the main tkinter window
                folder_path = filedialog.askdirectory()
                root.destroy()
                if folder_path:
                    st.session_state.codebase_path = folder_path
                    st.rerun()
        
        with col2:
            st.markdown("### 📊 What will be analyzed?")
            st.markdown("""
            ✅ Python files (.py, .pyw)<br>
            ✅ Import statements<br>
            ✅ Function/class usage<br>
            ✅ File I/O operations<br>
            ✅ Dependency relationships
            """, unsafe_allow_html=True)
            
            st.markdown("### 🚫 What will be excluded?")
            st.markdown("""
            ❌ venv folders<br>
            ❌ .git folders<br>
            ❌ __pycache__ folders<br>
            ❌ Non-Python files
            """, unsafe_allow_html=True)
        
        # Validate and proceed
        if codebase_path:
            if os.path.exists(codebase_path) and os.path.isdir(codebase_path):
                st.session_state.codebase_path = codebase_path
                
                # Show directory structure preview
                st.markdown("### 📂 Codebase Structure Preview")
                structure = get_directory_structure(codebase_path)
                
                if structure:
                    # Group by type for better display
                    dirs = [item for item in structure if item['type'] == 'directory']
                    files = [item for item in structure if item['type'] == 'file']
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**📁 Directories:**")
                        for item in dirs[:10]:  # Show first 10
                            st.markdown(f"{item['icon']} {item['name']}")
                        if len(dirs) > 10:
                            st.markdown(f"... and {len(dirs) - 10} more")
                    
                    with col2:
                        st.markdown("**🐍 Python Files:**")
                        for item in files[:10]:  # Show first 10
                            st.markdown(f"{item['icon']} {item['name']}")
                        if len(files) > 10:
                            st.markdown(f"... and {len(files) - 10} more")
                    
                    st.success(f"✅ Found {len(files)} Python files in {len(dirs)} directories")
                    
                    if st.button("➡️ Continue to Step 2", type="primary", use_container_width=True):
                        st.session_state.current_step = 2
                        st.rerun()
                else:
                    st.warning("⚠️ No Python files found in the selected directory")
            else:
                st.error("❌ Invalid path. Please enter a valid directory path.")
    
    # Step 2: Select Main File
    elif st.session_state.current_step == 2:
        st.markdown('<h2 class="section-header">🎯 Step 2: Select Main File</h2>', unsafe_allow_html=True)
        
        if not st.session_state.codebase_path:
            st.error("❌ No codebase path selected. Please go back to Step 1.")
            return
        
        st.markdown("""
        <div class="info-box">
        <strong>Instructions:</strong><br>
        • Select the main entry point file for your application<br>
        • This file will be the starting point for dependency analysis<br>
        • Only Python files from your codebase are shown
        </div>
        """, unsafe_allow_html=True)
        
        # Get Python files from codebase
        structure = get_directory_structure(st.session_state.codebase_path)
        python_files = [item for item in structure if item['type'] == 'file']
        
        if python_files:
            # Create a list of file options for selectbox
            file_options = [f"{item['icon']} {item['path']}" for item in python_files]
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                selected_file_display = st.selectbox(
                    "🐍 Select Main File:",
                    options=file_options,
                    index=0 if not st.session_state.main_file else 
                          next((i for i, f in enumerate(file_options) 
                                if f.endswith(st.session_state.main_file)), 0)
                )
                
                # Extract the actual file path
                selected_file = selected_file_display.split(" ", 1)[1] if " " in selected_file_display else selected_file_display
                st.session_state.main_file = selected_file
                
                # Show file info
                full_path = os.path.join(st.session_state.codebase_path, selected_file)
                if os.path.exists(full_path):
                    file_size = os.path.getsize(full_path)
                    st.info(f"📄 File: {selected_file}\n📏 Size: {file_size:,} bytes")
            
            with col2:
                st.markdown("### 📋 Selected Files")
                st.markdown(f"**Codebase:** {os.path.basename(st.session_state.codebase_path)}")
                st.markdown(f"**Main File:** {selected_file}")
                st.markdown(f"**Total Python Files:** {len(python_files)}")
            
            if st.button("➡️ Continue to Step 3", type="primary", use_container_width=True):
                st.session_state.current_step = 3
                st.rerun()
        else:
            st.error("❌ No Python files found in the codebase. Please check your codebase path.")
    
    # Step 3: Configure Exclusions
    elif st.session_state.current_step == 3:
        st.markdown('<h2 class="section-header">🚫 Step 3: Configure Exclusions</h2>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="info-box">
        <strong>Instructions:</strong><br>
        • Select directories and files you want to exclude from analysis<br>
        • This helps focus the analysis on relevant code<br>
        • You can always go back and modify these later
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📁 Exclude Directories")
            
            # Get directories from codebase
            structure = get_directory_structure(st.session_state.codebase_path)
            directories = [item for item in structure if item['type'] == 'directory']
            
            if directories:
                dir_options = [f"{item['icon']} {item['path']}" for item in directories]
                
                # Format the default values to match the options format
                default_dirs = [f"📁 {d}" for d in st.session_state.exclude_as_per_rqst_dirs]

                selected_dirs = st.multiselect(
                    "Select directories to exclude:",
                    options=dir_options,
                    default=default_dirs
                )
                
                # Extract actual directory names
                st.session_state.exclude_as_per_rqst_dirs = [d.split(" ", 1)[1] for d in selected_dirs if " " in d]
                
                if st.session_state.exclude_as_per_rqst_dirs:
                    st.markdown("**Selected for exclusion:**")
                    for dir_name in st.session_state.exclude_as_per_rqst_dirs:
                        st.markdown(f"❌ {dir_name}")
            else:
                st.info("No additional directories found to exclude")
        
        with col2:
            st.markdown("### 📄 Exclude Files")
            
            # Get Python files from codebase
            python_files = [item for item in structure if item['type'] == 'file']
            
            if python_files:
                file_options = [f"{item['icon']} {item['path']}" for item in python_files]
                
                # Format the default values to match the options format
                default_files = [f"🐍 {f}" for f in st.session_state.exclude_as_per_rqst_files]

                selected_files = st.multiselect(
                    "Select files to exclude:",
                    options=file_options,
                    default=default_files
                )
                
                # Extract actual file names
                st.session_state.exclude_as_per_rqst_files = [f.split(" ", 1)[1] for f in selected_files if " " in f]
                
                if st.session_state.exclude_as_per_rqst_files:
                    st.markdown("**Selected for exclusion:**")
                    for file_name in st.session_state.exclude_as_per_rqst_files:
                        st.markdown(f"❌ {file_name}")
            else:
                st.info("No Python files found")
        
        # Summary
        st.markdown("### 📊 Exclusion Summary")
        exclude_always_dirs = ["venv", ".git", "__pycache__"]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🚫 Always Excluded:**")
            st.markdown("• venv")
            st.markdown("• .git") 
            st.markdown("• __pycache__")
        
        with col2:
            st.markdown("**📁 Custom Excluded Dirs:**")
            if st.session_state.exclude_as_per_rqst_dirs:
                for dir_name in st.session_state.exclude_as_per_rqst_dirs:
                    st.markdown(f"• {dir_name}")
            else:
                st.markdown("• None")
        
        with col3:
            st.markdown("**📄 Custom Excluded Files:**")
            if st.session_state.exclude_as_per_rqst_files:
                for file_name in st.session_state.exclude_as_per_rqst_files:
                    st.markdown(f"• {file_name}")
            else:
                st.markdown("• None")
        
        if st.button("➡️ Continue to Step 4", type="primary", use_container_width=True):
            st.session_state.current_step = 4
            st.rerun()
    
    # Step 4: Analysis & Results
    elif st.session_state.current_step == 4:
        st.markdown('<h2 class="section-header">⚙️ Step 4: Analysis & Results</h2>', unsafe_allow_html=True)
        
        if not st.session_state.analysis_complete:
            st.markdown("""
            <div class="info-box">
            <strong>What will happen:</strong><br>
            • Analyze all Python files in your codebase<br>
            • Extract import statements and dependencies<br>
            • Generate dependency graph visualization<br>
            • Create detailed dependency reports
            </div>
            """, unsafe_allow_html=True)
            
            # Show configuration summary
            st.markdown("### 📋 Configuration Summary")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**📁 Codebase:** {st.session_state.codebase_path}")
                st.markdown(f"**🎯 Main File:** {st.session_state.main_file}")
                structure = get_directory_structure(st.session_state.codebase_path)
                python_files = [item for item in structure if item['type'] == 'file']
                st.markdown(f"**📊 Python Files:** {len(python_files)}")
            
            with col2:
                st.markdown(f"**🚫 Excluded Dirs:** {len(st.session_state.exclude_as_per_rqst_dirs)}")
                st.markdown(f"**🚫 Excluded Files:** {len(st.session_state.exclude_as_per_rqst_files)}")
            
            # Generate button
            if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
                with st.spinner("🔄 Analyzing codebase..."):
                    try:
                        # Prepare exclusion lists
                        exclude_always_dirs = ["venv", ".git", "__pycache__"]
                        exclude_always_files = []
                        
                        exclude_dirs = exclude_always_dirs + st.session_state.exclude_as_per_rqst_dirs
                        exclude_files = exclude_always_files + st.session_state.exclude_as_per_rqst_files
                        
                        # Generate dependency store
                        st.info("📊 Creating dependency store...")
                        dependency_store, num_py_files = dependency_store_maker(
                            folder_path=st.session_state.codebase_path,
                            exclude_dirs=exclude_dirs,
                            exclude_files=exclude_files
                        )
                        
                        st.session_state.dependency_store = dependency_store
                        st.session_state.num_py_files = num_py_files
                        
                        st.success(f"✅ Dependency store created! Analyzed {num_py_files} Python files.")
                        
                        # Generate graph
                        st.info("📈 Generating dependency graph...")
                        codebase_root = os.path.abspath(st.session_state.codebase_path)
                        main_file_rel = os.path.relpath(
                            os.path.join(st.session_state.codebase_path, st.session_state.main_file), 
                            codebase_root
                        ).replace("\\", "/")
                        
                        det_deps_path, fig = graph_maker(
                            dependency_store=dependency_store,
                            main_folder_path=st.session_state.codebase_path,
                            main_file_path=main_file_rel
                        )
                        
                        st.session_state.analysis_complete = True
                        st.session_state.det_deps_path = det_deps_path
                        st.session_state.dependency_graph_fig = fig
                        
                        st.success("✅ Analysis complete! Graph generated successfully.")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error during analysis: {str(e)}")
                        st.exception(e)
        
        else:
            # Show results
            st.markdown("""
            <div class="success-box">
            <strong>✅ Analysis Complete!</strong><br>
            Your dependency analysis has been generated successfully. Explore the results below.
            </div>
            """, unsafe_allow_html=True)
            
            # Results summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📁 Python Files", st.session_state.num_py_files)
            
            with col2:
                codebase_name = os.path.basename(st.session_state.codebase_path)
                st.metric("📊 Codebase", codebase_name)
            
            with col3:
                st.metric("🎯 Main File", os.path.basename(st.session_state.main_file))
            
            # Tabs for different views
            tab1, tab2, tab3 = st.tabs(["📈 Dependency Graph", "📋 Detailed Dependencies", "📄 Full Analysis"])
            
            with tab1:
                st.markdown("### 📈 Dependency Graph Visualization")
                st.markdown("The dependency graph shows the relationships between your main file and all its dependencies.")
                
                # Note about the graph
                st.info("""
                **Graph Legend:**
                - 🟡 **Yellow Square**: Main file
                - 🔴 **Red Circle**: Custom modules in your codebase
                - 🟢 **Green Circle**: Pre-built/standard library modules
                - 🟣 **Purple Circle**: Unknown/external modules
                """)
                
                # The graph should have been displayed by graph_maker function
                if st.session_state.dependency_graph_fig:
                    st.pyplot(st.session_state.dependency_graph_fig, use_container_width=True)
                else:
                    st.warning("⚠️ Graph figure not available.")
                
                # Save graph option
                if st.button("💾 Save Graph as Image", use_container_width=True):
                    try:
                        buf = save_graph_as_image(st.session_state.dependency_graph_fig)
                        st.download_button(
                            label="📥 Download Graph Image",
                            data=buf.getvalue(),
                            file_name=f"dependency_graph_{codebase_name}.png",
                            mime="image/png",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Error saving graph: {e}")
            
            with tab2:
                st.markdown("### 📋 Detailed Dependencies (Main File)")
                
                # Read and display detailed dependencies
                if hasattr(st.session_state, 'det_deps_path') and os.path.exists(st.session_state.det_deps_path):
                    with open(st.session_state.det_deps_path, 'r') as f:
                        detailed_deps = f.read()
                    
                    st.text_area(
                        "Detailed Dependencies:",
                        value=detailed_deps,
                        height=400,
                        disabled=True
                    )
                    
                    # Download option
                    st.download_button(
                        label="📥 Download Detailed Dependencies",
                        data=detailed_deps,
                        file_name=f"detailed_deps_{codebase_name}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                else:
                    st.warning("Detailed dependencies file not found.")
            
            with tab3:
                st.markdown("### 📄 Full Analysis Report (Entire Codebase)")
                
                # Display dependency store information
                if st.session_state.dependency_store:
                    deps_data = st.session_state.dependency_store.get_all_dependencies()
                    
                    # Files analyzed
                    st.markdown("#### 📁 Files Analyzed")
                    files = list(deps_data["files"].keys())
                    st.write(f"Total files: {len(files)}")
                    
                    # Show first few files
                    if files:
                        st.markdown("**Sample files:**")
                        for file in files[:10]:
                            st.markdown(f"• {file}")
                        if len(files) > 10:
                            st.markdown(f"... and {len(files) - 10} more")
                    
                    # Modules found
                    st.markdown("#### 📦 Modules Found")
                    modules = list(deps_data["modules"].keys())
                    st.write(f"Total modules: {len(modules)}")
                    
                    if modules:
                        st.markdown("**Sample modules:**")
                        for module in modules[:10]:
                            st.markdown(f"• {module}")
                        if len(modules) > 10:
                            st.markdown(f"... and {len(modules) - 10} more")
                    
                    # Download full JSON
                    json_data = json.dumps(deps_data, indent=2)
                    st.download_button(
                        label="📥 Download Full Analysis (JSON)",
                        data=json_data,
                        file_name=f"dependencies_{codebase_name}.json",
                        mime="application/json",
                        use_container_width=True
                    )
    
    # Step 5: Save & Export
    elif st.session_state.current_step == 5:
        st.markdown('<h2 class="section-header">💾 Step 5: Save & Export</h2>', unsafe_allow_html=True)
        
        if not st.session_state.analysis_complete:
            st.error("❌ No analysis results available. Please go back to Step 4 and generate the analysis.")
            return
        
        st.markdown("""
        <div class="success-box">
        <strong>✅ All Results Ready!</strong><br>
        Your analysis is complete. You can now save and export all results.
        </div>
        """, unsafe_allow_html=True)
        
        codebase_name = os.path.basename(st.session_state.codebase_path)
        
        # Export options
        st.markdown("### 📦 Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📈 Graph Export")
            if st.button("💾 Save Dependency Graph", use_container_width=True):
                try:
                    buf = save_graph_as_image(st.session_state.dependency_graph_fig)
                    st.download_button(
                        label="📥 Download Graph Image",
                        data=buf.getvalue(),
                        file_name=f"dependency_graph_{codebase_name}.png",
                        mime="image/png",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error saving graph: {e}")
        
        with col2:
            st.markdown("#### 📋 Data Export")
            
            # Detailed dependencies
            if hasattr(st.session_state, 'det_deps_path') and os.path.exists(st.session_state.det_deps_path):
                with open(st.session_state.det_deps_path, 'r') as f:
                    detailed_deps = f.read()
                
                st.download_button(
                    label="📥 Download Detailed Dependencies",
                    data=detailed_deps,
                    file_name=f"detailed_deps_{codebase_name}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            # Full analysis
            if st.session_state.dependency_store:
                deps_data = st.session_state.dependency_store.get_all_dependencies()
                json_data = json.dumps(deps_data, indent=2)
                
                st.download_button(
                    label="📥 Download Full Analysis (JSON)",
                    data=json_data,
                    file_name=f"dependencies_{codebase_name}.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        # Summary
        st.markdown("### 📊 Analysis Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📁 Python Files", st.session_state.num_py_files)
        
        with col2:
            st.metric("📊 Codebase", codebase_name)
        
        with col3:
            st.metric("🎯 Main File", os.path.basename(st.session_state.main_file))
        
        # Navigation
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Start New Analysis", use_container_width=True):
                # Reset session state
                for key in ['current_step', 'codebase_path', 'main_file', 'exclude_as_per_rqst_dirs', 
                           'exclude_as_per_rqst_files', 'analysis_complete', 'dependency_store', 
                           'num_py_files', 'dependency_graph_fig']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        
        with col2:
            if st.button("📊 View Graph Again", use_container_width=True):
                st.info("The dependency graph should be visible in a separate window. If not, please check your matplotlib backend settings.")

if __name__ == "__main__":
    main()