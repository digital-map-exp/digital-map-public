import json
from util.dir_util import copy_dir, del_dir, is_file, exists_path

from config.config import dm_directories

def initiate_data(entities_dir):
    global dm_directories

    project_entities_dir = dm_directories['input']['data']['entities']['entities']
    del_dir(project_entities_dir)
    if not exists_path(entities_dir):
        return
    if is_file(entities_dir):
        return
    copy_dir(entities_dir, project_entities_dir)

def initiate_network_simulation_netconf(simulation_dir):
    global dm_directories

    netconf_dir = dm_directories['generated']['netconf']
    del_dir(netconf_dir)

    if not exists_path(simulation_dir):
        return
    if is_file(simulation_dir):
        return

    copy_dir(simulation_dir, netconf_dir)

def initiate_network_simulation_csv(simulation_dir):
    global dm_directories

    entities_dir = dm_directories['generated']['entities']
    del_dir(entities_dir)
    if not exists_path(simulation_dir):
        return
    if is_file(simulation_dir):
        return
    copy_dir(simulation_dir, entities_dir)
