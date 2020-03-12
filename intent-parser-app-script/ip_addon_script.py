from app_script_api import AppScriptAPI
from drive_api import DriveAPI
from googleapiclient import errors
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import datetime
import json 
import pickle
import os.path
import script_util as util

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/script.projects',
          'https://www.googleapis.com/auth/script.deployments',
          'https://www.googleapis.com/auth/documents',
          'https://www.googleapis.com/auth/drive.readonly']

MAXIMUM_CREATE_QUOTA = 50
DOCUMENT_SIZE = 0
NUMBER_OF_CREATION = 0
INCOMPLETE_DOCS = []

def authenticate_credentials():
    """
    Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds    

def _contain_folder_id(id, local_folders):
    for j in range(len(local_folders)):
        l_folder = local_folders[j]
        if id == l_folder['id']:
            return True
    return False

def _contain_document_id(id, local_documents):
    for j in range(len(local_documents)):
        l_doc = local_documents[j]
        if id == l_doc['id']:
            return True
    return False

def _get_local_document(id, local_documents):
    for j in range(len(local_documents)):
        l_doc = local_documents[j]
        if id == l_doc['id']:
            return l_doc
    return None

def update_logged_folders(folder_id):  
    '''
    Update logged_folders.json with new folders found in the given folder_id
    ''' 
    print('Updating logged_folders.json')
    creds = authenticate_credentials()
    
    drive_api = DriveAPI(creds)
    remote_folders = drive_api.get_subfolders_from_folder(folder_id)
   
    updated_data = {} 
    with open('logged_folders.json') as in_file:
        f_data = json.load(in_file)
        local_folders = f_data['folders']
        
        d = datetime.datetime.utcnow()
        current_time = d.isoformat("T") + "Z"
        for i in range(len(remote_folders)):
            r_folder = remote_folders[i]
            r_id = r_folder['id']
            if _contain_folder_id(r_id, local_folders):
                local_folders[i]['updateTime'] = current_time
            else:
                f_dict = {}
                f_dict['id'] = r_id
                f_dict['name'] = r_folder['name']
                f_dict['createTime'] = current_time
                f_dict['updateTime'] = current_time
                local_folders.append(f_dict)
        updated_data = {'folders' : local_folders}
        
    with open('logged_folders.json', 'w') as out_file:
        json.dump(updated_data, out_file)
    
    return updated_data

def update_logged_documents(folder_id, user_account, publish_message, script_proj_title='IPProject Test'):
    '''
    Update Google Docs located in a Google Drive folder.
    
    Args:
        folder_id: id of Google Drive Folder
        user_account: gmail account making used to access Google Docs and Drive folder.
        publish_message: Message assigned to a script project when making a publish. 
        script_proj_title: Title of a script project. 
    '''   
    print('Updating logged documents for folder %s' % folder_id)
    creds = authenticate_credentials()
    drive_api = DriveAPI(creds)
    remote_documents = drive_api.get_documents_from_folder(folder_id)
    
    global DOCUMENT_SIZE
    DOCUMENT_SIZE = len(remote_documents)
    print('Located % d documents.' % DOCUMENT_SIZE)
    
    app_script_api = AppScriptAPI(creds) 
    with open(folder_id + '_log.json') as in_file:
        d_data = json.load(in_file)
        local_documents = d_data['documents']
        
        d = datetime.datetime.utcnow()
        current_time = d.isoformat("T") + "Z"
        
        for i in range(DOCUMENT_SIZE):
            r_doc = remote_documents[i]
            r_id = r_doc['id']
            
            if i == MAXIMUM_CREATE_QUOTA:
                INCOMPLETE_DOCS = remote_documents[i:]
                
            
            if _contain_document_id(r_id, local_documents):
                print('Updating script project metadata for document %s' % r_id)
                l_doc = _get_local_document(r_id, local_documents)
                l_doc['publishSucceed'] = False

                # get script id associated to document
                script_id = l_doc['scriptId']
                remote_metadata = app_script_api.get_project_metadata(script_id)
                
                # push Code.js and manifest
                app_script_api.update_project_metadata(script_id, remote_metadata)
                l_doc['updateTime'] = current_time
                
                # create version
                new_version = app_script_api.get_head_version(script_id) + 1
                app_script_api.create_version(script_id, new_version, publish_message)
                l_doc['scriptVersion'] = new_version
                l_doc['publishSucceed'] = True
            else:        
                print('Creating add-on script project for document %s.' % r_id)
                d_dict = {}
                d_dict['id'] = r_id
                d_dict['name'] = r_doc['name']
                d_dict['publishSucceeded'] = False
                
                # create an add-on script project
                response = app_script_api.create_project(script_proj_title, r_id)
                global NUMBER_OF_CREATION
                NUMBER_OF_CREATION = NUMBER_OF_CREATION + 1
                d_dict['createTime'] = current_time
                d_dict['updateTime'] = current_time
                script_id = response['scriptId']
                d_dict['scriptId'] = script_id
                
                # push code.js and manifest
                remote_metadata = app_script_api.get_project_metadata(script_id)
                app_script_api.set_project_metadata(script_id, remote_metadata, user_account)
                    
                # create version
                new_version = app_script_api.get_head_version(script_id) + 1
                app_script_api.create_version(script_id, new_version, publish_message)
                d_dict['scriptVersion'] = new_version
                
                d_dict['publishSucceed'] = True
                local_documents.append(d_dict)
        updated_data = {'documents' : local_documents}
    
    return updated_data

def perform_daily_run(folder_id, user_account, publish_message):
    try:
        folder_dict = update_logged_folders(folder_id)
        folder_list = folder_dict['folders']
        for i in range(len(folder_list)):
            folder_id = folder_list[i]['id']
            updated_data = update_logged_documents(folder_id, user_account, publish_message)
        print('Script completed!')
    except errors.HttpError as error:
        # The API encountered a problem.
        print(error.content) 
    finally:
        print('%d / %d scripts created' % (NUMBER_OF_CREATION, DOCUMENT_SIZE))     
        if len(INCOMPLETE_DOCS) > 0: 
            with open(folder_id + '_incomplete.json', 'w') as out_file:
                json.dump({'folder_id' : folder_id, 'incomplete' : INCOMPLETE_DOCS}, out_file)
    
    

def perform_initial_run(folder_id, user_account, publish_message):
    try:
        updated_data = update_logged_documents(folder_id, user_account, publish_message)
        with open(folder_id + '_log.json', 'w') as out_file:
            json.dump(updated_data, out_file)
        print('Script completed!')
    except errors.HttpError as error:
        # The API encountered a problem.
        print(error.content) 
    finally:
        print('%d / %d scripts created' % (NUMBER_OF_CREATION, DOCUMENT_SIZE))     
        if len(INCOMPLETE_DOCS) > 0: 
            with open(folder_id + '_incomplete.json', 'w') as out_file:
                json.dump({'folder_id' : folder_id, 'incomplete' : INCOMPLETE_DOCS}, out_file)
    
if __name__ == '__main__':
    publish_message = 'Test1 2.4 Release'
    user_account = {
            "domain": 'gmail.com',
            "email": 'tramy.nguy@gmail.com',
            "name": 'Tramy Nguyen'
      }
    folder_id = '1tvT29Y20-iXO20TCiCO_61TTv3NAkld9'
#     perform_daily_run(folder_id, user_account, publish_message)
    perform_initial_run(folder_id, user_account, publish_message)




