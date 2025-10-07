"""
MCP tools for shopping list operations
"""

import logging
from typing import Optional

from ..services.user_service import user_service
from ..services.shopping_list_service import shopping_list_service
from ..exceptions import (
    ShoppingListError,
    ItemNotFoundError,
    ValidationError,
    DatabaseError
)

logger = logging.getLogger(__name__)


def add_item(
    user_id: str,
    item_name: str,
    quantity: float = 1.0,
    unit: str = "",
    category: str = "",
    notes: str = ""
) -> str:
    """
    Add an item to the user's shopping list.
    
    Args:
        user_id: Claude user identifier
        item_name: Name of the item to add
        quantity: Quantity of the item (default: 1.0)
        unit: Unit of measurement (e.g., 'kg', 'lbs', 'pieces')
        category: Category of the item (e.g., 'dairy', 'produce', 'meat')
        notes: Additional notes about the item
    
    Returns:
        Success message with item details
    """
    try:
        # Ensure user exists
        user_service.get_or_create_user(user_id)
        
        # Add item to shopping list
        shopping_list, item = shopping_list_service.add_item(
            user_id=user_id,
            item_name=item_name,
            quantity=quantity,
            unit=unit,
            category=category,
            notes=notes
        )
        
        qty_str = f"{quantity} {unit}".strip()
        return f"Added '{item_name}' ({qty_str}) to your shopping list."
        
    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        return f"Error: {e.message}"
    except DatabaseError as e:
        logger.error(f"Database error: {e.message}")
        return f"Database error: Unable to add item. Please try again."
    except Exception as e:
        logger.error(f"Unexpected error in add_item: {e}")
        return f"Error: Unable to add item. Please try again."


def remove_item(user_id: str, item_name: str) -> str:
    """
    Remove an item from the user's shopping list by name.
    
    Args:
        user_id: Claude user identifier
        item_name: Name of the item to remove
    
    Returns:
        Success message or error if item not found
    """
    try:
        shopping_list, removed = shopping_list_service.remove_item(user_id, item_name)
        return f"Removed '{item_name}' from your shopping list."
        
    except ItemNotFoundError as e:
        logger.warning(f"Item not found: {e.message}")
        return f"Could not find '{item_name}' in your shopping list."
    except DatabaseError as e:
        logger.error(f"Database error: {e.message}")
        return f"Database error: Unable to remove item. Please try again."
    except Exception as e:
        logger.error(f"Unexpected error in remove_item: {e}")
        return f"Error: Unable to remove item. Please try again."


def update_item(
    user_id: str,
    item_name: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    category: Optional[str] = None,
    notes: Optional[str] = None
) -> str:
    """
    Update details of an item in the shopping list.
    
    Args:
        user_id: Claude user identifier
        item_name: Name of the item to update
        quantity: New quantity (optional)
        unit: New unit (optional)
        category: New category (optional)
        notes: New notes (optional)
    
    Returns:
        Success message with updated details
    """
    try:
        shopping_list, item = shopping_list_service.update_item(
            user_id=user_id,
            item_name=item_name,
            quantity=quantity,
            unit=unit,
            category=category,
            notes=notes
        )
        
        return f"Updated '{item_name}' in your shopping list."
        
    except ItemNotFoundError as e:
        logger.warning(f"Item not found: {e.message}")
        return f"Could not find '{item_name}' in your shopping list."
    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        return f"Error: {e.message}"
    except DatabaseError as e:
        logger.error(f"Database error: {e.message}")
        return f"Database error: Unable to update item. Please try again."
    except Exception as e:
        logger.error(f"Unexpected error in update_item: {e}")
        return f"Error: Unable to update item. Please try again."


def check_item(user_id: str, item_name: str) -> str:
    """
    Mark an item as checked/purchased.
    
    Args:
        user_id: Claude user identifier
        item_name: Name of the item to check
    
    Returns:
        Success message
    """
    try:
        shopping_list, item = shopping_list_service.check_item(user_id, item_name)
        return f"Marked '{item_name}' as purchased."
        
    except ItemNotFoundError as e:
        logger.warning(f"Item not found: {e.message}")
        return f"Could not find '{item_name}' in your shopping list."
    except DatabaseError as e:
        logger.error(f"Database error: {e.message}")
        return f"Database error: Unable to check item. Please try again."
    except Exception as e:
        logger.error(f"Unexpected error in check_item: {e}")
        return f"Error: Unable to check item. Please try again."


def uncheck_item(user_id: str, item_name: str) -> str:
    """
    Unmark an item (mark as not purchased).
    
    Args:
        user_id: Claude user identifier
        item_name: Name of the item to uncheck
    
    Returns:
        Success message
    """
    try:
        shopping_list, item = shopping_list_service.uncheck_item(user_id, item_name)
        return f"Unmarked '{item_name}'."
        
    except ItemNotFoundError as e:
        logger.warning(f"Item not found: {e.message}")
        return f"Could not find '{item_name}' in your shopping list."
    except DatabaseError as e:
        logger.error(f"Database error: {e.message}")
        return f"Database error: Unable to uncheck item. Please try again."
    except Exception as e:
        logger.error(f"Unexpected error in uncheck_item: {e}")
        return f"Error: Unable to uncheck item. Please try again."


def get_shopping_list(user_id: str) -> str:
    """
    Get the user's complete shopping list.
    
    Args:
        user_id: Claude user identifier
    
    Returns:
        Formatted shopping list with all items
    """
    try:
        # Ensure user exists
        user_service.get_or_create_user(user_id)
        
        # Get shopping list
        shopping_list = shopping_list_service.get_shopping_list(user_id)
        
        # Format and return
        return shopping_list_service.format_shopping_list(shopping_list)
        
    except DatabaseError as e:
        logger.error(f"Database error: {e.message}")
        return "Database error: Unable to retrieve shopping list. Please try again."
    except Exception as e:
        logger.error(f"Unexpected error in get_shopping_list: {e}")
        return "Error: Unable to retrieve shopping list. Please try again."


def clear_checked_items(user_id: str) -> str:
    """
    Remove all checked/purchased items from the shopping list.
    
    Args:
        user_id: Claude user identifier
    
    Returns:
        Success message with count of removed items
    """
    try:
        shopping_list, count = shopping_list_service.clear_checked_items(user_id)
        return f"Removed {count} purchased item(s) from your shopping list."
        
    except ItemNotFoundError as e:
        logger.warning(f"Shopping list not found: {e.message}")
        return "No shopping list found."
    except DatabaseError as e:
        logger.error(f"Database error: {e.message}")
        return "Database error: Unable to clear items. Please try again."
    except Exception as e:
        logger.error(f"Unexpected error in clear_checked_items: {e}")
        return "Error: Unable to clear items. Please try again."


def clear_all_items(user_id: str) -> str:
    """
    Clear all items from the shopping list.
    
    Args:
        user_id: Claude user identifier
    
    Returns:
        Success message
    """
    try:
        shopping_list, count = shopping_list_service.clear_all_items(user_id)
        return "Cleared all items from your shopping list."
        
    except ItemNotFoundError as e:
        logger.warning(f"Shopping list not found: {e.message}")
        return "No shopping list found."
    except DatabaseError as e:
        logger.error(f"Database error: {e.message}")
        return "Database error: Unable to clear items. Please try again."
    except Exception as e:
        logger.error(f"Unexpected error in clear_all_items: {e}")
        return "Error: Unable to clear items. Please try again."