

#login configuration
login_file_formatter = '%(asctime)s %(levelname)-6s  module:%(module)-23s     function:%(funcName)-29s     %(message)-30s'
login_console_formatter = '%(levelname)s -- %(message)s'
login_file = "logfile.log"

# login levels: INFO, WARNING, ERROR, CRITICAL, NOTSET, DEBUG
CRITICAL = 50
ERROR = 40
WARNING = 30
INFO = 20
DEBUG = 10
NOTSET = 0
login_file_level = DEBUG
login_console_level = INFO
logger_level = DEBUG

