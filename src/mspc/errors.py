class ServiceNotFoundError(Exception):
    pass


class ServiceIsDisabledError(Exception):
    pass


class ServiceError(Exception):
    pass


class NothingFoundError(Exception):
    pass


class NoNextTrackError(Exception):
    pass


class NoPreviousTrackError(Exception):
    pass


class IncorrectProtocolError(Exception):
    pass


class PathNotFoundError(Exception):
    pass


class IncorrectTrackIndexError(Exception):
    pass


class NothingIsPlayingError(Exception):
    pass


class IncorrectPositionError(Exception):
    pass


class LoginError(Exception):
    pass


class LocaleNotFoundError(Exception):
    pass
