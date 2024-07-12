import sys

from util.app_logger import get_my_logger
logger = get_my_logger(__name__)

def delete_dict_elements(specified_key, dict_data):

    if isinstance(dict_data, dict) or isinstance(dict_data, list):
        for key in list(dict_data):
            try:
                if key == specified_key:
                    del dict_data[key]
                else:
                    value = dict_data[key]
                    if isinstance(value, dict):
                        delete_dict_elements(specified_key, value)
                    elif isinstance(value, list):
                        for member in value:
                            if isinstance(member, dict) or isinstance(member, list):
                                delete_dict_elements(specified_key, member)
            except:
                error = str(sys.exc_info())
                logger.error("delete dict elements ERROR", error)
                logger.error("ERROR FOR KEY: {0}".format(key))