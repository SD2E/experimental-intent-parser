"""
A script setup up to install and run Intent Parser as a Google Doc add-on.

This script uses Google's REST APIs to make calls to a Google Drive folder and Google App Script.
If there is a Resource Error when running this script, then the scopes set up to run this script has changed and a new token must be generated.
To do so, remove the token.pickle file in this directory and rerun this script again to regenerate a new token.

This script will need to get the scriptId assigned to each Google Doc in order to make updates to an add-on.
Currently, Google App Script API does not have a functionality to get a scriptId from a Google Doc so this script handles this by loading in a local json file that keeps track of scriptIds bounded to each Google Doc.
If a scriptId exist for a Google Doc, then the script will update the add-on with the appropriate metadata.
If no scriptId exist for a Google Doc, then a new script is created and recorded to the json file.
Note that Google's REST API has quotas that limits how many create and update methods a user can call per timeframe. 
If a quota limit is reached, then the script will store each document that needs to process to a queue and move onto the next Google Doc to process.
"""

from app_script_api import AppScriptAPI
from document_api import DocumentAPI
from drive_api import DriveAPI
from googleapiclient import errors
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json
import logging 
import os.path
import pickle
import script_util as util
import time

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/script.projects',
          'https://www.googleapis.com/auth/script.deployments',
          'https://www.googleapis.com/auth/documents',
          'https://www.googleapis.com/auth/drive.readonly']

USER_ACCOUNT = {
            "domain": 'gmail.com',
            "email": 'bbn.intentparser@gmail.com',
            "name": 'bbn intentparser'}

ADDON_FILE = 'addon_file'

logger = logging.getLogger('ip_addon_script')

def authenticate_credentials():
    """
    Authenticate credentials for script
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
            curr_path = os.path.dirname(os.path.realpath(__file__))
            credential_path = os.path.join(curr_path, 'credentials.json')
            flow = InstalledAppFlow.from_client_secrets_file(
                credential_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds    



def perform_automatic_run(current_release, drive_id='1FYOFBaUDIS-lBn0fr76pFFLBbMeD25b3'):
    creds = authenticate_credentials()
    drive_api = DriveAPI(creds)
    app_script_api = AppScriptAPI(creds) 
    publish_addon = False
    
    # load file
    local_docs = util.load_json_file(ADDON_FILE)
    remote_docs = drive_api.recursive_list_doc(drive_id)
    while len(remote_docs) > 0 :
        doc = remote_docs.pop(0)
        r_id = doc['id']
       
        if r_id in local_docs:
            try:
                metadata = local_docs[r_id]
                if metadata['releaseVersion'] != current_release:
                    logger.info('Updating script project metadata for doc: %s' % r_id)
                    script_id = metadata['scriptId']
                    
                    remote_metadata = app_script_api.get_project_metadata(script_id)
                    app_script_api.update_project_metadata(script_id, remote_metadata)
                    
                    new_version = app_script_api.get_head_version(script_id) + 1
                    app_script_api.create_version(script_id, new_version, publish_message)
                    
                    local_docs[r_id] = {'scriptId' : script_id, 'releaseVersion' : current_release}
                    util.write_to_json(local_docs, ADDON_FILE)
            except errors.HttpError as error:
                print('Reached update quota limit!')
                logger.info('Reached update quota limit!')
                remote_docs.append(doc)
                time.sleep(60) 
        else:
            try:
                print('Creating add-on for doc: %s' % r_id)
                logger.info('Creating add-on for doc: %s' % r_id)
                script_proj_title='IPProject Release'
                response = app_script_api.create_project(script_proj_title, r_id)
                script_id = response['scriptId']
                
                remote_metadata = app_script_api.get_project_metadata(script_id)
                app_script_api.set_project_metadata(script_id, remote_metadata, USER_ACCOUNT)
                
                local_docs[r_id] = {'scriptId' : script_id, 'releaseVersion' : current_release}
                util.write_to_json(local_docs, ADDON_FILE)
            except errors.HttpError as error:
                print('Reached create quota limit!')
                logger.info('Reached create quota limit!')
                remote_docs.append(doc)
                time.sleep(60)  

if __name__ == '__main__':

    current_release = '2.4'
    hdlr = logging.FileHandler('ip_addon_script.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr) 
    
    logger.setLevel(logging.INFO)
    logger.info('Running IP addon script for release %s' % current_release)
    print('Running IP addon script for release %s' % current_release)
    try:
        while True:
            perform_automatic_run(current_release)
            print('Run completed! Scheduling next run.')   
            logger.info('Run completed! Scheduling next run.')  
            time.sleep(300)
    except (KeyboardInterrupt, SystemExit) as err:
        logger.info('Script stopped!')  
 


