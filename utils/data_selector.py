import pandas as pd
import numpy as np
import scipy.stats as stats
import warnings
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.backend_tools import ToolToggleBase

plt.rcParams["toolbar"] = "toolmanager"
mpl.use('qtagg')

class DataSelector:
    def __init__(
        self, df: pd.DataFrame = None, title_prefix: str = "", show_cols: list = []
    ) -> None:
        """DataSelector class
        Args:
            df (pd.DataFrame): dataframe to truncate (time must be on index as pd.DatetimeIndex)
            show_cols (list): columns to show (if emply -> all columns are used)
            title_prefix (str): title
        """

        self.df = df
        self.show_cols = show_cols
        self.title_prefix = title_prefix

    def get_startArgs_of_gaps(
        self, time: np.array, p_value=1e-8, maxIter=10
    ) -> np.array:
        """Get all start indices of the gaps
        Args:
            time (np.array): timestamps as floats
            p_value (float): p value of test
            maxIter (int): max iteration allowed before returning (raises a warning if exceeded)
        Returns:
            numpy array with indices that point on the position of x which are right before a gap
        """

        # check if dtype of time is a float
        if not np.issubdtype(time.dtype, np.floating):
            raise TypeError("time must be from a floating type")

        freq = 1 / np.diff(time)  # get frequencies
        freq_copy = np.copy(freq)  # copy frequencies

        # calculate parameter for normal distribution in while loop
        mean = np.mean(freq_copy)
        std = np.std(freq_copy)

        old_startArgs = None  # stores a copy of startArgs
        counter = 0  # counts runs of loop
        while True:
            thres = stats.norm.ppf(
                q=p_value, loc=mean, scale=std
            )  # calculate upper threshold value of frequency to be allowed

            startArgs = np.argwhere(freq < thres)  # find startArgs

            if isinstance(old_startArgs, np.ndarray):  # if not first time
                if np.array_equal(old_startArgs, startArgs):  # successfully converged
                    return startArgs.flatten()

            else:  # first time (no value store in old_startArgs)
                old_startArgs = startArgs

            freq_copy = np.delete(freq, startArgs)  # delete all the 'bad frequencies'

            # try to find params of pure distribution
            mean = np.mean(freq_copy)
            std = np.std(freq_copy)

            counter += 1
            # max iterations reached
            if counter > maxIter:
                warnings.warn("startArgs did not converge")
                return startArgs.flatten()

    def get_mean_fs(self, time: np.array) -> float:
        """Calculates the mean sampling frequency
        Args:
            time (np.array): timestamps as floats
        Returns:
            mean sampling frequency in Hz
        """

        # check if dtype of time is a float
        if not np.issubdtype(time.dtype, np.floating):
            raise TypeError("time must be from a floating type")

        freq = 1 / np.diff(time)  # get frequencies

        return np.mean(freq)  # return mean

    def get_std_fs(self, time: np.array) -> float:
        """Calculates the standard deviation of the sampling frequency
        Args:
            time (np.array): timestamps as floats
        Returns:
            std sampling frequency in Hz
        """

        # check if dtype of time is a float
        if not np.issubdtype(time.dtype, np.floating):
            raise TypeError("time must be from a floating type")

        freq = 1 / np.diff(time)  # get frequencies

        return np.std(freq)  # return std

    def truncate(self, **kwargs) -> pd.DataFrame:
        """Interactive truncating of a dataframe (also shows gaps as red squares & displays metrics about sampling frequency in title)

        Returns:
            truncated dataframe
        """

        class Marker(ToolToggleBase):
            default_keymap = "M"
            description = "Marker"
            default_toggled = False

            def __init__(self, *args, gid, **kwargs) -> None:
                self.gid = gid
                super().__init__(*args, **kwargs)

                self.__clickEvent_gid = None  # gid of clickEvent stored here
                self.__line2D_1: Line2D = None  # line1 stored here
                self.__line2D_2: Line2D = None  # line2 stored here
                self.__polygon = None  # box store here

                # coordinates of selected area stored here
                self.xcordBegin = None
                self.xcordEnd = None

            def removeMarker(self):
                if self.__line2D_1:
                    ax.lines.remove(self.__line2D_1)
                    self.__line2D_1 = None

                if self.__line2D_2:
                    ax.lines.remove(self.__line2D_2)
                    self.__line2D_2 = None

                if self.__polygon:
                    ax.patches.remove(self.__polygon)
                    self.__polygon = None

                self.xcordBegin = None
                self.xcordEnd = None

                fig.canvas.draw()  # this line was missing earlier

            def onClick(self, event):
                xData = event.xdata

                if xData != None:
                    if not self.__line2D_1 and not self.__line2D_2:  # no lines defined
                        self.__line2D_1 = ax.axvline(xData, color="magenta")
                        self.xcordBegin = xData

                    elif self.__line2D_1 and not self.__line2D_2:  # start line defined
                        self.__line2D_2 = ax.axvline(xData, color="magenta")
                        self.__polygon = ax.axvspan(
                            self.__line2D_1.get_xdata(orig=True)[0],
                            self.__line2D_2.get_xdata(orig=True)[0],
                            color="magenta",
                            alpha=0.1,
                        )
                        self.xcordEnd = xData

                    else:  # both lines defined
                        self.removeMarker()

                    fig.canvas.draw()

            def enable(self, *args):
                self.__clickEvent_gid = self.figure.canvas.mpl_connect(
                    "button_press_event", self.onClick
                )

            def disable(self, *args):
                self.figure.canvas.mpl_disconnect(self.__clickEvent_gid)

                self.removeMarker()

        # check if index has correct type
        if not isinstance(self.df.index, pd.DatetimeIndex):
            raise Exception("index of df must be from type 'pandas.DatetimeIndex'")

        normalized_index = (self.df.index - self.df.index[0]) / pd.Timedelta(
            1, "s"
        )  # make index relative and convert to seconds

        # select cols (no selected -> select all)
        cols_to_show = self.show_cols or self.df.columns
        fig, ax = plt.subplots(1, 1)

        gapArgs = self.get_startArgs_of_gaps(
            normalized_index, **kwargs
        )  # get start args of gaps

        if len(gapArgs) > 0:  # if gaps found
            splitted_index = np.split(
                self.df.index.values, gapArgs + 1
            )  # split index so gaps are in between of splits

            # first section
            first_sub_df = self.df.loc[splitted_index[0]]  # get first sub dataframe
            colors = {
                col: ax.plot(
                    first_sub_df.index.values, first_sub_df[col].values, label=col
                )[0].get_color()
                for col in cols_to_show
            }
            # iterate over remaining sections
            for i in range(1, len(splitted_index)):
                # draw gap
                gap_start_x = splitted_index[i - 1][-1]
                gap_end_x = splitted_index[i][0]
                ax.axvspan(gap_start_x, gap_end_x, color="red", alpha=0.1)

                sub_df = self.df.loc[splitted_index[i]]  # get sub dataframe

                # plot columns
                for col in cols_to_show:
                    ax.plot(sub_df.index.values, sub_df[col].values, color=colors[col])

        else:
            # plot columns
            for col in cols_to_show:
                ax.plot(self.df.index.values, self.df[col].values, label=col)

        ax.set_title(
            f"{self.title_prefix} [mean sf= {np.round(self.get_mean_fs(normalized_index), 4)}Hz; std= {np.round(self.get_std_fs(normalized_index), 4)}Hz]"
        )
        ax.set_xlabel("relative time [s]")
        ax.set_ylabel("value")
        ax.legend()

        # add custom tool
        toggleButton: Marker = fig.canvas.manager.toolmanager.add_tool(
            "Marker", Marker, gid="marker"
        )
        fig.canvas.manager.toolbar.add_tool("Marker", "Additionals")
        plt.show(block=True)

        # check if no area selected
        if not toggleButton.xcordBegin or not toggleButton.xcordEnd:
            raise Exception("No area selected")

        # convert numbers we get from matplotlib to datetime
        xStart_dateTime = np.datetime64(mpl.dates.num2date(toggleButton.xcordBegin))
        xEnd_dateTime = np.datetime64(mpl.dates.num2date(toggleButton.xcordEnd))

        return self.df.loc[
            (self.df.index >= xStart_dateTime) & (self.df.index <= xEnd_dateTime)
        ]
