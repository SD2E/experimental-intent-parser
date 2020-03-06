from app_script_api import AppScriptAPI
from drive_api import DriveAPI
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
import os.path

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
    if not items:
        print('No files found.')
        return
    
    print('Files:')
    script_list = []
    app_script_api = AppScriptAPI(creds)
    for doc_id in list_of_doc:
        script_id = app_script_api.create_project('IPProject Test', doc_id)
        script_list.append(script_id)
        script_msg = u'{0} ({1})'.format(item['name'], item['id']) + '\n'
        print('Created script for: ' + script_msg)
        SCRIPT_IDS.append(script_msg)
    
    for script_id in script_list:
        update_script(app_script_api, script_id, save_message)
        
def update_script(app_script_api, script_proj_id, save_message):
    response = app_script_api.get_project_metadata(script_proj_id)
    app_script_api.update_project(script_proj_id, response)
    
    new_version = app_script_api.get_head_version() + 1
    app_script_api.create_version(script_proj_id, new_version, save_message)
    
    
    
if __name__ == '__main__':
    drive_id = '1693MJT1Up54_aDUp1s3mPH_DRw1_GS5G'
    publish_message = 'Test1 2.4 Release'
    publish_ip_add_on(drive_id, publish_message)