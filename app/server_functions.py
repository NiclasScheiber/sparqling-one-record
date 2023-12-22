import pandas as pd
from rdflib.plugins.sparql import prepareQuery
from rdflib import URIRef

from logistics_objects_handling import get_logistics_object_as_graph

# Extract triples from Where-Clause of parsed SPARQL-query
def extract_triples(algebra):
    bgp_triples = []
    variable_bindings = []


    if algebra.name == 'BGP':
        bgp_triples.extend(algebra['triples'])

    elif 'p' in algebra:

        # Extract bindings
        if 'expr' in algebra and 'var' in algebra:

            # To-do: Check if more than one element exists in algebra 'var' clause
            if isinstance(algebra['expr'], URIRef):
                variable_bindings.append((algebra['expr'], algebra['var']))

        triples, bindings = extract_triples(algebra['p'])
        bgp_triples.extend(triples)
        variable_bindings.extend(bindings)
    elif 'p1' in algebra and 'p2' in algebra:
        triples_p1, bindings_p1 = extract_triples(algebra['p1'])
        triples_p2, bindings_p2 = extract_triples(algebra['p2'])
        bgp_triples.extend(triples_p1 + triples_p2)
        variable_bindings.extend(bindings_p1 + bindings_p2)
    elif 'elements' in algebra:
        for element in algebra['elements']:
            triples, bindings = extract_triples(element)
            bgp_triples.extend(triples)
            variable_bindings.extend(bindings)

    return bgp_triples, variable_bindings

def parse_BGP_from_sparql_query(query):

    # Extract triples from the algebraic form
    triples, bindings = extract_triples(query.algebra)

    # Create a DataFrame and return it
    columns = ['subject', 'predicate', 'object']
    columns2 = ['uri', 'variable']
    return pd.DataFrame(triples, columns=columns), pd.DataFrame(bindings, columns=columns2)

# Extract and build a sub-query for a specific logistics object
def create_subquery_for_logistics_object(uri, variable, query_frame, lo_presence_flag):

    # Flag for variable properties, since they cannot be used with the VALUES clause
    variable_property = False
    explicit_property = False
    explicit_object = False
    variable_name = ''

    # Hold uri to check, set to None if lo presence flag and a variable is present
    # Note: For first element, variable is always None, hence query is created even if it already is in-memory
    uri_for_check = uri
    if lo_presence_flag and variable is not None:
        uri_for_check = None

    # Build introduction to query
    query_str = """select ?new_predicate ?object where{\n"""

    # And to values clause
    query_values_clause = """values ?new_predicate { """

    # And to explicit rows
    explicit_rows = ""

    # Loop through query frame
    for index, row in query_frame.iterrows():
        # Access row data if subject is uri or variable - if uri already present, just for variable
        if (row['subject'] == uri_for_check) or (row['subject'] == variable):

            # if object is explicit, add all triples
            if "/" in str(row['object']):
                # Set explicit object to true
                explicit_object = True

                # Format string differently if predicate is explicit (<>) or variable (?)
                if "/" in str(row['predicate']):
                    explicit_rows += "<" + str(uri) + ">" + " <" + str(row['predicate']) + "> <" + str(row['object']) + ">.\n"
                else:
                    explicit_rows += "<" + str(uri) + ">" + " ?" + str(row['predicate']) + " <" + str(row['object']) + ">.\n"

            # if property is explicit
            elif "/" in str(row['predicate']):
                query_values_clause += "<" + str(row['predicate']) + "> "
                explicit_property = True
            # if property is a variable
            else:
                variable_name = row['object']
                variable_property = True

    # Finish the Values clause
    query_values_clause += """ }\n"""

    # Add query values clause for explicit property
    if variable_property:
        query_str += """     <""" + str(uri) + """> ?new_predicate ?object .\n"""
    elif explicit_property:
        query_str += query_values_clause
        query_str += """     <""" + str(uri) + """> ?new_predicate ?object .\n"""
    elif explicit_object:
        # Do nothing
        query_str += ""
    else:
        # Return no query, since LO does not need to be fetched
        return None, None, None

    # Add explicit rows if there have been any
    query_str += explicit_rows

    # Finish query with Filter for real linked logistics-objects
    query_str += """     filter(regex(str(?object), "/logistics-objects/")) \n}"""

    # print(query_str)

    query = prepareQuery(query_str)

    return query, variable_property, variable_name

