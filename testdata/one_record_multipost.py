from rdflib import Graph
import requests
import json

# 1. Enter filepath
file_path = r'./03032024_Testdata.nt'

# 2. Enter URL of your ONE Record Server logistics-objects endpoint, eg. "http://localhost:8080/logistics-objects"
server_url = "http://localhost:8080/logistics-objects"

# 3. If your server requires authentication: Enter the token here, eg. "abc123"
token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJGYzdaSHZUNGozbldNenZkX2xuYUsySGZWWnUtYWtBLTB0TGMwLVgwc1BZIn0.eyJleHAiOjE3MDk3NTMzMjIsImlhdCI6MTcwOTcxNzMyMiwianRpIjoiZTUzZTYyMDgtNjBlMS00ZDcwLTk4YmYtYzhmZWNhYTE4ODIyIiwiaXNzIjoiaHR0cDovL2xvY2FsaG9zdDo4OTg5L3JlYWxtcy9uZW9uZSIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiIwYWU4OThmMy1kMjQ4LTRlYWMtODY4MS1iMDM4MWM4MmQ2YzAiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJuZW9uZS1jbGllbnQiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbIioiXSwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbIm9mZmxpbmVfYWNjZXNzIiwiZGVmYXVsdC1yb2xlcy1uZW9uZSIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJwcm9maWxlIGVtYWlsIiwiY2xpZW50SG9zdCI6IjE3Mi4yMS4wLjEiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsImxvZ2lzdGljc19hZ2VudF91cmkiOiJodHRwOi8vbG9jYWxob3N0OjgwODAvbG9naXN0aWNzLW9iamVjdHMvX2RhdGEtaG9sZGVyIiwicHJlZmVycmVkX3VzZXJuYW1lIjoic2VydmljZS1hY2NvdW50LW5lb25lLWNsaWVudCIsImNsaWVudEFkZHJlc3MiOiIxNzIuMjEuMC4xIiwiY2xpZW50X2lkIjoibmVvbmUtY2xpZW50In0.yXKjY0SkHaLm1ixndlWGf3OaXaK-3herHNahIOOLuXw9HZnvPq0xLvjIQCrlX8aBDcj--1_NFh6Wmko8tUJOlE7ycMq657zwZEjbO0tPv6LPlGkDzDC6juYbji0U-5QcfjSwfnH3-JsuEBt-KCuJQ4kOU-BMsU3GtJNlqzJ0uhkLAM0FxZF-IwFgmuxma9k60Bk4T_iJ9ro3VJzEdnm8i5fFRXnec-Tsvyi5woYR1C49G1uxYFOmLFWYwTAvvHoK4XkF7m0GDA9-UPD_kaPkHEoT748aK0jnWJf7wIR58I8jUajtOMZLL9hVA8tN430x5G55vNX3TKwUHvVDhzibig"

# 4. Run the script. Ignore parsing warnings. It will take a few minutes.





# Open file
with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
    file_content = file.read()

# Do not change this
file_content = file_content.replace("https://www.someurl.com/logistics-objects", server_url)

# Create initial graph
pre_existing_graph = Graph()
pre_existing_graph.parse(data=file_content, format="nt")

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
        FILTER (regex(str(?object), "_:"))
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
            sub_graph_json = sub_graph_json.replace('"@id": "' + obj + '",', "", 1)

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

    # Create graph
    json_graph = Graph()

    postCounter += 1

    r = requests.post(server_url, json=json.loads(individual_graph_json),
                headers={"Content-Type": "application/ld+json", "Authorization": "Bearer " + token}, )

    if r.status_code == 500:

        # Create a unique file name based on the timestamp
        file_path_json = f'./jsons/error_post_{postCounter}.json'

        json_graph.parse(data=individual_graph_json, format="json-ld")

        json_graph.serialize(destination=file_path_json, format='json-ld')

        while r.status_code == 500:
            print("500 error, retry")
            r = requests.post(server_url, json=json.loads(individual_graph_json),
                              headers={"Content-Type": "application/ld+json", "Authorization": "Bearer " + token}, )

    print(postCounter, " / ", len(individual_jsons), " ", str(r.status_code), " ", r.text)