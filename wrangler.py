import json
import polars as pl
from questdb.ingress import Sender

# read config.json file
with open("config.json") as json_data_file:
    config = json.load(json_data_file)


class File:
    """
    Class to get data from SensorLogger App Files and write new data to database

    Attributes:
        path (str): Path to the dataset

    Methods:
        get_data: Returns the data as a polars DataFrame
    """

    def __init__(self, path="./", sensors=["time"], data=None):
        """
        Args:
            path (str): Path to the dataset
            sensors (list): List of sensors to use
            data (polars.DataFrame): Dataframe with the data
        """

        self.path = path
        self.sensors = sensors
        self.data = data

    def get_data(self):
        """
        Returns the data as a polars DataFrame

        Returns:
            data (polars.DataFrame): Dataframe with the data
        """
        # check if data is already loaded
        if self.data is None:
            # error handling
            try:
                # read json + lazy
                data = pl.read_json(self.path).lazy()

                # melt data grouped by time and sensor
                data = data.melt(id_vars=["time", "sensor"])

                # rename variable to sensor_variable
                data = data.with_columns(
                    (pl.col("sensor") + "_" + pl.col("variable")).alias("variable")
                )

                # drop sensor column
                data = data.drop(["sensor"])

                # time to int
                data = data.with_columns(pl.col("time").cast(pl.Int64).alias("time"))

                # change resolution of data to 10ms
                data = data.with_columns(
                    (pl.col("time") // 10000000 * 10).cast(pl.Int64).alias("time")
                )

                # change time measurements from nanoseconds to milliseconds
                data = data.with_columns(pl.from_epoch("time", unit="ms").alias("time"))

                # convert values to float if possible
                data = data.with_columns(
                    pl.col("value").cast(pl.Float32, strict=False).alias("value")
                )

                # filter sensors
                data = data.filter(pl.col("variable").is_in(self.sensors))

                # collect 1
                data = data.collect()

                # pivot the data + lazy
                data = data.pivot(
                    index="time",
                    columns="variable",
                    values="value",
                    aggregate_function="mean",
                    sort_columns=True,
                ).lazy()

                # add file name to columns as filename
                data = data.with_columns(
                    pl.lit(self.path.split("/")[-1].split(".")[0]).alias("filename")
                )

                # add person name to columns as person
                data = data.with_columns(
                    pl.lit(self.path.split("/")[-2]).alias("person")
                )

                # add activity name to columns as activity
                data = data.with_columns(
                    pl.lit(self.path.split("/")[-3]).alias("activity")
                )

                # collect 2
                data = data.collect()

                # set data
                self.data = data

                # return data
                return self.data

            except Exception as e:
                # throw error if occurred
                print(f"Error processing {self.path}: {e}")
                return None

        return self.data

    def write_data(self, data=None, table="test"):
        """
        Writes the data to the database

        Args:
            data (polars.DataFrame): Dataframe with the data
            table (str): Name of the table to write to

        Returns:
            success (bool): True if successful, False if not
        """
        # error handling
        try:
            # check if data was passed, if not, use self.data
            if data is None:
                data = self.data
            # write data to database
            with Sender(config["questdb"]["host"], config["questdb"]["port"]) as sender:
                # note: polars DataFrame needs to be converted to pandas DataFrame
                sender.dataframe(df=data.to_pandas(), table_name=table)
            # return True if successful
            return True

        except Exception as e:
            # print error and return False if occured
            print(f"Error writing data to database: {e}")
            return False
