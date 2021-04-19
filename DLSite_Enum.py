from enum import Enum, auto


class DLSite_Rate(Enum):
    UNKNOWN = 0
    ALL_AGE = auto()
    R15 = auto()
    R18 = auto()


class DLSite_Type(Enum):
    UNKNOWN = 0
    GAME = auto()
    COMIC = auto()
    CG_ART = auto()
    NOVEL = auto()
    ANIMATION = auto()
    VOICE = auto()
    MUSIC = auto()
    MATERIAL = auto()
    OTHER = auto()
