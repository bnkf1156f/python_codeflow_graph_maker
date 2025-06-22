import os
from worker import dependency_store_maker, graph_maker

if __name__=="__main__":
    codebase_path='D:/Projects/python_codeflow_graphmaker'
    main_file='D:/Projects/python_codeflow_graphmaker/gui.py'
    exclude_always_dirs=["venv", ".git", "__pycache__"]
    exclude_as_per_rqst_dirs=["codeflow_maker"] #as per request some dirs are ignored

    exclude_always_files=["ignore_this.py"]
    exclude_as_per_rqst_files=[]

    dependency_store, num_py_files=dependency_store_maker(
        folder_path=codebase_path,
        exclude_dirs=exclude_always_dirs+exclude_as_per_rqst_dirs,
        exclude_files=exclude_always_files+exclude_as_per_rqst_files
    )
    
    codebase_root = os.path.abspath(codebase_path)
    main_file_rel = os.path.relpath(main_file, codebase_root).replace("\\", "/")
    print("main_file_rel:", main_file_rel)
    det_deps_path=graph_maker(dependency_store=dependency_store, main_folder_path=codebase_path,
                            main_file_path=main_file_rel)