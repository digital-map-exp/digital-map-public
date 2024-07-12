from datetime import datetime

from util.app_logger import get_my_logger, login_decorator
from util.dir_util import copy_dir, del_dir, get_files

from digital_map.model.digital_map_entity import find_digital_map_entities, DigitalMapEntity
from digital_map.model.digital_map_files import generate_entity_file, find_entity_instances

import json


logger = get_my_logger(__name__)

# Generate xml and json files, from files generated from netconf or rest/restconf collection,
# knowledge and other data input

@login_decorator

def generate_dm_entities(datetime_results_path, dm_directories, netconf_devices, external_systems):

    entities_results_path = datetime_results_path + "/" + dm_directories['results']['entities']

    generated_path_dict = {}

    for device_info in netconf_devices:
        device_path = dm_directories['generated']['netconf'] + '/' + device_info.sys_type + "-" + device_info.host
        generated_path_dict[device_path] = device_info

    for external_system_info in external_systems:
        ext_system_path = dm_directories['generated']['intents'] + '/' + external_system_info.sys_type + "-" + external_system_info.host
        generated_path_dict[ext_system_path] = external_system_info

    all_external_systems = []
    all_external_systems.extend(netconf_devices)
    all_external_systems.extend(external_systems)

    #find all entities with mapping for all devices
    entities = find_digital_map_entities(all_external_systems,
                                         dm_directories['input']['knowledge']['entities'],
                                         dm_directories['input']['knowledge']['mapping'])

    entity: DigitalMapEntity
    for entity in entities:
        all_entity_instances = []

        start = datetime.today()

        # add entity instances from the device info collected from netconf and from system vian rest/restconf
        for system_path in generated_path_dict:
            device_entity_instances = generate_dm_entities_system(dm_directories, entity,
                                                                  system_path, generated_path_dict[system_path])
            if device_entity_instances:
                all_entity_instances.extend(device_entity_instances)

        # add entity instances from the file system
        csv_entity_instances = find_entity_instances(dm_directories['input']['data']['entities']['csv'], entity.type)
        all_entity_instances.extend(csv_entity_instances)

        entity_columns = entity.get_columns()
        # remove duplicate entries, does not work with converting to set because of TypeError, unhashable dict type
        # add meta data from knowledge
        aggregated_entity_instances = []
        entity_id_list = []
        for generated_instance in all_entity_instances:
            entityID = entity.generate_entity_id(entity.type, generated_instance)
            if entityID in entity_id_list:
                continue
            else:
                if ("compute" in entity.layer):
                    layer = entity.compute_layer(generated_instance, entity.layer['compute'])
                    generated_instance["layer"] = layer
                else:
                    generated_instance["layer"] = entity.layer
                generated_instance["sublayer"] = entity.sublayer
                generated_instance["topologyRole"] = entity.topology_role
                generated_instance["entityType"] = entity.type
                generated_instance["entityID"] = entityID
                entity_id_list.append(entityID)
                aggregated_entity_instances.append(generated_instance)

        if aggregated_entity_instances:
            generate_entity_file(datetime_results_path, entities_results_path,
                                 entity.type, entity_columns, aggregated_entity_instances)

        end = datetime.today()
        duration = end - start
        logger.info("Entity {} generation duration {}".format(entity.type, duration.total_seconds()))
    del_dir(dm_directories['generated']['entities'])
    copy_dir(entities_results_path, dm_directories['generated']['entities'])

@login_decorator
def generate_dm_entities_system(dm_directories, entity, system_path, system_info):
    generated_file_json_data = ""
    generated_file_config_json_data = ""
    optimized_config_json_data = {}
    input_files_json_data = {}

    generated_file = entity.get_generated_file(system_info)
    generated_file_config, generated_file_config_scope = entity.get_generated_file_config(system_info)
    input_external_files = entity.get_input_external_files(system_info)
    input_internal_files = entity.get_input_internal_files(system_info)

    device_entity_instances = None

    try:
        if generated_file:
            with open(system_path + "/json/" + generated_file) as entity_instance_file:
                generated_file_json_data = json.load(entity_instance_file)

        if generated_file_config:
            with open(system_path + "/json/" + generated_file_config) as entity_instance_file:
                generated_file_config_json_data = json.load(entity_instance_file)
                for item in generated_file_config_scope:
                    optimized_config_json_data[item] = generated_file_config_json_data[item]

        for input_file in input_external_files:
            with open(system_path + "/json/" + input_file) as entity_instance_file:
                input_files_json_data[input_file] = json.load(entity_instance_file)

        for input_file in input_internal_files:
            with open(dm_directories['input']['data']['entities']['json'] + "/" + input_file) as entity_instance_file:
                input_files_json_data[input_file] = json.load(entity_instance_file)

        device_entity_instances = \
            entity.generate_instances_system(system_info, system_path,
                                             optimized_config_json_data,
                                             generated_file_json_data,
                                             input_files_json_data,
                                             dm_directories['input']['data']['entities']['json'])
    except Exception as e:
        logger.error("ERROR: generate_dm_entities_system ", e)
        logger.error("Generation of DM entities failed for system {} and entity {}".format(system_path, entity.type))

    return device_entity_instances