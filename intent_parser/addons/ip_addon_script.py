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
from googleapiclient import errors
from intent_parser.accessor.google_accessor import GoogleAccessor
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.utils.intent_parser_utils as util
import json
import logging.config
import os.path
import time
import traceback


USER_ACCOUNT = {
            "domain": 'gmail.com',
            "email": 'bbn.intentparser@gmail.com',
            "name": 'bbn intentparser'}

CURR_PATH = os.path.dirname(os.path.realpath(__file__))
ADDON_FILE = os.path.join(CURR_PATH, 'addon_file.json')
INTENT_PARSER_ADDON_CODE_FILE = os.path.join(CURR_PATH, 'Code.js')
INTENT_PARSER_MANIFEST_FILE = os.path.join(CURR_PATH, 'appsscript.json')

logger = logging.getLogger('ip_addon_script')

def setup_logging(
    default_path='logging.json',
    default_level=logging.INFO,
    env_key='LOG_CFG'):
    """
    Setup logging configuration
    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'r') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level, format="[%(levelname)-8s] %(asctime)-24s %(filename)-23s line:%(lineno)-4s  %(message)s")
    
    hdlr = logging.FileHandler('ip_addon_script.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr) 
    
    logger.setLevel(logging.INFO)
   
    logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.CRITICAL)
    logging.getLogger("googleapiclient.discovery").setLevel(logging.CRITICAL)


def perform_automatic_run(current_release, drive_id='1FYOFBaUDIS-lBn0fr76pFFLBbMeD25b3'):
    drive_access = GoogleAccessor().get_google_drive_accessor(version=3)
    app_script_access = GoogleAccessor().get_google_app_script_accessor()
    
    local_docs = util.load_json_file(ADDON_FILE)
    remote_docs = drive_access.get_all_docs(drive_id)
    while len(remote_docs) > 0:
        doc = remote_docs.pop(0)
        r_id = doc
        logger.info('Processing doc: ' + r_id)
        if r_id in local_docs:
            try:
                metadata = local_docs[r_id]
                if metadata['releaseVersion'] != current_release:
                    logger.info('Updating script project metadata for doc: %s' % r_id)
                    script_id = metadata['scriptId']
                    
                    remote_metadata = app_script_access.get_project_metadata(script_id)
                    app_script_access.update_project_metadata(script_id,
                                                              remote_metadata,
                                                              INTENT_PARSER_ADDON_CODE_FILE,
                                                              INTENT_PARSER_MANIFEST_FILE)
                    
                    new_version = app_script_access.get_head_version(script_id) + 1
                    publish_message = current_release + ' Release'
                    app_script_access.create_version(script_id, new_version, publish_message)
                    
                    local_docs[r_id] = {'scriptId' : script_id, 'releaseVersion' : current_release}
                    util.write_json_to_file(local_docs, ADDON_FILE)
            except errors.HttpError:
                logger.info('Reached update quota limit!')
                remote_docs.append(doc)
                time.sleep(60) 
        else:
            try:
                logger.info('Creating add-on for doc: %s' % r_id)
                script_proj_title = 'IPProject Release'
                response = app_script_access.create_project(script_proj_title, r_id)
                script_id = response['scriptId']
                
                remote_metadata = app_script_access.get_project_metadata(script_id)
                app_script_access.set_project_metadata(script_id, remote_metadata, USER_ACCOUNT, INTENT_PARSER_ADDON_CODE_FILE, INTENT_PARSER_MANIFEST_FILE, 'Code')
                
                local_docs[r_id] = {'scriptId': script_id, 'releaseVersion': current_release}
                util.write_json_to_file(local_docs, ADDON_FILE)
            except errors.HttpError:
                logger.info('Reached create quota limit!')
                remote_docs.append(doc)
                time.sleep(60)  

def main():
    current_release = ip_constants.RELEASE_VERSION
    setup_logging()
    logger.info('Running IP addon script for release %s' % current_release)
    try:
        while True:
            perform_automatic_run(current_release)
            logger.info('Run completed! Scheduling next run.')  
            time.sleep(300)
    except (KeyboardInterrupt, SystemExit) as ex:
        logger.info('Script stopped!') 
        logger.info(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__))) 
        
        
if __name__ == '__main__':
    main()
 


