from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import app_script_util as util
import datetime
import json

class AppScriptAPI:
    '''
    A list of APIs to access a Google Add-on Script Project:
    '''
 
    def __init__(self, creds):
        self._service = build('script', 'v1', credentials=creds)
    
   
    def get_project_metadata(self, script_id, version_number=None):
        if version_number is None:
            return self._service.projects().getContent(
                scriptId=script_id).execute()
                
        return self._service.projects().getContent(
            scriptId=script_id,
            versionNumber=version_number).execute() 
    
    def get_project_versions(self, script_id):
        '''
        Get a list of versions generated for the project
        
        Returns:
            A list of integers. An empty list is returned if no version exist on the project
        '''
        response = self._service.projects().versions().list(
            scriptId=script_id).execute()
        if not response:
            return []
        list_of_versions = self._get_versions(script_id, response, [])
        return list_of_versions
    
    def _get_versions(self, script_id, response, list_of_versions):
        if 'nextPageToken' not in response:
            list_of_versions.extend(self._get_version_number(response['versions']))
            return list_of_versions
        
        next_page_token = response['nextPageToken']
        response = self._service.projects().versions().list(
            scriptId=script_id,
            pageToken=next_page_token).execute()
        list_of_versions.extend(self._get_version_number(response['versions']))
        self._get_versions(response, list_of_versions)
        
    def _get_version_number(self, version_list):
        version_numbers = []
        for index in range(len(version_list)):
            version_dict = version_list[index]
            version_numbers.append(version_dict['versionNumber'])
        return version_numbers
    
    def get_head_version(self, script_id):
        '''
        Get the latest project version.
        '''
        list_of_versions = self.get_project_versions(script_id)
        if not list_of_versions:
            return 0
        
        return max(list_of_versions)
    
    def _get_manifest_file_index(self, file_list):
        for index in range(len(file_list)):
            file = file_list[index]
            file_type = file['type']
            file_name = file['name']
            
            if file_type == 'JSON' and file_name == 'appsscript':
                return index
        
        return None
    
    def _get_code_file_index(self, file_list):
        for index in range(len(file_list)):
            file = file_list[index]
            file_type = file['type']
            file_name = file['name']
            
            if file_type == 'SERVER_JS' and file_name == 'Code':
                return index
        
        return None
    
    def load_local_manifest(self, manifest_name='appsscript'):
        file = util.load_json_file(manifest_name)
        return file
    
    def load_local_code(self, code_name='Code'):
        file = util.load_js_file(code_name)
        return str(file).strip()
    
    def update_remote_manifest(self, response):
        file_list = response['files']
        index = self._get_manifest_file_index(file_list)
        file_list[index]['source'] = self.load_local_manifest()
        request = {'files' : file_list}
        return request
    
    def update_remote_code(self, response):
        file_list = response['files']
        code_index = self._get_code_file_index(file_list)
        file_list[code_index]['source'] = self.load_local_code()
        request = {'files' : file_list}
        return request
    
    def update_metadata(self, response):
        file_list = response['files']
        code_index = self._get_code_file_index(file_list)
        file_list[code_index]['source'] = self.load_local_code()
        
        manifest_index = self._get_manifest_file_index(file_list)
        file_list[manifest_index] = self.load_local_manifest()
        request = {'files' : file_list}
        return request
    
    def update_project(self, script_id, response):
        request = self.update_metadata(response)
        return self._service.projects().updateContent(
            body=request,
            scriptId=script_id).execute()
            
    def create_project(self, project_title, doc_id):
        '''
        Create a new Add-on script project bounded to a document.
        
        Args: 
            doc_id: id of Google Doc the script project will create from
            project_title: name of the script project
        
        Return:
            The ID generated for the script project
        '''
        request = {
            'title': project_title,
            'parentId': doc_id
        }
        response = self._service.projects().create(
            body=request).execute()
        return response['scriptId']
            
        
    def create_version(self, script_id, number, description):
        d = datetime.datetime.utcnow()
        created_time = d.isoformat("T") + "Z"
        
        request = {
            'versionNumber': number,
            'description': description,
            'createTime': created_time
            }
        version_obj = self._service.projects().versions().create(
            scriptId=script_id,
            body=request).execute()
        
        return version_obj
    
    def get_deployment(self, script_id, deployment_id):
        response = self._service.projects().deployments().get(
            scriptId=script_id,
            deploymentId=deployment_id).execute()
            
        return response
    
    def create_deployment(self, script_id, deploy_version, description):
        request = {
            'versionNumber': deploy_version,
            'manifestFileName': 'appsscript',
            'description': description
        }
        return self._service.projects().deployments().create(
            scriptId=script_id,
            body=request).execute()
        
    def run_script(self, script_id, function_name, dev_mode=False):   
        request = {
            'function': function_name,
            'devMode': dev_mode
        }
        return self._service.scripts().run(
            scriptId=script_id,
            body=request
            ).execute()
    
    
    def update_deployment(self, script_id, deploy_id, version_number, description):
        request = {
            'deploymentConfig': {
                'scriptId': script_id, 
                'versionNumber': version_number,
                'manifestFileName': 'appsscript',
                'description': description
            }
        }
        return self._service.projects().deployments().update(
            scriptId=script_id,
            deploymentId=deploy_id).execute()
        