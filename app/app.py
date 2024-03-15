import pandas as pd
import server_functions as sf
from flask import Flask, request
from rdflib import Graph
from rdflib.plugins.sparql import prepareQuery

# Create main results graph to persist during a session
main_graph = Graph()

# Create the Flask Server
app = Flask(__name__)

# Token
token = ""

# Route for default HTTP GET request
@app.route('/')
def hello():
    return 'Hello, World! This "Sparqling ONE Record", a middleware server to query ONE Record Servers with SPARQL.'

@app.route('/token', methods=['POST'])
def token_post():
    global token
    token = request.data.decode('utf-8')
    return 'Token set as' + token

# Route to handle sparql HTTP POST request
@app.route('/sparql', methods=['POST'])
def sparql_post():
    if not token:
        return "Please set the ONE Record server token to /token endpoint"

    if request.is_json:
        return 'This route expects a SPARQL query as plain text.'

    # Check SPARQL-Query and prepare query - TO-DO invalid query?
    plain_request = request.data.decode('utf-8')
    main_query = prepareQuery(plain_request)

    # Extract pattern from query
    pattern_df, binding_df = sf.parse_BGP_from_sparql_query(main_query)

    # Retrieve anchor LO: one subject in where clause must be explicitly stated
    anchor_lo_uri = None
    anchor_lo_variable = None

    for index, row in binding_df.iterrows():

       # Access row data using row['subject']
       if "/logistics-objects/" in row['uri']:

        anchor_lo_uri = row['uri']
        anchor_lo_variable = row['variable']
        break

    if anchor_lo_uri is None:
        # TO-DO exception and Http code in header
        return "One valid logistics-object must be bound to a variable"

    # Create LO to fetch frame
    los_to_fetch_df = pd.DataFrame(columns=['uri', 'variable', 'status_code'])

    # Append anchor_lo_uri to LO to fetch frame
    los_to_fetch_df.loc[len(los_to_fetch_df)] = [anchor_lo_uri, anchor_lo_variable, '']

    # Iteratively fetch and query logistics objects
    sf.fetch_logistics_objects(pattern_df, los_to_fetch_df, los_to_fetch_df, main_graph, token)

    # Perform final query and return the results as dataframe in string form
    result_graph = main_graph.query(main_query)
    result_df = pd.DataFrame(result_graph.bindings)
    return result_df.to_string()

if __name__ == '__main__':
    app.run(debug=True)