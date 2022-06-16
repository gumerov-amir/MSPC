from enum import Enum


class SoundDeviceType(Enum):
    OUTPUT = 0
    INPUT = 1


class SoundDevice:
    def __init__(self, name: str, id: str, type: SoundDeviceType) -> None:
        self.name = name
        self.id = id
        self.type = type
