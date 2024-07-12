
#json_conf_data: [],
#input_files_json_data: "openconfig-network-instance.json"

def generate_instances(json_conf_data, json_status_data, input_files_json_data):
  if not input_files_json_data:
    return []

  generated_instances = []
  if 'openconfig-network-instance.json' not in input_files_json_data or \
          'openconfig-system.json' not in input_files_json_data:
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

      instance['ne-node-id'] = input_files_json_data['openconfig-system.json']['system']['state']['hostname']
      instance['supporting-node'] = instance['ne-node-id']
      instance['l3-node-attributes.name'] = isis_instance['global']['state']['instance']
      instance['node-id'] = 'isis:' + instance['ne-node-id'] + ':' + instance['l3-node-attributes.name']
      instance['network-id'] = "isis:" + isis_instance['global']['config']['net'].split('.')[0]
      instance['l3-node-attributes.flag'] = 'isis'
      instance['l3-node-attributes.prefix'] = 'TODO l3-node-attributes.prefix'
      instance['isis-node-attributes.system-id'] = isis_instance['global']['config']['net'].split('.')[1] + '.' + \
                              isis_instance['global']['config']['net'].split('.')[2] + '.' + \
                              isis_instance['global']['config']['net'].split('.')[3]
      instance['l3-node-attributes.router-id'] = instance['isis-node-attributes.system-id']

      instance['l3-node-attributes.prefix'] = 'TODO'

      instance['isis-node-attributes.area-address'] = isis_instance['global']['config']['net'].split('.')[0]

      instance['isis-node-attributes.level'] = isis_instance['global']['config']['level-capability']
      if isis_instance['global']['config']['level-capability'] == 'LEVEL_1':
        if 'interfaces' not in isis_instance or 'interface' not in isis_instance['interfaces']:
          interfaces = []
        else:
          interfaces = return_list(isis_instance['interfaces']['interface'])
        for interface in interfaces:
          if 'levels' not in interface or 'level' not in interface['levels']:
            levels = []
          else:
            levels = return_list(interface['levels']['level'])
          for level in levels:
            if level['level-number'] == '2':
              instance['isis-node-attributes.level'] = 'level-1-2'

      instance['isis-node-attributes.lsp-lifetime'] = "DISCUSS WITH OSCAR FOR OPENCONFIG"
      instance['isis-node-attributes.lsp-refresh-interval'] = "DISCUSS WITH OSCAR FOR OPENCONFIG"

      instance['isis-timer-attributes.lsp-mtu'] = "DISCUSS WITH OSCAR FOR OPENCONFIG"
      instance['isis-timer-attributes.lsp-lifetime'] = "DISCUSS WITH OSCAR FOR OPENCONFIG"
      instance['isis-timer-attributes.lsp-refresh-interval'] = "DISCUSS WITH OSCAR FOR OPENCONFIG"
      instance['isis-timer-attributes.poi-tlv'] = isis_instance['global']['state']['poi-tlv']

      instance['label'] = 'ISIS ' + instance['isis-node-attributes.level'] + " system: " + \
                                  instance['isis-node-attributes.system-id'].replace('0000.','')

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
