
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
      if 'interfaces' not in isis_instance:
        continue

      interfaces = return_list(isis_instance['interfaces']['interface'])
      for interface in interfaces:
        instance = {}

        instance['ne-node-id'] = input_files_json_data['openconfig-system.json']['system']['state']['hostname']
        instance['node-name'] = isis_instance['global']['state']['instance']
        instance['node-id'] = 'isis:' + instance['ne-node-id'] + ':' + instance['node-name']
        instance['network-id'] = 'isis:' + isis_instance['global']['config']['net'].split('.')[0]
        instance['system-id'] = isis_instance['global']['config']['net'].split('.')[1] + '.' + \
                                isis_instance['global']['config']['net'].split('.')[2] + '.' + \
                                isis_instance['global']['config']['net'].split('.')[3]
        instance['tp-id'] = instance['node-id'] + ':' + interface['interface-id']
        name = interface['interface-id']
        name_label = name
        name_label = name_label.replace("GigabitEthernet", "GE")
        name_label = name_label.replace("HundredGigE", "100GE")
        name_label = name_label.replace("TenGigE", "10GE")
        name_label = name_label.replace("LoopBack", "Lb")

        instance['interface-name'] = name

        instance['supporting-termination-point'] = instance['ne-node-id']  + ":" +  interface['interface-id']
        instance['isis-termination-point-attributes.level'] = isis_instance['global']['config']['level-capability']
        instance['label'] = 'ISIS ' + instance['isis-termination-point-attributes.level'] + \
                            ' interface: ' + name_label

        if 'state' in interface:
          instance['l3-termination-point-attributes.termination-point-type'] = 'interface-name'
          instance['l3-termination-point-attributes.interface-name'] = interface['state']['interface-id']
          instance['isis-termination-point-attributes.is-passive'] = interface['state']['passive']
          instance['isis-termination-point-attributes.interface-type'] = interface['state']['circuit-type']

        adjacency_count = 0
        if 'levels' not in interface or 'level' not in interface['levels']:
          generated_instances.append(instance)
          continue
        levels = return_list(interface['levels']['level'])
        levels_list = []
        for level in levels:
          levels_list.append(level['level-number'])
          if 'adjacencies' not in level or 'adjacency' not in level['adjacencies']:
            continue
          adjacencies = return_list(level['adjacencies']['adjacency'])
          for adjacency in adjacencies:
            instance['nbr-system-id'] = adjacency['system-id']
            instance['nbr-ne-node-id'] = adjacency['system-id']
            adjacency_count += 1

        if '1' in levels_list and '2' not in levels_list:
          instance['isis-termination-point-attributes.level'] = 'level-1'
        elif '1' not in levels_list and '2' in levels_list:
          instance['isis-termination-point-attributes.level'] = 'level-2'
        elif '1' in levels_list and '2' in levels_list:
          instance['isis-termination-point-attributes.level'] = 'level-1-2'

        instance['label'] = 'ISIS ' + instance['isis-termination-point-attributes.level'] + \
                            ' interface: ' + name_label
        if adjacency_count == 0:
          generated_instances.append(instance)
          continue

        if 'levels' not in isis_instance or 'level' not in isis_instance['levels']:
          generated_instances.append(instance)
          continue
        levels = return_list(isis_instance['levels']['level'])
        for level in levels:
          if 'link-state-database' not in level or 'lsp' not in level['link-state-database']:
            generated_instances.append(instance)
            continue

          lsps = return_list(level['link-state-database']['lsp'])
          for lsp in lsps:
            circuit = lsp['lsp-id'].split('-')[0]
            if 'tlvs' not in lsp or 'tlv' not in lsp['tlvs']:
              continue
            tlvs = return_list(lsp['tlvs']['tlv'])
            for tlv in tlvs:
              if tlv['type'] != 'EXTENDED_IS_REACHABILITY':
                continue
              neighbors = return_list(tlv['extended-is-reachability']['neighbors']['neighbor'])
              if len(neighbors) == 2:
                if neighbors[0]['system-id'] == instance['nbr-system-id'] and neighbors[1]['system-id'] == instance['system-id']:
                  instance['circuit-id'] = circuit
                if neighbors[1]['system-id'] == instance['nbr-system-id'] and neighbors[0]['system-id'] == instance['system-id']:
                  instance['circuit-id'] = circuit

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
