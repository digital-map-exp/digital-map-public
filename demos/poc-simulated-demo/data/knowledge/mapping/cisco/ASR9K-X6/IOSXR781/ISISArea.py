
#json_conf_data: [],
#input_files_json_data: "openconfig-network-instance.json"

def generate_instances(json_conf_data, json_status_data, input_files_json_data):
  if not input_files_json_data:
    return []

  generated_instances = []
  if 'openconfig-network-instance.json' not in input_files_json_data or 'Network.json' not in input_files_json_data:
    return []

  vpn_instances = return_list(input_files_json_data['openconfig-network-instance.json']['network-instances']['network-instance'])
  for vpn_instance in vpn_instances:
    if 'protocols' not in vpn_instance:
      continue

    protocols = return_list(vpn_instance['protocols']['protocol'])
    for protocol in protocols:
      if 'isis' not in protocol:
        continue

      isis_instance = protocol['isis']

      instance = {}

      instance['network-id'] = "isis:" + isis_instance['global']['config']['net'].split('.')[0]
      instance['network-types'] = "ietf-l3-unicast-topology:l3-unicast-topology,ietf-l3-isis-topology:isis-topology"
      instance['l3-topology-attributes.name'] = isis_instance['global']['config']['net'].split('.')[0]
      instance['l3-topology-attributes.flag'] = 'isis'
      instance['area-address'] = isis_instance['global']['config']['net'].split('.')[0]
      instance['level'] = isis_instance['global']['config']['level-capability']
      instance['supporting_network_id'] = return_value(input_files_json_data, ['Network.json', 'Network', 'network-id'])

      instance['label'] = 'ISIS ' + instance['level'] + ' area:' + instance['area-address']
      generated_instances.append(instance)

  return generated_instances

# if container returns the list of 1 container, if list it just returns it
# the reason is that json does not have [] when only 1 element for the yang list
def return_list(json_data):
    instances_list = []
    if isinstance(json_data, dict):
      instances_list.append(json_data)
    elif isinstance(json_data, list):
      instances_list = json_data
    return instances_list


def return_value(container, path_list):
  lenght = len(path_list)
  i = 0
  current_container = container
  for path in path_list:
    if path not in current_container: return ""
    current_container = current_container[path]

  return current_container
