import json
import os
import re

def load_js_file(file_name):
    with open(file_name + '.js', 'r') as f:
        if f.mode != 'r':
            raise Exception('Unable to load file')
        file_data = f.read()
  
    return file_data

def load_json_file(file_name):
    with open(file_name + '.json', 'r') as file:
        json_data = json.load(file)
        return json_data

def get_function_names_from_js_file(file_name):
    function_dict = {}
    values = []
    
    function_pattern = re.compile(r'function[ ]+(?P<name>[^ (]+)[^)]*[)]')
    with open(file_name + '.js', 'r') as f:
        if f.mode != 'r':
            raise Exception('Unable to load file')
     
        for line in f:
            res = function_pattern.search(line)
            if res is not None:
                values.append({'name' : res.group(1)})
        
        function_dict['values'] = values
        
    return function_dict
    
def write_to_json(data, file_name, file_path=None):
    output_path = '/'.join([os.path.dirname(os.path.abspath(__file__)), file_name])
    if file_path:
       output_path = '/'.join([file_path, file_name])
    
    with open(output_path+'.json', 'w') as outfile:
       json.dump(data, outfile) 

def write_to_js(data, file_name, file_path=None):
    output_path = '/'.join([os.path.dirname(os.path.abspath(__file__)), file_name])
    if file_path:
       output_path = '/'.join([file_path, file_name])
    with open(output_path + '.js', 'w') as file:
        file.write(str(data).strip())
        
def get_dict_from_list(dictionary_key, list):
    for index in len(list):
        if dictionary_key in list[index]:
            return list[index]
    return None 

if __name__ == '__main__':
    file = load_js_file('Code')
    function_dict = get_function_names_from_js_file('Code')
    print(json.dumps(function_dict))
    