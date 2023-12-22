![Logo](./assets/sparqling-one-record-logo.jpg)

# SPARQLing ONE Record Middleware Server

The Sparqling ONE Record middleware server is a demonstration application to execute SPARQL queries on ONE Record data compliant with [Data Model 3.0.0](https://onerecord.iata.org/ns/cargo) and [API 2.0.0](https://iata-cargo.github.io/ONE-Record/). It is built using RDFlib, Flask, Requests, and Pandas. Please note that this server is designed for demonstration purposes and is not intended for productive use.

It was developed built on knowledge gained through research project Digitales Testfeld Air Cargo (DTAC), sponsored by the German Ministry for Digital and Transport.

## Features

- **SPARQL Query Dissection**: On POST requests to the endpoint `/sparql`, the server parses the body in text form as a SPARQL query. It dissects the query into algebraic components to create sub-queries to execute sequentially.

- **Sequential Logistics Objects Retrieval**: The server fetches the first ONE Record logistics object based on the parsed query. From there, it sequentially fetches and queries the ONE Record graph.

- **Result Presentation**: Once all required logistics objects are fetched, the full query is applied to the dataset, and the result bindings are returned as a Pandas DataFrame converted to a string.

## Missing Features

The middleware server is currently incomplete and lacks some important features, including:

- **Handling Inaccessible LogisticsObjects**: The server does not handle cases where LogisticsObjects are inaccessible.

- **Authentication to ONE Record Servers**: Authentication mechanisms to access ONE Record servers are not implemented.

- **Proper HTTP Responses and Error Codes**: The server does not provide proper HTTP responses and error codes.

- **Multiple Output Formats**: The server currently supports only a string-converted Pandas DataFrame as an output format.

## Sample SPARQL Queries

The repository includes sample SPARQL queries for selected, simplified air cargo documents. These queries can be used to test and demonstrate the capabilities of the middleware server.

| Query           | Anchor LogisticsObject | Description                                                                                                              |
|-----------------|------------------------|--------------------------------------------------------------------------------------------------------------------------|
| flight_manifest | TransportMovement      | Returns a simplified flight manifest per master air waybill                                                              |
| special_loads   | TransportMovement      | Returns a list of all special loads per master air waybill including all relevant Special Handling Codes (compare NOTOC) |

## Test data

This repository contains ONE Record test data to try the SPARQL queries and a script to shoot it onto a ONE Record Server. The test data was randomly generated as part of the Digital Avatar sub-project of research project Digitales Testfeld Air Cargo (DTAC), sponsored by the German Ministry for Digital and Transport.

Will be added in the near future.

## Usage

TBD

## Disclaimer

This middleware server is intended for demonstration purposes only. Use it cautiously and avoid deploying it in production environments.