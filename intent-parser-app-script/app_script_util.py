import json

def load_js_file(file_name):
    f = open(file_name + '.js', 'r')
    if f.mode != 'r':
        raise Exception('Unable to load file')
    return f.read()

def load_json_file(file_name):
    with open(file_name + '.json', 'r') as file:
        json_data = json.load(file)
        return json_data
    

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