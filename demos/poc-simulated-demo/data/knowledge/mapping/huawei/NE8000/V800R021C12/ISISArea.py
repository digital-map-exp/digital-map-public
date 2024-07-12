import util
import traceback

def generate_instances(json_conf_data, json_status_data, input_files_json_data):
  if not json_status_data:
    return []

  if 'Network.json' not in input_files_json_data:
    return []

  generated_instances = []
  instances = return_list(json_status_data['network-instance']['instances']['instance'])
  for instance in instances:
    sites = return_list(instance['isis']['sites']['site'])
    for site in sites:
      if 'net-entitys' in site and 'net-entity' in site['net-entitys']:
        area_instance = {}
        area_instance['network-types'] = "ietf-l3-unicast-topology:l3-unicast-topology,ietf-l3-isis-topology:isis-topology"
        area_instance['l3-topology-attributes.flag'] = 'isis'
        area_instance['level'] = site['level']
        area_instance['supporting-network'] = \
          return_value(input_files_json_data, ['Network.json', 'Network', 'network-id'])

        networks = return_list(site['net-entitys']['net-entity'])

        area_ids = []
        for network in networks:
          net = network['value'].split('.')
          area_id = net[0]
          area_ids.append(area_id)

        areas = " ".join(area_ids)
        area_instance['network-id'] = "isis:" + areas
        area_instance['l3-topology-attributes.name'] = areas
        area_instance['area-address'] = areas
        area_instance['label'] = 'ISIS ' + area_instance['level'] + ' area:' + areas
        generated_instances.append(area_instance)

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
