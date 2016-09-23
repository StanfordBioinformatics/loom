import os
from ConfigParser import SafeConfigParser

class ServerInfo:
    def __init__(self):
        DEFAULT_SETTINGS_FILE = os.path.join(os.getenv('HOME'), '.loom', 'server.cfg')
        self.config_parser = SafeConfigParser()
        if not os.path.exists(DEFAULT_SETTINGS_FILE):
            print 'No config file found at %s. Creating a new one.'
            self.config_parser.add_section('server')
            self.config_parser.set('server', 'ip', '127.0.0.1')
            self.config_parser.set('server', 'port', '8000')
            with open(DEFAULT_SETTINGS_FILE, 'w') as cfgfile:
                self.config_parser.write(cfgfile)
        
        self.config_parser.read(DEFAULT_SETTINGS_FILE)
        try:
            self.ip = self.config_parser.get('server', 'ip')
            self.port = self.config_parser.get('server', 'port')
        except NoOptionError:
            print 'Invalid config file found at %s. Please edit it and try again.' 
    
