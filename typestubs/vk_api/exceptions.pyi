class ApiHttpError(Exception):
    pass

class ApiError(Exception):
    code: int
