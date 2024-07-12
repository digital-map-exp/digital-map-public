

class ExternalSystemInfo:
    """Data class to store the device information."""
    def __init__(self, category: str, sys_vendor: str, sys_type: str, software_version:str,
                 host: str, port: int,
                 username: str, password: str, device_handler: str,
                 device_name = "DefaultName"):
        self.category: str = category
        self.sys_vendor: str = sys_vendor
        self.sys_type: str = sys_type
        self.software_version: str = software_version
        self.host: str = host
        self.port: int = port
        self.username: str = username
        self.password: str = password
        self.device_handler = device_handler



