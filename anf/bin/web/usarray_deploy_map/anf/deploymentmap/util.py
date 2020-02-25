"""Utility Functions and classes for deployment_map."""

import argparse
import collections
import datetime
import logging
import os

from antelope import stock

from . import constant
from .exceptions import DeployMapValueError, YearMonthValueError

LOGGER = logging.getLogger(__name__)


class YearMonth(collections.namedtuple("YearMonth", ["year", "month"])):
    """Track a numeric Year and Month for the deployment maps."""

    @staticmethod
    def get_default():
        """Return a YearMonth object representing the most recent plausible map.

        Monthly deployment maps are normally generated at the end of the month, so
        this returns the YearMonth associated with the previous full month.
        """
        today = datetime.date.today()
        if today.month == 1:
            return YearMonth(today.year - 1, 12)
        return YearMonth(today.year, today.month - 1)


class ValidateYearMonth(argparse.Action):  # pylint: disable=too-few-public-methods
    """Argparse validator for year and month."""

    def __call__(self, parser, args, values, option_string=None):
        """Validate the Year and Month.

        Args:
            parser, args, option_string - as per parent class.
            values (list(int, int)) - two element list of year, month
        """
        valid_years = range(constant.START_YEAR, constant.MAX_YEAR)
        valid_months = range(1, 12)
        (year, month) = values
        year = int(year)
        if year not in valid_years:
            raise YearMonthValueError("invalid year {s!r}".format(s=year))
        month = int(month)
        if month not in valid_months:
            raise YearMonthValueError("invalid month {s!r}".format(s=month))
        setattr(args, self.dest, YearMonth(year, month))


class StoreDeployType(argparse.Action):  # pylint: disable=too-few-public-methods
    """Argparse action for handing the Deployment Type."""

    def __call__(self, parser, args, value, option_string=None):
        """Store the Deployment type.

        Expects values to contain a single element.

        If values[0] is both, then set the resulting attribute to DEPLOYMENT_TYPES
        """
        if value not in constant.DEPLOYMENT_TYPES + ["both"]:
            raise DeployMapValueError("invalid deployment type {s!r}".format(s=value))
        if value == "both":
            value = constant.DEPLOYMENT_TYPES
        setattr(args, self.dest, value)


class StoreMapType(argparse.Action):  # pylint: disable=too-few-public-methods
    """Argparse action for handing the Map Type."""

    def __call__(self, parser, args, value, option_string=None):
        """Store the Map type.

        Expects values to contain a single element.

        If values[0] is both, then set the resulting attribute to MAP_TYPES
        """
        if value not in constant.MAP_TYPES + ["both"]:
            raise DeployMapValueError("invalid map type {s!r}".format(s=value))
        if value == "both":
            value = constant.MAP_TYPES
        setattr(args, self.dest, value)


def get_start_end_timestamps(year, month):
    """Generate start and end time unix timestamps for dbsubsets.

    Args:
        year (int): ending year in integer format
        month (int): ending month in integer format

    Returns:
        tuple (int, int): tuple containing the unix start time and end time
    """

    logger = logging.getLogger(__name__)
    logger.debug("month:%s", month)
    logger.debug("year:%s", year)
    month = int(month)
    year = int(year)
    next_year = year
    next_month = month + 1
    if next_month > 12:
        next_month = 1
        next_year = next_year + 1

    logger.debug("next_month: %s", next_month)
    logger.debug("next_year: %s", next_year)

    start_time = stock.str2epoch("%02d/01/%4d 00:00:00" % (month, year))
    end_time = stock.str2epoch("%02d/01/%4d 00:00:00" % (next_month, next_year))
    logger.info("START:%s => %s", start_time, stock.strdate(start_time))
    logger.info("END:%s => %s", end_time, stock.strdate(end_time))

    return start_time, end_time


def set_working_dir(path):
    """Change working to directory to path."""
    full_path = os.path.abspath(os.path.expanduser(path))
    full_cwd = os.path.abspath(os.getcwd())
    if full_cwd != full_path:
        os.chdir(full_path)
        LOGGER.info('Changed current working directory to "%s".', full_path)


class StationSensorClassifier:
    """Abstract class for station classification based on it's sensors."""

    @property
    def sensor_classes(self):
        raise NotImplementedError


class InframetClassifier:
    """Classify an Inframet station based on it's sensors."""

    _sensor_classes = ['mems', 'ncpa', 'setra', 'complete']

    @property
    def sensor_classes(self):
        return set(self._sensor_classes)

    @classmethod
    def classify(cls, sensors):
        """Classify an Inframet station based on it's sensors.

        Args:
            sensors (set): the sensors that a station is equipped with.

        Returns:
            (string): containing the sensor class.
        """

        s = None
        if sensors == cls.sensor_classes:
            s = "complete"
        elif sensors == {"MEMS", "NCPA"}:
            s = "ncpa"
        elif sensors == {"MEMS", "SETRA"}:
            s = "setra"
        elif s == {"MEMS"}:
            s = "mems"

        return s

    def __call__(cls, sensors):
        return cls.classify(sensors)
