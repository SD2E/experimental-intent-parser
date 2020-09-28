# Overview

The purpose of the intent parser is to aid in creating well described experimental plans.
The code base exists in two forms: one is a javascript-like language, Google Application Script (GAS), which creates a plugin for Google Docs.  
This plugin manifests itself as a "SD2 Intent Parser" menu item in the Add-Ons file menu of a document.  
From here, the user can access features such as:
- analyze the document, 
- looking for specific keywords and suggesting links  
- use a spellchecking dictionary to look for unknown words and possibly add them to the list of SynbioHub terms.
- validate and generate a structured request for running an experiment
  
The second part of the code base is a server written in Python that receives and process requests from the GAS code.  

## <a name="proj-install-block">Project Installation</a>:
1. Create a directory for your project and clone the [experimental-intent-parser](https://github.com/SD2E/experimental-intent-parser) using 

	`git clone https://github.com/SD2E/experimental-intent-parser.git`

2. Create a python virtual environment by running 

	`python3 -m venv intent-parser-env`

	In this command, `intent-parser-env` represents the name of your virtual environment.

3. Run `source bin/activate` to begin installing dependencies for the project
    - Install [python-datacatalog](https://gitlab.sd2e.org/sd2program/python-datacatalog) from source. 
        * Contact @mweston in order to access this repository and clone the project. When cloning, make sure to store it in your virtual environment.
        * The project that you have clone to your local machine should be set to the master branch. Switch your github branch for python-datacatalog to `2_2` before installing this project's dependencies. 
        * Run `pip3 install -r requirements.txt` on the [requirements.txt](https://gitlab.sd2e.org/sd2program/python-datacatalog/blob/master/requirements.txt). 
          Then, build python-datacatalog by running `python3 setup.py install`.
    - Install [synbiohub-adapter](https://github.com/SD2E/synbiohub_adapter) by running ```pip3 install git+https://github.com/SD2E/synbiohub_adapter.git@v1.2```. 
    - Install dependencies for experimental-intent-parser by running pip install on experimental-intent-parser's [requirements.txt](https://github.com/SD2E/experimental-intent-parser/blob/master/intent_parser/requirements.txt)
    ```pip3 install -r requirements.txt```
	- This completes dependency installation. Run ```deactivate``` to stop your virtual environment.

## <a name="proj-setup-block">Project Setup</a>:

#### <a name="pycharm-setup-block">PyCharm </a>:
1. Click on a **Open Project...** and select the github project for intent parser.
2. Go to PyCharm's **Preferences** to select a **Project Interpreter** 
    * Click on the radio button that says **Existing interpreter**
    * Set the interpreter value to point to your virtual environment’s python3.exe.  
5. Contact a developer to get remaining sensitive files to complete your project setup. 

## <a name="run-project-block">How to Run Project</a>:
The first time you run, python should open a web browser to log into Google.  
This will allow the Intent Parser Server to manipulate the Dictionary Spreadsheet, and to analyze documents.
After authentication, a file called "token.pickle" will be created.
The Google account that you log into must have permission to edit the Dictionary spreadsheet, as well as any Google documents the Intent Parser will be run on.

#### <a name="pycharm-run-block">PyCharm</a>:
- Set up a Python Run/Debug Configurations
- Provide a name for the configuration (i.e. run_ip_server)
- Set **Script path:** to point to `intent_parser_server.py`
- Contact a developer to get the necessary arguments for **Parameters**.

#### <a name="command-line-run-block">Command Line</a>:
- Run `python3 intent_parser_server.py -h ` to get a list of command line options that the Intent Parser server accepts. 


## <a name="proj-deploy-block">How to Deploy Project</a>:
This project is set up to build docker images for the server and for the Google App Script Addon.

1. Contact a developer to get access to intent parser's docker hub repository.  
2. Open up a command line and navigate to where the .Dockerfiles are located.
3. To build and push a docker image for the server:
    - Update `serverURL`(a variable) in [Code.js](https://github.com/SD2E/experimental-intent-parser/blob/master/intent_parser/addons/Code.js) to reflect the tool's version for release. 
    - Run the following dockerhub commands:
        
        ```
        docker build -f intent_parser.server.Dockerfile -t username/repo_name:tag_name_and_version .
        docker push username/repo_name:tag_name_and_version
        ```
4. To build and push a docker image for GAS, 
    - Update `current_release`(a variable) in [ip_addon_script.py](https://github.com/SD2E/experimental-intent-parser/blob/master/intent_parser/addons/ip_addon_script.py) to reflect the tool's version for release.
    - Update version in [setup.py](https://github.com/SD2E/experimental-intent-parser/blob/a0e3108888dfaa12e139dbb516a262dd63ddf271/intent_parser/setup.py#L5) to reflect the tool's version for release.
    - Run the following dockerhub commands:
    
        ```
        docker build -f intent_parser.addons.Dockerfile -t username/repo_name:tag_name_and_version .
        docker push username/repo_name:tag_name_and_version
        ```
   
5. The docker image is then deployed on a [portainer](https://admin.services-ec2-04.sd2e.org/#/auth) instance. 
    - Contact a @eriksf to access this website and the two containers that host intent parser server and the GAS script built for deployment.
    - Update these two containers to reflect the new docker hub images.
        * To do this, stop each container and click on a `Duplicate/Edit` button.
        * Modify the `Image` field to reflect your docker image tag release
        * Click `Start` and this concludes the deployment step.
   