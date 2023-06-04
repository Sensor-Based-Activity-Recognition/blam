import io
import json
import requests

import polars as pl

# Load database configuration
with open("config.json") as f:
    config = json.load(f)
questdb_settings = config["questdb"]  # Extract QuestDB settings from the loaded configuration

class Database:
    """
    A class to interact with a database.

    ...

    Attributes
    ----------
    None

    Methods
    -------
    get_scalar(query:str) -> float:
        Execute a query and return a scalar.
    """

    def __init__(self):
        """
        Constructs all the necessary attributes for the Database object.
        """
        pass

    def get_scalar(self, query: str) -> float:
        """
        Execute a SQL query and return a scalar.

        Args:
            query (str): SQL query to execute.

        Returns:
            scalar (float): Scalar result of the query.
        """
        # Prepare the URL for the HTTP request by concatenating the host, port, and query parameters
        url = f"http://{questdb_settings['host']}:{questdb_settings['port_web']}/exec?query={query}"

        # Send an HTTP GET request to the specified URL
        r = requests.get(url)

        # Parse the response text as JSON and extract the scalar result
        return json.loads(r.text)["dataset"][0][0]
