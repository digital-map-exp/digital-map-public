import os
from shutil import copytree, rmtree, copy


def exists_path(path):
    return os.path.exists(path)

def is_file(path):
    return os.path.isfile(path)

def create_dir(path):
    if not os.path.exists(path):
        os.mkdir(path)
def create_dirs(path):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)

def del_dir(path):
    if os.path.exists(path):
        rmtree(path)

def copy_dir(path1, path2):
    if os.path.exists(path1):
        copytree(path1, path2)

def get_files(path):
    return os.listdir(path)
def get_folders(path):
    dir_list = os.listdir(path)
    return dir_list

def get_all_files(path):
    dir_list = os.listdir(path)
    all_files = list()
    for entry in dir_list:
        full_path = os.path.join(path, entry)
        full_path = full_path.replace('\\','/')
        if os.path.isdir(full_path):
            all_files = all_files + get_all_files(full_path)
        else:
            all_files.append(full_path)
    return all_files

def get_file_name(full_path):
    return os.path.basename(full_path)

def copy_files(path1, path2):
    if os.path.exists(path1):
        if not os.path.exists(path2):
            os.mkdir(path2)
        files = os.listdir(path1)
        for file_name in files:
            copy(path1 + "/" + file_name, path2 + "/" + file_name)