# ASK query on the main graph to see if the LO is already in main_graph
def ask_logistics_object_presence(uri, graph):

    uri = URIRef(uri)

    return (uri, None, None) in graph

# Iteratively fetch logistics objects if the query needs them
def fetch_logistics_objects(pattern_frame, current_los_to_fetch_frame, full_los_to_fetch_frame, full_graph):

    # Initialize list of los to fetch
    new_los_to_fetch_df = pd.DataFrame(columns=['uri', 'variable', 'status_code'])

    for index in current_los_to_fetch_frame.index:

        row = current_los_to_fetch_frame.loc[index]
        uri = row['uri']

        sub_query = None
        lo_already_present = False

        # Check if URI is already fetched
        lo_variable_already_present = (full_los_to_fetch_frame[['uri', 'variable', 'status_code']] == (row['uri'], row['variable'], 200)).all(axis=1).any()

        if not lo_variable_already_present:

            # Extract BGF statements that apply for LO that might need to be fetched
            sub_query, variable_property, variable_name = create_subquery_for_logistics_object(uri, row['variable'], pattern_frame, lo_already_present)

            lo_already_present = ask_logistics_object_presence(row['uri'], full_graph)
            #(full_los_to_fetch_frame[['uri', 'status_code']] == (row['uri'], 200)).all(axis=1).any()
        else:
            print("LO already fetched and bound")

        # If a query could be created, fetch LO and perform query
        if sub_query is not None:

            # Check if LO was already fetched, only fetch if not
            if lo_already_present:

                # Fill status_code in los_to_fetch_df dataframe
                current_los_to_fetch_frame.loc[index, 'status_code'] = 200

                print("LO already fetched")

                # Perform query on full_graph since the LO was not refetched
                query_graph = full_graph

            # Otherwise get it!
            else:
                # Get LO as graph, add triples to main_graph
                sub_graph, status_code = get_logistics_object_as_graph(row['uri'])
                full_graph += sub_graph

                # Fill status_code in los_to_fetch_df dataframe
                current_los_to_fetch_frame.loc[index, 'status_code'] = status_code

                print("fetched LO", str(row['uri']), "with code", status_code)

                # Perform query on smaller sub_graph
                query_graph = sub_graph


            # Write down what was (not) fetched for debugging
            full_los_to_fetch_frame.loc[len(full_los_to_fetch_frame)] = current_los_to_fetch_frame.loc[index]

            # Perform the query then
            sub_query_results = query_graph.query(sub_query)

            # If something was found, add to list of LOs to query
            if len(sub_query_results) > 0:
                sub_query_results_df = pd.DataFrame(sub_query_results.bindings)
                sub_query_results_df.columns = ['predicate', 'uri']
                sub_query_results_df = pd.merge(sub_query_results_df, pattern_frame, on="predicate", how="left").drop(columns=["subject", "predicate"])
                sub_query_results_df.columns = ['uri', 'variable']

                # if variable_property was used, replace NaN subjects
                if variable_property:
                    sub_query_results_df.fillna(variable_name, inplace=True)

                # Add empty column
                sub_query_results_df['status_code'] = None

                # Append to full list
                new_los_to_fetch_df = pd.concat([new_los_to_fetch_df, sub_query_results_df], ignore_index=True)

    # Iterate again through all new los to fetch
    if not new_los_to_fetch_df.empty:
        fetch_logistics_objects(pattern_frame, new_los_to_fetch_df, full_los_to_fetch_frame, full_graph)