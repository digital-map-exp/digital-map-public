
from util.app_logger import get_my_logger, login_decorator
from util.dir_util import create_dir, del_dir, copy_dir

from netconf.netconf_scenarios import netconf_scenarios
from digital_map.model.digital_map_entity import find_digital_map_entities

logger = get_my_logger(__name__)

# Collect from devices via neconf and generate xml and json files, knowledge driven for xpath
@login_decorator
def generate_device_entities(datetime_results_path, dm_directories, netconf_scenarios_configured, netconf_devices):

    netconf_path = datetime_results_path + "/" + dm_directories['results']['netconf']
    generated_path_netconf = dm_directories['generated']['netconf']
    entities_knowledge = dm_directories['input']['knowledge']['entities']
    mapping_knowledge = dm_directories['input']['knowledge']['mapping']

    # run netconf tests and collect from device
    # this is now driven by the config_netconf paths, this would be driven by mapping
    # generate xml and json files from netconf queries
    create_dir(netconf_path)
    generated_path_dict = {}
    for device_info in netconf_devices:
        device_path = netconf_path + '/' + device_info.sys_type + "-" + device_info.host
        create_dir(device_path)
        generated_path_dict[device_path] = device_info

        # Run scenario from config, if current configuration or path list required outside knowledge
        # only enable for xpath testing during debugging, otherwise xpath is done in generate_device_files_model_driven
        execute_configurable_scenarios(device_path, device_info, netconf_scenarios_configured)

        # Run netconf scenario from knowledge
        generate_device_files_model_driven(device_path, device_info,entities_knowledge, mapping_knowledge)

    # Copy results files to the generated dir
    del_dir(generated_path_netconf)
    copy_dir(netconf_path, generated_path_netconf)

@login_decorator
def execute_configurable_scenarios(device_path, device_info, netconf_scenarios_configured):
    for scenario in netconf_scenarios_configured:
        doSomething = getattr(netconf_scenarios, scenario)
        doSomething(netconf_scenarios(device_path, device_info))

@login_decorator
def generate_device_files_model_driven(device_path, device_info, entities_knowledge, mapping_knowledge):

    netconf = netconf_scenarios(device_path, device_info)
    # find all entities with mapping for this device only
    device_info_list = []
    device_info_list.append(device_info)
    entities = find_digital_map_entities(device_info_list, entities_knowledge, mapping_knowledge)
    for entity in entities:
        xpaths = entity.get_entity_xpaths(device_info)
        generated_file = entity.get_generated_file(device_info)
        if (len(xpaths) == 0) or (generated_file == None):
            continue
        netconf.get_xpath_list_entity(entity.type, generated_file, xpaths)
