import re

def get_function_names_from_js_file(file_name):
    function_dict = {}
    values = []
    
    function_pattern = re.compile(r'function[ ]+(?P<name>[^ (]+)[^)]*[)]')
    with open(file_name, 'r') as f:
        if f.mode != 'r':
            raise Exception('Unable to load file')
     
        for line in f:
            res = function_pattern.search(line)
            if res is not None:
                values.append({'name' : res.group(1)})
        
        function_dict['values'] = values
        
    return function_dict
    


    