from enum import Enum


class ProcessingMode(str, Enum):
    FAST = "fast"
    ACCURATE = "accurate"