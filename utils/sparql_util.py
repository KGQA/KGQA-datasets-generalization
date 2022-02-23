
import re
import os
from utils import big_bracket_pattern, angle_bracket_pattern
from rdflib.plugins.sparql import parser
from collections import deque
from rdflib.plugins.sparql.parserutils import CompValue
from rdflib.plugins.sparql.algebra import translateQuery



def get_functions_from_sparql(sparql):
    functions = []
    # count function
    count_pattern = re.compile("(?:COUNT|count)")
    count_strings = count_pattern.findall(sparql)
    if count_strings and len(count_strings) > 0:
        functions.append("count")
    # comparative functions
    lt_pattern = re.compile("\ <\ ")
    lt_strings = lt_pattern.findall(sparql)
    if lt_strings and len(lt_strings) > 0:
        lt_strings = [lt.strip() for lt in lt_strings if lt.strip() == "<"]
        functions.extend(lt_strings)
    lq_pattern = re.compile("\ <=\ ")
    lq_strings = lq_pattern.findall(sparql)
    if lq_strings and len(lq_strings) > 0:
        lq_strings = [lq.strip() for lq in lq_strings if lq.strip() == "<="]
        functions.extend(lq_strings)
    gt_pattern = re.compile("\ >\ ")
    gt_strings = gt_pattern.findall(sparql)
    if gt_strings and len(gt_strings) > 0:
        gt_strings = [gt.strip() for gt in gt_strings if gt.strip() == ">"]
        functions.extend(gt_strings)
    ge_pattern = re.compile("\ >=\ ")
    ge_strings = ge_pattern.findall(sparql)
    if ge_strings and len(ge_strings) > 0:
        ge_strings = [ge.strip() for ge in ge_strings if ge.strip() == ">="]
        functions.extend(ge_strings)
    neq_pattern = re.compile("\ !=\ ")
    neq_strings = neq_pattern.findall(sparql)
    if neq_strings and len(neq_strings) > 0:
        neq_strings = [neq.strip() for neq in neq_strings if neq.strip() == "!="]
        functions.extend(neq_strings)

    if len(functions) == 0:
        functions.append("none")
    return functions


def get_triples_grailqa(query, pattern=None):
    return _filter_extracted_triples(extract_triples(query), pattern=pattern)


def get_triples_graphquestions(query, pattern=None):
    return _filter_extracted_triples(extract_triples(query), pattern=pattern)


