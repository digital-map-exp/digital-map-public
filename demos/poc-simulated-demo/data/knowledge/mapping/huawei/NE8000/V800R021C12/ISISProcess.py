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

      process_instance = {}
      process_instance['network-id'] = "isis:" + areas
      process_instance['isis-node-attributes.area-address'] = areas
      process_instance['l3-node-attributes.name'] = site['id']
      process_instance['ne-node-id'] = input_files_json_data['huawei-system.json']['system']['system-info']['sys-name']
      process_instance['node-id'] = "isis:" + process_instance['ne-node-id'] + ':' + process_instance['l3-node-attributes.name']
      process_instance['l3-node-attributes.router-id'] = system_id
      process_instance['isis-node-attributes.system-id'] = system_id
      process_instance['l3-node-attributes.flag'] = 'isis'
      process_instance['l3-node-attributes.prefix'] = ''
      process_instance['isis-node-attributes.level'] = site['level']
      if site['level'] == 'level-1':
        if 'circuits' not in site or 'circuit' not in site['circuits']:
          circuits = []
        else:
          circuits = return_list(site['circuits']['circuit'])
        for circuit in circuits:
          if circuit['level'] == 'level-1-2':
            process_instance['isis-node-attributes.level'] = circuit['level']

      process_instance['isis-node-attributes.lsp-lifetime'] = site['timer']['lsp-max']
      process_instance['isis-node-attributes.lsp-refresh-interval'] = site['timer']['lsp-refresh']

      process_instance['isis-timer-attributes.lsp-mtu'] = "DISCUSS WITH OSCAR: "
      process_instance['isis-timer-attributes.lsp-lifetime'] = site['timer']['lsp-max']
      process_instance['isis-timer-attributes.lsp-refresh-interval'] = site['timer']['lsp-refresh']
      process_instance['isis-timer-attributes.poi-tlv'] = "DISCUSS WITH OSCAR: "

      process_instance['label'] = 'ISIS ' + process_instance['isis-node-attributes.level'] + " system: " + \
                                  process_instance['isis-node-attributes.system-id'].replace('0000.','')
      process_instance['supporting-node'] = process_instance['ne-node-id']

      generated_instances.append(process_instance)

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
