import Levenshtein

from collections import namedtuple as _namedtuple

from difflib import Match

IPSMatch = _namedtuple('Match', 'a b size content_word_length')

def analyze_term(entry):
    term = entry[0]
    start_offset = entry[1]
    paragraphs = entry[2]
    partial_match_min_size = entry[3]
    partial_match_thresh = entry[4]
    uri = entry[5]
    results = find_text(term, start_offset, paragraphs, partial_match_min_size, partial_match_thresh)
    search_results = []
    for result in results:
        search_results.append(
                        { 'paragraph_index' : result[0],
                          'offset'          : result[1],
                          'end_offset'      : result[2],
                          'term'            : term,
                          'uri'             : uri,
                          'link'            : result[3],
                          'text'            : result[4]})
    return search_results

def find_text(text, abs_start_offset, paragraphs, partial_match_min_size, partial_match_thresh):
    """
    Search through the whole document and return a collection of matches, including partial, to the search term.
    """
    results = []
    for paragraph_index in range( len(paragraphs )):
        paragraph = paragraphs[ paragraph_index ]
        elements = paragraph['elements']

        for element_index in range( len(elements) ):
            element = elements[ element_index ]

            if 'textRun' not in element:
                continue
            text_run = element['textRun']

            # Don't start the search until after the starting position
            end_index = element['endIndex']
            if end_index < abs_start_offset:
                continue

            start_index = element['startIndex']
            content = text_run['content']

            # Trim off content if it starts after the starting position
            start_offset = max(0,abs_start_offset - start_index)
            if start_offset > 0:
                content = content[start_offset:]

            matches = find_common_substrings(content.lower(), text.lower(), partial_match_min_size, partial_match_thresh)
            for match in matches:
                # Need to exceed partial match threshold - content word length
                if match.size < int(match.content_word_length * partial_match_thresh):
                    continue

                # Need to exceed partial match threshold - dictionary term length
                if match.size < int(len(text) * partial_match_thresh):
                    continue

                offset = match.a

                # Require whitespace before found text
                if offset > 0 and content[offset-1].isalpha():
                    continue

                # Require whitespace after found text
                next_offset = offset + match.size
                if next_offset < len(content) and content[next_offset].isalpha():
                    continue

                content_text = content[offset:(offset + match.size)]

                first_index = elements[0]['startIndex']
                offset += (start_index + start_offset) - first_index

                link = None

                if 'textStyle' in text_run:
                    text_style = text_run['textStyle']
                    if 'link' in text_style:
                        link = text_style['link']
                        if 'url' in link:
                            link = link['url']

                # If the text is linked, we must have an exact match, otherwise ignore
                if link is not None and (not match.size == len(content) or not match.size == len(text)):
                    continue

                results.append((paragraph_index, offset, offset + match.size - 1, link, content_text))
    return results

def find_common_substrings(content, dict_term, partial_match_min_size, partial_match_thresh):
    """
    Scan dict_term finding any common substrings from dict_term.  For each possible common substring, only the first one is found.
    """
    results = []
    len_content = len(content)
    len_term = len(dict_term)
    i = 0
    while i < len_content:
        match_start = -1
        matched_chars = 0
        # Ignore white space
        if content[i].isspace():
            i += 1
            continue;
        match = None
        for j in range(len_term):
            char_match = (i + matched_chars < len_content and content[i + matched_chars] == dict_term[j])
            if char_match and match_start == -1:
                match_start = j
            elif match_start > -1 and not char_match:
                match = Match(i, match_start, j - match_start)
                break
            if char_match:
                matched_chars += 1
        # Check for match at the end
        if match is None and match_start > -1:
            match = Match(i, match_start, len_term - match_start)
        # Process content match
        if not match is None:
            # Ignore matches if they aren't big enough
            # No partial matches for small terms
            if len_term <= partial_match_min_size:
                if match.size >= len_term:
                    results.append(match)
            # If the term is larger, we can have content partial match
            elif match.size >= int(len_term * partial_match_thresh):
                results.append(match)
            i += match.size
        else:
            i += 1

    # Compute word length for matched substrings
    # The word is terminated by whitespace, or /, unless the character in question is also present in the dictionary term at the same location
    results_mod = []
    for res in results:
        start_idx = res.a
        start_idx_b = res.b
        while (start_idx > 0 and (content[start_idx - 1].isalpha() or content[start_idx - 1] == '_')) or (start_idx > 0 and start_idx_b > 0 and content[start_idx - 1] == dict_term[start_idx_b - 1]):
            start_idx -= 1
            start_idx_b -= 1
        end_idx = res.a
        end_idx_b = res.b
        while (end_idx < len_content and (content[end_idx].isalpha() or content[end_idx] == '_')) or (end_idx < len_content and end_idx_b < len_term and content[end_idx] == dict_term[end_idx_b]):
            end_idx += 1
            end_idx_b += 1
        content_word_length = end_idx - start_idx
        results_mod.append(IPSMatch(res.a, res.b, res.size, content_word_length))
    return results_mod


