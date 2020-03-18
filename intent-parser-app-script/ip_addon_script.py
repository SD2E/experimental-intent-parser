"""
A script setup up to install and run Intent Parser as a Google Doc add-on.

This script uses Google's REST APIs to make calls to a Google Drive folder and Google App Script.
If there is a Resource Error when running this script, then the scopes set up to run this script has changed and a new token must be generated.
To do so, remove the token.pickle file in this directory and rerun this script again to regenerate a new token.

This script begins by collecting Google Drive folders that will be used to look for Google docs to set up intent parser as an add-on.
This task is accomplished by loading a logged_folder.json to use for tracking folder ids. 
This script will monitor any new folder that gets added to the Experiment Request Google Drive folder and update logged_folder.json accordingly.

The next step is to iterate over each Google Doc from a Google Drive folder and set up the intent parser add-on.
This script will need to get the scriptId assigned to each Google Doc in order to make updates to an add-on.
Currently, Google App Script API does not have a functionality to get a scriptId from a Google Doc so this script handles this by loading in local json files that keeps track of scriptIds bounded to each Google Doc.
If a scriptId exist for a Google Doc, then the script will update the add-on with the appropriate metadata.
To look for the file that a scriptId bounds to a Google Doc, look for the Google Drive's folder id that the Doc is stored as the file name appended with the _log.json
If no scriptId exist for a Google Doc, then a new script is created and recorded to the json file.
Note that Google's REST API limits how many create methods a user running this script can call per day. 
The maximum quota for calling create methods is stored in MAXIMUM_CREATE_QUOTA. 
If this quota has been reached for the day, then the script will throw a RESOURCE_EXHAUSTED error.
This error will resolve itself after 24 hours when the quota is reset for the day.  
"""

from app_script_api import AppScriptAPI
from document_api import DocumentAPI
from drive_api import DriveAPI
from googleapiclient import errors
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import argparse
import datetime
import json 
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
            "name": 'bbn intentparser'
      }

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
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds    

def update_logged_documents(folder_id, user_account, publish_addon, publish_message, script_proj_title='IPProject Release'):
    """
    Update Google Docs located in a Google Drive folder.
    
    Args:
        folder_id: id of Google Drive Folder
        user_account: gmail account making used to access Google Docs and Drive folder.
        publish_message: Message assigned to a script project when making a publish. 
        script_proj_title: Title of a script project. 
    """  
    print('Updating logged documents for folder %s' % folder_id)
    creds = authenticate_credentials()
    drive_api = DriveAPI(creds)
    remote_documents = drive_api.get_documents_from_folder(folder_id)
    
    global COMPLETE_DOCS
    global INCOMPLETE_DOCS
    global NUMBER_OF_UPDATES
    global MAXIMUM_UPDATE_QUOTA
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
            
            if (NUMBER_OF_UPDATES > 0) and (NUMBER_OF_UPDATES % MAXIMUM_UPDATE_QUOTA == 0):
                time.sleep(300)   
            
            if _contain_document_id(r_id, local_documents):
                print('Updating script project metadata for document %s' % r_id)
                if publish_addon:
                    l_doc = _get_local_document(r_id, local_documents)
                    l_doc['publishSucceeded'] = False
 
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
                    l_doc['publishSucceeded'] = True
               
                    NUMBER_OF_UPDATES = NUMBER_OF_UPDATES + 1
            if not _contain_document_id(r_id, local_documents):        
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
                
                d_dict['publishSucceeded'] = True
                local_documents.append(d_dict)
                COMPLETE_DOCS.append(d_dict)
        updated_data = local_documents
        
    return updated_data



def perform_automatic_run(current_release, drive_id='1FYOFBaUDIS-lBn0fr76pFFLBbMeD25b3'):
    creds = authenticate_credentials()
    drive_api = DriveAPI(creds)
    app_script_api = AppScriptAPI(creds) 
    publish_addon = False
    
    # load file
    local_docs = util.load_json_file('temp_script')
    remote_docs = drive_api.recursive_list_doc(drive_id)
    
    while len(remote_docs) > 0 :
        doc = remote_docs.pop(0)
        r_id = doc['id']
        # create or update add-on script
        # check if local doc contains remote, then update local doc
        if r_id in local_docs:
            print('Updating script project metadata for document %s' % r_id)
            try:
                metadata = local_docs[r_id]
                if metadata['releaseVersion'] != current_release:
                    script_id = metadata['scriptId']
                    
                    remote_metadata = app_script_api.get_project_metadata(script_id)
                    app_script_api.update_project_metadata(script_id, remote_metadata)
                    
                    new_version = app_script_api.get_head_version(script_id) + 1
                    app_script_api.create_version(script_id, new_version, publish_message)
                    
                    local_docs[r_id] = {'scriptId' : script_id, 'releaseVersion' : current_release}
                    util.write_to_json(local_docs, 'temp_script')
            except errors.HttpError as error:
                print('Reached update quota limit!')
                remote_docs.append(doc)
        else:
            try:
                print('Creating add-on for doc %s' % r_id)
                script_proj_title='IPProject Release'
                response = app_script_api.create_project(script_proj_title, r_id)
                script_id = response['scriptId']
                
                remote_metadata = app_script_api.get_project_metadata(script_id)
                app_script_api.set_project_metadata(script_id, remote_metadata, USER_ACCOUNT)
                
                local_docs[r_id] = {'scriptId' : script_id, 'releaseVersion' : current_release}
                util.write_to_json(local_docs, 'temp_script')
            except errors.HttpError as error:
                print('Reached create quota limit!')
                remote_docs.append(doc) 
    print('script stopped!')       

if __name__ == '__main__':

    current_release = '2.4'
    perform_automatic_run(current_release)
 


