"""
Shopping list service layer
Business logic for shopping list operations
"""

import logging
from typing import Optional, List, Tuple
from datetime import datetime

from ..models import ShoppingItem, ShoppingList
from ..database import db
from ..exceptions import (
    ItemNotFoundError,
    ItemOperationError,
    ValidationError,
    DatabaseError
)

logger = logging.getLogger(__name__)


class ShoppingListService:
    """Service for shopping list operations"""
    
    @staticmethod
    def add_item(
        user_id: str,
        item_name: str,
        quantity: float = 1.0,
        unit: str = "",
        category: str = "",
        notes: str = ""
    ) -> Tuple[ShoppingList, ShoppingItem]:
        """
        Add an item to user's shopping list
        
        Returns:
            Tuple of (updated_list, added_item)
        """
        try:
            # Validate and create item
            item = ShoppingItem(
                name=item_name.strip(),
                quantity=quantity,
                unit=unit.strip(),
                category=category.strip(),
                notes=notes.strip()
            )
            
            # Get or create shopping list
            shopping_list = db.get_or_create_shopping_list(user_id)
            
            # Add item to list
            shopping_list.add_item(item)
            
            # Save to database
            db.update_shopping_list(shopping_list)
            
            logger.info(f"Added item '{item_name}' to list for user {user_id}")
            return shopping_list, item
            
        except ValidationError as e:
            logger.error(f"Validation error adding item: {e}")
            raise
        except DatabaseError as e:
            logger.error(f"Database error adding item: {e}")
            raise ItemOperationError(
                f"Failed to add item: {str(e)}",
                details={"user_id": user_id, "item_name": item_name}
            )
        except Exception as e:
            logger.error(f"Unexpected error adding item: {e}")
            raise ItemOperationError(
                f"Failed to add item: {str(e)}",
                details={"user_id": user_id, "item_name": item_name, "error": str(e)}
            )
    
    @staticmethod
    def remove_item(user_id: str, item_name: str) -> Tuple[ShoppingList, bool]:
        """
        Remove an item from user's shopping list
        
        Returns:
            Tuple of (updated_list, was_removed)
        """
        try:
            shopping_list = db.get_shopping_list(user_id)
            
            if not shopping_list:
                raise ItemNotFoundError(
                    "Shopping list not found",
                    details={"user_id": user_id}
                )
            
            removed = shopping_list.remove_item(item_name.strip())
            
            if not removed:
                raise ItemNotFoundError(
                    f"Item '{item_name}' not found in shopping list",
                    details={"user_id": user_id, "item_name": item_name}
                )
            
            # Save to database
            db.update_shopping_list(shopping_list)
            
            logger.info(f"Removed item '{item_name}' from list for user {user_id}")
            return shopping_list, removed
            
        except (ItemNotFoundError, DatabaseError) as e:
            logger.error(f"Error removing item: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error removing item: {e}")
            raise ItemOperationError(
                f"Failed to remove item: {str(e)}",
                details={"user_id": user_id, "item_name": item_name, "error": str(e)}
            )
    
    @staticmethod
    def update_item(
        user_id: str,
        item_name: str,
        quantity: Optional[float] = None,
        unit: Optional[str] = None,
        category: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[ShoppingList, ShoppingItem]:
        """
        Update an item in user's shopping list
        
        Returns:
            Tuple of (updated_list, updated_item)
        """
        try:
            shopping_list = db.get_shopping_list(user_id)
            
            if not shopping_list:
                raise ItemNotFoundError(
                    "Shopping list not found",
                    details={"user_id": user_id}
                )
            
            item = shopping_list.find_item(item_name.strip())
            
            if not item:
                raise ItemNotFoundError(
                    f"Item '{item_name}' not found in shopping list",
                    details={"user_id": user_id, "item_name": item_name}
                )
            
            # Update fields if provided
            if quantity is not None:
                if quantity < 0:
                    raise ValidationError(
                        "Quantity cannot be negative",
                        details={"field": "quantity", "value": quantity}
                    )
                item.quantity = quantity
            
            if unit is not None:
                item.unit = unit.strip()
            
            if category is not None:
                item.category = category.strip()
            
            if notes is not None:
                item.notes = notes.strip()
            
            # Validate updated item
            item.validate()
            
            # Update timestamp
            shopping_list.updated_at = datetime.utcnow()
            
            # Save to database
            db.update_shopping_list(shopping_list)
            
            logger.info(f"Updated item '{item_name}' in list for user {user_id}")
            return shopping_list, item
            
        except (ItemNotFoundError, ValidationError, DatabaseError) as e:
            logger.error(f"Error updating item: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating item: {e}")
            raise ItemOperationError(
                f"Failed to update item: {str(e)}",
                details={"user_id": user_id, "item_name": item_name, "error": str(e)}
            )
    
    @staticmethod
    def check_item(user_id: str, item_name: str) -> Tuple[ShoppingList, ShoppingItem]:
        """
        Mark an item as checked/purchased
        
        Returns:
            Tuple of (updated_list, checked_item)
        """
        try:
            shopping_list = db.get_shopping_list(user_id)
            
            if not shopping_list:
                raise ItemNotFoundError(
                    "Shopping list not found",
                    details={"user_id": user_id}
                )
            
            item = shopping_list.find_item(item_name.strip())
            
            if not item:
                raise ItemNotFoundError(
                    f"Item '{item_name}' not found in shopping list",
                    details={"user_id": user_id, "item_name": item_name}
                )
            
            item.mark_checked()
            shopping_list.updated_at = datetime.utcnow()
            
            # Save to database
            db.update_shopping_list(shopping_list)
            
            logger.info(f"Checked item '{item_name}' in list for user {user_id}")
            return shopping_list, item
            
        except (ItemNotFoundError, DatabaseError) as e:
            logger.error(f"Error checking item: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error checking item: {e}")
            raise ItemOperationError(
                f"Failed to check item: {str(e)}",
                details={"user_id": user_id, "item_name": item_name, "error": str(e)}
            )
    
    @staticmethod
    def uncheck_item(user_id: str, item_name: str) -> Tuple[ShoppingList, ShoppingItem]:
        """
        Mark an item as unchecked
        
        Returns:
            Tuple of (updated_list, unchecked_item)
        """
        try:
            shopping_list = db.get_shopping_list(user_id)
            
            if not shopping_list:
                raise ItemNotFoundError(
                    "Shopping list not found",
                    details={"user_id": user_id}
                )
            
            item = shopping_list.find_item(item_name.strip())
            
            if not item:
                raise ItemNotFoundError(
                    f"Item '{item_name}' not found in shopping list",
                    details={"user_id": user_id, "item_name": item_name}
                )
            
            item.mark_unchecked()
            shopping_list.updated_at = datetime.utcnow()
            
            # Save to database
            db.update_shopping_list(shopping_list)
            
            logger.info(f"Unchecked item '{item_name}' in list for user {user_id}")
            return shopping_list, item
            
        except (ItemNotFoundError, DatabaseError) as e:
            logger.error(f"Error unchecking item: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error unchecking item: {e}")
            raise ItemOperationError(
                f"Failed to uncheck item: {str(e)}",
                details={"user_id": user_id, "item_name": item_name, "error": str(e)}
            )
    
    @staticmethod
    def get_shopping_list(user_id: str) -> ShoppingList:
        """
        Get user's shopping list
        
        Returns:
            ShoppingList object
        """
        try:
            shopping_list = db.get_or_create_shopping_list(user_id)
            logger.info(f"Retrieved shopping list for user {user_id}")
            return shopping_list
            
        except DatabaseError as e:
            logger.error(f"Error getting shopping list: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting shopping list: {e}")
            raise ItemOperationError(
                f"Failed to get shopping list: {str(e)}",
                details={"user_id": user_id, "error": str(e)}
            )
    
    @staticmethod
    def clear_checked_items(user_id: str) -> Tuple[ShoppingList, int]:
        """
        Remove all checked items from list
        
        Returns:
            Tuple of (updated_list, count_removed)
        """
        try:
            shopping_list = db.get_shopping_list(user_id)
            
            if not shopping_list:
                raise ItemNotFoundError(
                    "Shopping list not found",
                    details={"user_id": user_id}
                )
            
            count = shopping_list.clear_checked_items()
            
            # Save to database
            db.update_shopping_list(shopping_list)
            
            logger.info(f"Cleared {count} checked items from list for user {user_id}")
            return shopping_list, count
            
        except (ItemNotFoundError, DatabaseError) as e:
            logger.error(f"Error clearing checked items: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error clearing checked items: {e}")
            raise ItemOperationError(
                f"Failed to clear checked items: {str(e)}",
                details={"user_id": user_id, "error": str(e)}
            )
    
    @staticmethod
    def clear_all_items(user_id: str) -> Tuple[ShoppingList, int]:
        """
        Remove all items from list
        
        Returns:
            Tuple of (updated_list, count_removed)
        """
        try:
            shopping_list = db.get_shopping_list(user_id)
            
            if not shopping_list:
                raise ItemNotFoundError(
                    "Shopping list not found",
                    details={"user_id": user_id}
                )
            
            count = shopping_list.clear_all_items()
            
            # Save to database
            db.update_shopping_list(shopping_list)
            
            logger.info(f"Cleared all {count} items from list for user {user_id}")
            return shopping_list, count
            
        except (ItemNotFoundError, DatabaseError) as e:
            logger.error(f"Error clearing all items: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error clearing all items: {e}")
            raise ItemOperationError(
                f"Failed to clear all items: {str(e)}",
                details={"user_id": user_id, "error": str(e)}
            )
    
    @staticmethod
    def format_shopping_list(shopping_list: ShoppingList) -> str:
        """
        Format shopping list for display
        
        Returns:
            Formatted string representation
        """
        if not shopping_list.items:
            return "Your shopping list is empty."
        
        unchecked = shopping_list.get_unchecked_items()
        checked = shopping_list.get_checked_items()
        
        result = f"**{shopping_list.list_name}**\n\n"
        
        if unchecked:
            result += "**Items to Buy:**\n"
            for item in unchecked:
                qty_unit = f"{item.quantity} {item.unit}".strip()
                category = f" [{item.category}]" if item.category else ""
                notes = f" - {item.notes}" if item.notes else ""
                result += f"• {item.name} ({qty_unit}){category}{notes}\n"
        
        if checked:
            result += "\n**Purchased:**\n"
            for item in checked:
                qty_unit = f"{item.quantity} {item.unit}".strip()
                result += f"✓ {item.name} ({qty_unit})\n"
        
        result += f"\n**Total items:** {len(unchecked)} to buy, {len(checked)} purchased"
        
        return result


# Global service instance
shopping_list_service = ShoppingListService()