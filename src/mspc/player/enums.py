from enum import Enum


class State(Enum):
    STOPPED = "Stopped"
    PLAYING = "Playing"
    PAUSED = "Paused"


class Mode(Enum):
    SINGLE_TRACK = "st"
    REPEAT_TRACK = "rt"
    TRACK_LIST = "tl"
    REPEAT_TRACK_LIST = "rtl"
    RANDOM = "rnd"
