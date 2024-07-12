import json
from util.dir_util import copy_dir, del_dir, is_file, exists_path

from config.config import dm_directories

def initiate_knowledge(knowledge_dir):
    global dm_directories

    project_knowledge_dir = dm_directories['input']['knowledge']['knowledge']
    del_dir(project_knowledge_dir)

    if not exists_path(knowledge_dir):
        return
    if is_file(knowledge_dir):
        return

    copy_dir(knowledge_dir, project_knowledge_dir)


