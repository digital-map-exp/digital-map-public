import json

from config.config import digital_map_scenarios_configured, generated_database
from util.dir_util import is_file, exists_path

def initiate_digital_map_scenarios(json_file):
    global digital_map_scenarios_configured

    if not exists_path(json_file):
        return
    if not is_file(json_file):
        return

    with open(json_file) as data_file:
        data=json.load(data_file)

    digital_map_scenarios_configured.clear()

    for response in data['scenarios']:
        scenario = response['scenario']
        digital_map_scenarios_configured.append(scenario)

def initiate_digital_map_db(json_file):
    global generated_database

    if not exists_path(json_file):
        return
    if not is_file(json_file):
        return

    with open(json_file) as data_file:
        data=json.load(data_file)

    generated_database.name = data["digital_map_db"]["name"]
    generated_database.uri = data["digital_map_db"]["uri"]
    generated_database.user = data["digital_map_db"]["user"]
    generated_database.password = data["digital_map_db"]["password"]




