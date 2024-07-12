import util
import traceback

def generate_instances(json_conf_data, json_status_data, input_files_json_data):
  if not json_status_data:
    return []

  if 'huawei-system.json' not in input_files_json_data: return []

  generated_instances = []
  instances = return_list(json_status_data['network-instance']['instances']['instance'])
  for instance in instances:
    sites = return_list(instance['isis']['sites']['site'])
    for site in sites:
      if 'circuits' not in site or 'circuit' not in site['circuits']:
        circuits = []
      else:
        circuits = return_list(site['circuits']['circuit'])
      if 'peers' not in site or 'peer' not in site['peers']:
        peers = []
      else:
        peers = return_list(site['peers']['peer'])

      area_ids = []
      system_id = "N/A"
      if 'net-entitys' in site and 'net-entity' in site['net-entitys']:
        networks = return_list(site['net-entitys']['net-entity'])

        for network in networks:
          net = network['value'].split('.')
          area_id = net[0]
          area_ids.append(area_id)
          system_id = net[1] + '.' + net[2] + '.' + net[3]

      areas = " ".join(area_ids)
      for circuit in circuits:
        interface_instance = {}
        if 'is-name' in site:
          interface_instance['ne-node-id'] = site['is-name']
        else:
          interface_instance['ne-node-id'] = input_files_json_data['huawei-system.json']['system']['system-info']['sys-name']
        interface_instance['network-id'] = "isis:" + areas
        interface_instance['node-name'] = site['id']
        interface_instance['system-id'] = system_id
        interface_instance['node-id'] = "isis:" + interface_instance['ne-node-id'] + ':' + interface_instance['node-name']

        interface_instance['tp-id'] = "isis:" + interface_instance['ne-node-id'] + ':' + \
                                      interface_instance['node-name'] + ':' + circuit['name']
        name = circuit['name']
        name_label = name
        name_label = name_label.replace("GigabitEthernet", "GE")
        name_label = name_label.replace("LoopBack", "Lb")
        interface_instance['l3-termination-point-attributes.interface-name'] = name
        interface_instance['supporting-termination-point'] = interface_instance['ne-node-id'] + ":" + circuit['name']
        interface_instance['l3-termination-point-attributes.termination-point-type'] = 'interface-name'
        if 'disp-data' in circuit:
          interface_instance['l3-termination-point-attributes.unnumbered-id'] = circuit['disp-data']['index']
        if circuit['p2p-enable'] == "true":
           interface_instance['isis-termination-point-attributes.interface-type'] = "point-to-point"
        else:
           interface_instance['isis-termination-point-attributes.interface-type'] = "broadcast"

        if circuit['mesh-group']['state'] == 'inactive':
          interface_instance['isis-termination-point-attributes.is-passive'] = 'true'
        else:
          interface_instance['isis-termination-point-attributes.is-passive'] = 'false'

        interface_instance['isis-termination-point-attributes.level'] = circuit['level']
        interface_instance['label'] = 'ISIS ' + interface_instance['isis-termination-point-attributes.level'] + \
                                      ' interface: ' + name_label

        for peer in peers:
          if interface_instance['l3-termination-point-attributes.interface-name'] == peer['interface-name']:
            interface_instance['nbr-system-id'] = peer['system-id']
            interface_instance['nbr-ne-node-id'] = peer['host-name'].split('*')[0]
            interface_instance['l3-termination-point-attributes.ip-address'] = peer['ipv6-link-local-addr']
            interface_instance['circuit-id'] = peer['circuit-id']

        generated_instances.append(interface_instance)

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
