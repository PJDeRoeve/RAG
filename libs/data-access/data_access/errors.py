"""Errors related to DAOs."""


class DAOError(Exception):
    """Something went wrong when accessing the database."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message: str = message


class DAONotFoundError(Exception):
    """Item not found in database."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message: str = message


class CacheExpiredError(Exception):
    """Cache has expired"""

    def __init__(self, message: str):
        super().__init__(message)
        self.message: str = message


class DAOInitializationError(Exception):
    """Something went wrong when initializing a DAO"""

    def __init__(self, message: str):
        super().__init__(message)
        self.message: str = message
