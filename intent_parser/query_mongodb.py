import pymongo

dbURI = "mongodb://readonly:WNCPXXd8ccpjs73zxyBV@catalog.sd2e.org:27020/admin?readPreference=primary"
client = pymongo.MongoClient(dbURI)
science_view = client.catalog_staging.science_view
files = client.catalog_staging.files

request_docs = {
    'Novel Chassis and Yeast States: The Automated Time Series Experimental Request':  '10HqgtfVCtYhk3kxIvQcwljIUonSNlSiLBC8UFmlwm1s',
    'Novel Chassis NAND2.0 Omics Experimental Request':                                '1g0SjxU2Y5aOhUbM63r8lqV50vnwzFDpJg4eLXNllut4',
    'NovelChassis_NAND2.0_Parts_Verification Experimental Request':                    '1K5IzBAIkXqJ7iPF4OZYJR7xgSts1PUtWWM2F0DKhct0',
    'Novel Chassis:Bacillus Subtilis WT Characterization Experimental Request':        '1uXqsmRLeVYkYJHqgdaecmN_sQZ2Tj4Ck1SZKcp55yEQ',
    'Novel Chassis NAND2.0 Titration Experimental Request':                            '1QX6e7BjK6VlCa7pDWhIE8oL2vhSYvqwoSjTrP-SNsOM'
}

def query_source_files(google_doc_id):
    '''
    Get Agave URIs for samples.json files that correspond to the provided Google request document ID
    '''
    
    google_doc_id = "https://docs.google.com/document/d/" + google_doc_id
    uri_query = { "experiment_design.uri" : google_doc_id }
    uri_matches = science_view.find(uri_query)

    source_files = set()
    for uri_match in uri_matches: 
        if not "derived_from" in uri_match["experiment"].keys():
            continue
        experiment_file_uuid = uri_match["experiment"]["derived_from"][0]
        metadata_json_query = { "uuid" : experiment_file_uuid }
        metadata_json = files.find_one(metadata_json_query)
        source_files.add(metadata_json['name'])
        #for m in metadata_json:
        #    print(m['name'])
    return source_files

for request_name, request_id in request_docs.items():
    source_files = query_source_files(request_id)
    for f in source_files:
        print(request_name, f)
