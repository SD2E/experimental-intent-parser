from enum import Enum


class TableType(Enum):
    UNKNOWN = 1
    LAB = 2
    MEASUREMENT = 3
    PARAMETER = 4
    CONTROL = 5
    EXPERIMENT_STATUS = 6
    EXPERIMENT_SPECIFICATION = 7