from synbiohub_adapter.query_synbiohub import SynBioHubQuery

def query_experiments(synbiohub, target_collection):
    '''
    Search the target collection and return references to all Experiment objects

    Parameters
    ----------
    synbiohub : SynBioHubQuery
        An instance of a SynBioHubQuery SPARQL wrapper from synbiohub_adapter
    target_collection : str
        A URI for a target collection
    '''

    # Correct the target collection URI in case the user specifies the wrong synbiohub namespace 
    # (a common mistake that can be hard to debug)
    if synbiohub.spoofed_url:
        if main_resource in target_collection:
            target_collection = target_collection.replace(main_resource, spoofed_resource)


    query = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX sbol: <http://sbols.org/v2#>
    PREFIX sd2: <http://sd2e.org#>
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    SELECT DISTINCT ?entity WHERE { 
            <%s> sbol:member ?entity .
            ?entity rdf:type sbol:Experiment .
    }
    """ %(target_collection)
    response = synbiohub.fetch_SPARQL('', query)
    experiments = [ m['entity']['value'] for m in response['results']['bindings']]
    return experiments

def query_experiment_source(synbiohub, experiment_uri):
    '''
    Return a reference to a samples.json file on Agave file system that generated the Experiment

    Parameters
    ----------
    synbiohub : SynBioHubQuery
        An instance of a SynBioHubQuery SPARQL wrapper from synbiohub_adapter
    experiment_uri : str
        A URI for an Experiment object
    '''
    
    query = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX sbol: <http://sbols.org/v2#>
    PREFIX sd2: <http://sd2e.org#>
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    SELECT DISTINCT ?source WHERE {
            <%s> prov:wasDerivedFrom ?source .
    }
    """ %(experiment_uri)
    response = synbiohub.fetch_SPARQL('', query)
    source = [ m['source']['value'] for m in response['results']['bindings']]
    return source

def query_experiment_request(synbiohub, experiment_uri):
    '''
    Return a URL to the experiment request form on Google Docs that initiated the Experiment

    Parameters
    ----------
    synbiohub : SynBioHubQuery
        An instance of a SynBioHubQuery SPARQL wrapper from synbiohub_adapter
    experiment_uri : str
        A URI for an Experiment object
    '''

    query = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX sbol: <http://sbols.org/v2#>
    PREFIX sd2: <http://sd2e.org#>
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    SELECT DISTINCT ?request_url WHERE {
            <%s> sd2:experimentReferenceURL ?request_url .
    }
    """ %(experiment_uri)
    response = synbiohub.fetch_SPARQL('', query)
    request_url = [ m['request_url']['value'] for m in response['results']['bindings']]
    if request_url:
        return request_url[0]
    else:
        return "NOT FOUND"

# Initialize SD2 specific parameters
user = 'sd2e'
password = 'jWJ1yztJl2f7RaePHMtXmxBBHwNt'
staging_instance = 'https://hub-staging.sd2e.org'
production_instance = 'https://hub.sd2e.org'
target_collection = 'https://hub-staging.sd2e.org/user/sd2e/experiment_test/experiment_test_collection/1'
#target_collection = 'https://hub-staging.sd2e.org/user/sd2e/foo/foo_collection/1'

# Initialize the query wrapper to query the staging instance of synbiohub
main_resource = staging_instance
spoofed_resource = production_instance
synbiohub  = SynBioHubQuery(main_resource + '/sparql', spoofed_url=spoofed_resource) 
synbiohub.login(user, password)

# Perform queries
experiments = query_experiments(synbiohub, target_collection)
for x in experiments:
    source = query_experiment_source(synbiohub, x)  # Get the reference to the source document with lab data
    request_doc = query_experiment_request(synbiohub, x)  # Get the reference to the Google request doc
    print('Experiment: ' + x)
    print('Request: ' + request_doc)
    print()
