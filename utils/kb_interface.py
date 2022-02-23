
from SPARQLWrapper import SPARQLWrapper, JSON

def KB_query(_query, kb_endpoint):
    sparql = SPARQLWrapper(kb_endpoint)
    sparql.setQuery(_query)
    sparql.setReturnFormat(JSON)
    # sparql.setTimeout(5)
    response = sparql.query().convert()
    return response