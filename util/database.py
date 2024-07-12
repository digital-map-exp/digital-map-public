
class DatabaseInfo:
    # Data class to store the connection info towards the DB
    def __init__(self, name, uri, user, password):
        self.name = name
        self.uri = uri
        self.user = user
        self.password = password