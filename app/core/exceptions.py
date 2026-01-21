# app/core/exceptions.py
"""
Custom domain exceptions.
These exceptions represent business logic errors, not HTTP errors.
"""

class DomainException(Exception):
    """Base exception for all domain errors."""
    def __init__(self, message: str = "A domain error occurred"):
        self.message = message
        super().__init__(self.message)


# Auth exceptions
class AuthenticationError(DomainException):
    """Raised when authentication fails."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when user credentials are invalid."""
    pass


class UserAlreadyExistsError(DomainException):
    """Raised when trying to register an existing user."""
    pass


# Project exceptions
class ProjectNotFoundError(DomainException):
    """Raised when a project doesn't exist."""
    pass


class ProjectCreationError(DomainException):
    """Raised when project creation fails."""
    pass


class InsufficientPermissionsError(DomainException):
    """Raised when user lacks required permissions."""
    pass


# Membership exceptions
class MembershipError(DomainException):
    """Base for membership-related errors."""
    pass


class MemberAlreadyExistsError(MembershipError):
    """Raised when trying to add an existing member."""
    pass


class LastOwnerError(MembershipError):
    """Raised when trying to remove the last owner."""
    pass

# Board exceptions
class BoardNotFoundError(DomainException):
    """Raised when a board doesn't exist."""
    pass

class BoardCreationError(DomainException):
    """Raised when board creation fails."""
    pass

# Task exceptions
class TaskNotFoundError(DomainException):
    """Raised when a task doesn't exist."""
    pass  

class TaskCreationError(DomainException):
    """Raised when task creation fails."""
    pass

class InvalidAssigneeError(DomainException):
    """Raised when the assignee is not a project member."""
    pass
# Resource exceptions
class ResourceNotFoundError(DomainException):
    """Generic resource not found."""
    pass


class ValidationError(DomainException):
    """Raised when business validation fails."""
    pass