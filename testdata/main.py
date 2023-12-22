from rdflib import Graph
import requests
import json

# Enter filepath
file_path = r'/Users/niclasscheiber/Desktop/DOH Hackathon/Import_Test.txt'

# Enter URL of your ONE Record Server
serverURL = "http://some-one-record-server.com/logistics-objects"

# Create initial graph
pre_existing_graph = Graph()
pre_existing_graph.parse(file_path)

# Create an array to store the individual graphs
individual_graphs = []
individual_jsons = []

# SPARQL query to retrieve individuals with the pattern "/logistics-objects/"
queryLO = """
    SELECT DISTINCT ?subject
    WHERE {
        ?subject ?predicate ?object .
        FILTER (regex(str(?subject), "/logistics-objects/"))
    }
"""

# SPARQL query to retrieve individuals with the pattern "neone: for embedded objects"
queryEO = """
    SELECT DISTINCT ?object
    WHERE {
        ?subject ?predicate ?object .
        FILTER (regex(str(?object), "neone:"))
    }
"""

def embedObjects(main_graph, sub_graph, sub_graph_json):

    # Query EOs from the given individual_graph
    resultsEO = sub_graph.query(queryEO)

    if len(resultsEO) > 0:

    # Iterate through results and add triples from original graph to a new graph
        for resultEO in resultsEO:

            #Create new graph
            eo_graph = Graph()

            #Select all triples where the given EO is the subject
            obj = resultEO['object']

            eo_graph += main_graph.triples((obj, None, None))

            # Save the graph as string in JSON-LD format
            eo_graph_json = eo_graph.serialize(format='json-ld')

            # Replace the EO reference in the json-version of individual graph
            sub_graph_json = sub_graph_json.replace('"@id": "' + obj + '"',
                                                              eo_graph_json[3:-3].replace("{", "", 1))

            # Replace the id of the EO in the json-version of individual graph
            sub_graph_json = sub_graph_json.replace('"@id": "' + obj + '",', "",1)

            # Recall method
            sub_graph_json = embedObjects(main_graph, eo_graph, sub_graph_json)

    return sub_graph_json

# Perform the SPARQL query on the pre-existing graph
results = pre_existing_graph.query(queryLO)

# Iterate over the query results and create individual graphs
for result in results:
    subject = result['subject']

    # Create a new graph for the individual
    individual_graph = Graph()

    # Add all triples of the individual to the individual graph
    individual_graph += pre_existing_graph.triples((subject, None, None))

    # Save the graph as string in JSON-LD format
    individual_graph_json = individual_graph.serialize(format='json-ld')

    # Recursively embed objects
    individual_graph_json = embedObjects(pre_existing_graph, individual_graph, individual_graph_json)

    # Add the json to the json array
    individual_jsons.append(individual_graph_json)

    # Add the individual graph to the array
    individual_graphs.append(individual_graph)

# Counter variable
postCounter = 0

# Post everything to the ONE Record Server
for individual_graph_json in individual_jsons:

    postCounter += 1

    print(postCounter, " / ", len(individual_jsons))

    r = requests.post("http://ne-one.de/airline/logistics-objects", json=json.loads(individual_graph_json),
                headers={"Content-Type": "application/ld+json"},)
