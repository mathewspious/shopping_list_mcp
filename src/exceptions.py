"""
Custom exceptions for Shopping List MCP Server
"""


class ShoppingListError(Exception):
    """Base exception for shopping list errors"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(ShoppingListError):
    """Database operation errors"""
    pass


class DatabaseConnectionError(DatabaseError):
    """Database connection errors"""
    pass


class UserNotFoundError(ShoppingListError):
    """User not found"""
    pass


class UserCreationError(ShoppingListError):
    """Error creating user"""
    pass


class ShoppingListNotFoundError(ShoppingListError):
    """Shopping list not found"""
    pass


class ItemNotFoundError(ShoppingListError):
    """Item not found in shopping list"""
    pass


class ItemOperationError(ShoppingListError):
    """Error performing item operation"""
    pass


class ValidationError(ShoppingListError):
    """Data validation error"""
    pass


class ConfigurationError(ShoppingListError):
    """Configuration error"""
    pass