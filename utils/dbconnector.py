import io
import json
import requests

import polars as pl

# read config
with open("config.json") as f:
    config = json.load(f)
questdb_settings = config["questdb"]


class Database:
    def __init__(self):
        pass

    def get_scalar(self, query):
        """
        Gets a scalar from a query

        Args:
            query (str): Query to run

        Returns:
            scalar (float): Scalar with the data
        """
        # prepare url with db config and query
        url = f"http://{questdb_settings['host']}:{questdb_settings['port_web']}/exec?query={query}"

        # get scalar
        r = requests.get(url)

        # read scalar
        return json.loads(r.text)["dataset"][0][0]
