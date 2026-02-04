from enum import Enum


class Strategy(str, Enum):
    DELAY = "delay"
    CLARIFY = "clarify"
    PROBE = "probe"
    EXTRACT = "extract"
    DEESCALATE = "deescalate"
    EXIT = "exit"