def get_triples_cwq(query, pattern=None):
    prefixes = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
        PREFIX wd: <http://www.wikidata.org/entity/> 
        PREFIX wdt: <http://www.wikidata.org/prop/direct/> 
    """
    query = prefixes + query
    # replace COUNT() with COUNT () to avoid parsing error
    pattern_1 = re.compile("(?:COUNT|count)\(\?[a-zA-Z0-9]+\)")
    count_strings = pattern_1.findall(query)
    if count_strings and len(count_strings) != 0:
        for count_string in count_strings:
            pattern_2 = re.compile("\?[a-zA-Z0-9]+")
            variable = pattern_2.findall(count_string)[0]
            query = query.replace(count_string, variable)
    return _filter_extracted_triples(extract_triples(query), pattern=pattern)


def add_missing_angle_brackets_lcquad2(query):
    where_clause = re.search(big_bracket_pattern, query).group(0)
    where_clause = where_clause.strip("{").strip("}")
    where_clause = where_clause.strip(" ")
    uris = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', where_clause)
    for uri in uris:
        start_pos = query.find(uri)
        s_pre = query[start_pos - 1]
        if s_pre != "<":
            query = query.replace(uri, "<" + uri + ">")
    return query


def formalize_for_lcquad2(sparql):
    prefixes = ["<http://dbpedia.org/resource/", "<http://dbpedia.org/property/",
                "<http://dbpedia.org/ontology/", "<http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "<http://www.wikidata.org/entity/", "<http://wikidata.dbpedia.org/resource/",
                ">"]
    prefixes_2 = ["http://dbpedia.org/resource/", "http://dbpedia.org/property/",
                "http://dbpedia.org/ontology/", "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "http://www.wikidata.org/entity/", "http://wikidata.dbpedia.org/resource/"]
    where_clause = re.search(big_bracket_pattern, sparql).group(0)
    left, right = sparql.replace(where_clause, "###").split("###")
    where_clause = where_clause.strip("{").strip("}")
    where_clause = where_clause.strip(" ")

    uris_1 = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', where_clause)
    uris_2 = re.findall(angle_bracket_pattern, where_clause)
    uris = list(set(uris_1+uris_2))
    id2links = dict()
    errors = []

    for uri in uris:
        if "http" in uri:
            if "http://www.w3.org/1999/02/22-rdf-syntax-ns#" not in uri:
                link, id = os.path.split(uri)
            else:
                link, id = uri.split("#")
            if id not in id2links:
                id2links[id] = link
        else:
            errors.append(uri)

    for p in prefixes:
        where_clause = where_clause.replace(p, "")
    for p in prefixes_2:
        where_clause = where_clause.replace(p, "")

    for err in errors:
        where_clause = where_clause.replace("<", "\"").replace(err, err + "\"")

    triples = [x.strip(" ") for x in where_clause.split(".")]
    new_where_clause = " . ".join([triple for triple in triples])
    for id, link in id2links.items():
        if id in ["subject", "predicate", "object"]:
            new_where_clause = new_where_clause.replace(id, "<" + link + "#" + id + ">")
        else:
            new_where_clause = new_where_clause.replace(id, "<" + link + "/" + id + ">")

    new_query = left + "{ " + new_where_clause + " }" + right
    return new_query


def get_triples_lcquad2(query, kb, pattern=None):

    if kb == "wikidata":
        prefixes = """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
            PREFIX wd: <http://www.wikidata.org/entity/> 
            PREFIX wdt: <http://www.wikidata.org/prop/direct/> 
            PREFIX p: <http://www.wikidata.org/prop/direct/> 
            PREFIX ps: <http://www.wikidata.org/prop/direct/> 
            PREFIX pq: <http://www.wikidata.org/prop/direct/>
        """

        query = prefixes + query

        # ASK WHERE { wd:Q3591475 wdt:P2630 ?obj FILTER (?obj = t1270953452) }
        # error occurs when parsing the above query as t1270953452 is not the correct keyword
        pattern_1 = re.compile("t[0-9]+")
        matches = pattern_1.findall(query)
        if len(matches) != 0:
            for match in matches: query=query.replace(match, "'{}'".format(match))

    # replace COUNT() with COUNT () to avoid parsing error
    pattern_2 = re.compile("(?:COUNT\(|count\()")
    count_strings = pattern_2.findall(query)
    if count_strings and len(count_strings) != 0:
        for count_string in count_strings:
            query = query.replace(count_string, count_string[:-1] + " (")

    # # remove FILTER() with FILTER () to avoid parsing error
    pattern_3 = re.compile("(?:FILTER\(|filter\()")
    filter_strings = pattern_3.findall(query)
    if filter_strings and len(filter_strings) != 0:
        for filter_string in filter_strings:
            query = query.replace(filter_string, filter_string[:-1]+" (")
    return _filter_extracted_triples(extract_triples(query), pattern=pattern)


def get_triples_lcquad(query, pattern=None):
    # replace COUNT() with COUNT () to avoid parsing error
    pattern_1 = re.compile("(?:COUNT|count)\(\?[a-zA-Z0-9]+\)")
    count_strings = pattern_1.findall(query)
    if count_strings and len(count_strings) != 0:
        for count_string in count_strings:
            pattern_2 = re.compile("\?[a-zA-Z0-9]+")
            variable = pattern_2.findall(count_string)[0]
            query = query.replace(count_string, variable)
    return _filter_extracted_triples(extract_triples(query), pattern=pattern)


def get_triples_complexwebquestions(query, pattern=None):
    # # replace OR with || to avoid parsing error
    query = re.sub("\ OR\ ", " || ", query)
    return _filter_extracted_triples(extract_triples(query), pattern=pattern)


def get_triples_qald(query, pattern=None):

    # due to the missing of necessary namespace in the sparql, the parsing error would occur.
    prefixes = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dbp: <http://dbpedia.org/property/>
        PREFIX dbo: <http://dbpedia.org/ontology/> 
        PREFIX res: <http://dbpedia.org/resource/> 
        PREFIX dbr: <http://dbpedia.org/resource/>
        PREFIX yago: <http://dbpedia.org/class/yago/> 
        PREFIX dct: <http://purl.org/dc/terms/> 
        PREFIX dbc: <http://dbpedia.org/resource/Category:> 
    """

    query = prefixes + query

    # when parsing the sparql, sometimes some errors caused by the COUNT would occur,
    # so for convenience, simply remove the sub string between SELECT and WHERE, and
    # replace it with a random variable ?uri
    if query.find("SELECT") != -1 and query.find("WHERE") != -1:
        middle = query[query.find("SELECT")+6:query.find("WHERE")]
        if middle != '':
            query = query.replace(middle, " ?uri ")
    return _filter_extracted_triples(extract_triples(query), pattern=pattern)


