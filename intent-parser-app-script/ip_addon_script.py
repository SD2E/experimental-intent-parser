from app_script_api import AppScriptAPI
from drive_api import DriveAPI
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os.path
import time

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/script.projects',
          'https://www.googleapis.com/auth/script.deployments',
          'https://www.googleapis.com/auth/documents']
SCRIPT_IDS = []

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
    
def publish_ip_add_on(drive_id, publish_message):
    creds = authenticate_credentials()

    # Call the Drive v3 API
    drive_api = DriveAPI(creds)
    doc_list = drive_api.recursive_list_doc(drive_id)
    create_and_save_new_script(creds, doc_list, publish_message)
    
    # Save script id for making future updates to the script file
    file = open('script_id_mapping.txt', 'w')
    file.writelines(SCRIPT_IDS)
    file.close()


def create_and_save_new_script(creds, list_of_doc, save_message):
    '''
    Create and save the add-on script bounded to each Google Doc
    '''
    if not list_of_doc:
        print('No files found.')
        return
    
    print('Creating script for doc:')
    app_script_api = AppScriptAPI(creds)
    index = 1
    for doc_id in list_of_doc:
        print(str(index) + ' ' + doc_id)
        script_id = app_script_api.create_project('IPProject Test', doc_id)
        update_script(app_script_api, script_id, save_message)

        print('Updating script ' + script_id)
        update_script(app_script_api, script_id, save_message)
        
        SCRIPT_IDS.append(script_id)
        index += 1
    
        
def update_script(app_script_api, script_proj_id, save_message):
    response = app_script_api.get_project_metadata(script_proj_id)
    app_script_api.update_project(script_proj_id, response)
    
    new_version = app_script_api.get_head_version(script_proj_id) + 1
    app_script_api.create_version(script_proj_id, new_version, save_message)
    
def update_add_on(list_of_script, update_message):
    creds = authenticate_credentials()
    script_api = AppScriptAPI(creds)
    for script_id in list_of_script:
        update_script(script_api, script_id, update_message)
    
    print('Update completed for %s scripts' % len(list_of_script))   
    
    
if __name__ == '__main__':
#     drive_id = '1693MJT1Up54_aDUp1s3mPH_DRw1_GS5G'
#     drive_id = '0BxtlE8cJbmC2RmxqQWRGWVdBd00'
#     publish_message = 'Test1 2.4 Release'
#     publish_ip_add_on(drive_id, publish_message)

    script_id = '1B_x_vEazhsdjxEGpCIZgyMOJyG_gPbcM85dH3V5MpQJyYbgRsSCrOZlf'
    update_add_on([script_id], 'Test update request')




