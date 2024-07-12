

def import_code(relative_path, python_package):
    import importlib
    import sys

    sys.path.append(relative_path)

    module = importlib.import_module(python_package)
    return module