def extract_triples(query):
    parsed_query = parser.parseQuery(query)
    translated_query = translateQuery(parsed_query)

    queue = deque([])
    triples = []

    p = translated_query.algebra
    queue.append(p)
    while len(queue) != 0:
        p = queue.popleft()
        if "triples" in p:
            triples.extend(p["triples"])
        else:
            for k in p.keys():
                if isinstance(p[k], CompValue):
                    queue.append(p[k])
    return triples


def _filter_extracted_triples(triples, pattern=None):
    if not pattern: return triples
    result = []
    for triple in triples:
        subj, pred, obj = triple
        triple_string = " ".join([subj.toPython(), pred.toPython(), obj.toPython()])
        if pattern not in triple_string:
            result.append(triple)
    return result


if __name__ == '__main__':
    # query_1 = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX wd: <http://www.wikidata.org/entity/> PREFIX wdt: <http://www.wikidata.org/prop/direct/> ASK WHERE { wd:Q2270 wdt:P2300 ?obj filter(?obj = 170000) } "
    # query_1 = "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX : <http://rdf.freebase.com/ns/> \nSELECT (?x0 AS ?value) WHERE {\nSELECT DISTINCT ?x0  WHERE { \n?x0 :type.object.type :medicine.routed_drug . \nVALUES ?x1 { :m.0hqs1x_ } \n?x0 :medicine.routed_drug.marketed_formulations ?x1 . \nFILTER ( ?x0 != ?x1  )\n}\n}"
    # query_1 = "SELECT DISTINCT ?uri WHERE {?uri <http://dbpedia.org/ontology/director> <http://dbpedia.org/resource/Stanley_Kubrick>  . }"
    # query_1 = "PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT ?x\nWHERE {\nFILTER (?x != ?c)\nFILTER (!isLiteral(?x) OR lang(?x) = '' OR langMatches(lang(?x), 'en'))\n?c ns:education.educational_institution.sports_teams ns:m.03d0l76 . \n?c ns:organization.organization.headquarters ?y .\n?y ns:location.mailing_address.state_province_region ?x .\n}\n"
    # query_1 = re.sub("\ OR\ ", " || ", query_1)
    query_1 = "SELECT ?answer WHERE { ?statement1 <http://www.w3.org/1999/02/22-rdf-syntax-ns#subject> <http://wikidata.dbpedia.org/resource/Q449506> . ?statement1 <http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate> <http://www.wikidata.org/entity/P1582>. ?statement1 <http://www.w3.org/1999/02/22-rdf-syntax-ns#object> ?answer . ?statement2 <http://www.w3.org/1999/02/22-rdf-syntax-ns#subject> ?answer. ?statement2 <http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate> <http://www.wikidata.org/entity/P1843> . ?statement2 <http://www.w3.org/1999/02/22-rdf-syntax-ns#object> Domestic Goat . }"
    # query_1 = "select distinct ?answer where { ?statement <http://www.w3.org/1999/02/22-rdf-syntax-ns#subject> <http://wikidata.dbpedia.org/resource/Q37319> . ?statement <http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate> <http://www.wikidata.org/entity/P706> . ?statement <http://www.w3.org/1999/02/22-rdf-syntax-ns#object> ?answer. }"
    # query_1 = " ASK { ?statement1 <http://www.w3.org/1999/02/22-rdf-syntax-ns#subject> <http://wikidata.dbpedia.org/resource/Q39809> . ?statement1 <http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate> <http://www.wikidata.org/entity/P1269> . ?statement1 <http://www.w3.org/1999/02/22-rdf-syntax-ns#object> <http://wikidata.dbpedia.org/resource/Q1066689>. ?statement2 <http://www.w3.org/1999/02/22-rdf-syntax-ns#subject> <http://wikidata.dbpedia.org/resource/Q39809> . ?statement2 <http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate> <http://www.wikidata.org/entity/P1269> . ?statement2 <http://www.w3.org/1999/02/22-rdf-syntax-ns#object> <http://wikidata.dbpedia.org/resource/Q207822>. } "
    triples = extract_triples(query_1)
    filtered_triples = _filter_extracted_triples(triples)
    print(triples)
