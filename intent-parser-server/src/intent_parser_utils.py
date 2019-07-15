from difflib import Match

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
                # Need to exceed partial match threshold
                if match.size < int(len(text) * partial_match_thresh):
                    continue

                offset = match.a

                # Check for whitespace before found text
                if offset > 0 and content[offset-1].isalpha():
                    continue

                # Check for whitespace after found text
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

    return results