def find_overlaps(start_idx, search_results, ignore_idx = set()):
        """
        Given a start index, find any entries in the results that overlap with the result at the start index
        In the case where the amount of overlap is equal, we pick the one that has the lowest Levenshtein (edit) distance between the matched text and the dictionary term.
        """
        query = search_results[start_idx]
        overlaps = [query]
        overlap_idx = [start_idx]
        best_overlap_idx = start_idx
        best_overlap_len = query['end_offset'] - query['offset']
        best_edit_dist = Levenshtein.distance(query['term'], query['text'])
        for idx in range(start_idx + 1, len(search_results)):

            if idx in ignore_idx:
                continue;
            comp = search_results[idx]

            if not comp['paragraph_index'] == query['paragraph_index']:
                continue
            overlap = max(0, min(comp['end_offset'], query['end_offset']) - max(comp['offset'], query['offset'])) > 0
            if overlap:
                overlaps.append(comp)
                overlap_idx.append(idx)
                dist = Levenshtein.distance(comp['term'], comp['text'])
                overlap_amount = comp['end_offset'] - comp['offset']
                if overlap_amount >= best_overlap_len or (overlap_amount == best_overlap_len and dist < best_edit_dist):
                    best_overlap_idx = idx
                    best_overlap_len = dist

        return overlaps, best_overlap_idx, overlap_idx

def query_experiments(synbiohub, target_collection, sbh_spoofing_prefix, sbh_url):
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
    if sbh_spoofing_prefix is not None:
        target_collection = target_collection.replace(sbh_url, sbh_spoofing_prefix)

    query = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX sbol: <http://sbols.org/v2#>
    PREFIX sd2: <http://sd2e.org#>
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    SELECT DISTINCT ?entity ?timestamp ?title WHERE {
            <%s> sbol:member ?entity .
            ?entity rdf:type sbol:Experiment .
            ?entity dcterms:created ?timestamp .
            ?entity dcterms:title ?title
    }
    """ %(target_collection)
    response = synbiohub.sparqlQuery(query)

    experiments = []
    for m in response['results']['bindings']:
        uri = m['entity']['value']
        timestamp = m['timestamp']['value']
        title = m['title']['value']
        if sbh_spoofing_prefix is not None: # We need to re-spoof the URL
            uri = uri.replace(sbh_spoofing_prefix, sbh_url)
        experiments.append({'uri': uri, 'timestamp': timestamp, 'title' : title})
    #experiments = [ {'uri' : m['entity']['value'], 'timestamp' : m['timestamp']['value'] }  for m in response['results']['bindings']]
    return experiments

def query_experiment_source(synbiohub, experiment_uri, sbh_spoofing_prefix, sbh_url):
    '''
    Return a reference to a samples.json file on Agave file system that generated the Experiment

    Parameters
    ----------
    synbiohub : SynBioHubQuery
        An instance of a SynBioHubQuery SPARQL wrapper from synbiohub_adapter
    experiment_uri : str
        A URI for an Experiment object
    '''

    # Correct the experiment_uri in case the user specifies the wrong synbiohub namespace
    # (a common mistake that can be hard to debug)
    if sbh_spoofing_prefix is not None:
        experiment_uri = experiment_uri.replace(sbh_url, sbh_spoofing_prefix)

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
    response = synbiohub.sparqlQuery(query)
    source = [ m['source']['value'] for m in response['results']['bindings']]
    return source

def query_experiment_request(synbiohub, experiment_uri, sbh_spoofing_prefix, sbh_url):
    '''
    Return a URL to the experiment request form on Google Docs that initiated the Experiment

    Parameters
    ----------
    synbiohub : SynBioHubQuery
        An instance of a SynBioHubQuery SPARQL wrapper from synbiohub_adapter
    experiment_uri : str
        A URI for an Experiment object
    '''

    # Correct the experiment_uri in case the user specifies the wrong synbiohub namespace
    # (a common mistake that can be hard to debug)
    if sbh_spoofing_prefix is not None:
        experiment_uri = experiment_uri.replace(sbh_url, sbh_spoofing_prefix)

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
    response = synbiohub.sparqlQuery(query)
    request_url = [ m['request_url']['value'] for m in response['results']['bindings']]
    if request_url:
        return request_url[0]
    else:
        return "NOT FOUND"
