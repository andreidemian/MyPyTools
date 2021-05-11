import yaml
import os

class RWYamlFile:
    
    def __init__(self,path_to_yaml_file=None):
        self.yaml_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),'test.yml')
        if(path_to_yaml_file):
            self.yaml_file = path_to_yaml_file
    
    def get_to_dic(self):
        with open(self.yaml_file) as ymlrf:
            data = yaml.load(ymlrf, Loader=yaml.FullLoader)
        return data
    
    def write_to_file(self, data):
        with open(self.yaml_file, 'w') as w_yml:
            yaml.dump(data, w_yml)