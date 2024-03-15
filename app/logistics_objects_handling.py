import requests
from rdflib import Graph

# GET Logistics object and return as graph - will include auth in the future
def get_logistics_object_as_graph(lo_iri, token):

    logistics_object = requests.get(lo_iri, headers={"Content-Type": "application/ld+json", "Authorization": "Bearer " + token}, )

    lo_Graph = Graph()

    lo_Graph.parse(data=logistics_object.json(), format="json-ld")

    return lo_Graph, logistics_object.status_code