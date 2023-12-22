import requests
from rdflib import Graph

# GET Logistics object and return as graph - will include auth in the future
def get_logistics_object_as_graph(lo_iri):

    logistics_object = requests.get(lo_iri)

    lo_Graph = Graph()

    lo_Graph.parse(data=logistics_object.json(), format="json-ld")

    return lo_Graph, logistics_object.status_code