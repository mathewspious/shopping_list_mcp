"""
Shopping List MCP Server for Claude Desktop
Connects to MongoDB Atlas to manage user shopping lists
"""

import os
from datetime import datetime
from typing import Any
import uuid

from fastmcp import FastMCP, Context, get_current_context
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# Initialize FastMCP server
mcp = FastMCP("Shopping List Manager")

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = "shopping_list_db"

uri = ""

ctx = get_current_context()

# Initialize MongoDB client
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
users_collection = db.users
shopping_lists_collection = db.shopping_lists

# Create indexes
# users_collection.create_index("claude_user_id", unique=True)
# shopping_lists_collection.create_index("user_id")


def get_or_create_user(claude_user_id: str) -> dict:
    """Get existing user or create new one"""
    user = users_collection.find_one({"claude_user_id": claude_user_id})
    
    if not user:
        user_doc = {
            "claude_user_id": claude_user_id,
            "name": f"User {claude_user_id[:8]}",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        users_collection.insert_one(user_doc)
        user = user_doc
    
    return user


def get_or_create_shopping_list(user_id: str) -> dict:
    """Get existing shopping list or create new one"""
    shopping_list = shopping_lists_collection.find_one({"user_id": user_id})
    
    if not shopping_list:
        list_doc = {
            "user_id": user_id,
            "list_name": "My Shopping List",
            "items": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        shopping_lists_collection.insert_one(list_doc)
        shopping_list = list_doc
    
    return shopping_list


@mcp.tool()
def add_item(
    #user_id: str,
    item_name: str,
    quantity: float = 1.0,
    unit: str = "",
    category: str = "",
    notes: str = ""
) -> str:
    """
    Add an item to the user's shopping list.
    
    Args:
        #user_id: Claude user identifier
        item_name: Name of the item to add
        quantity: Quantity of the item (default: 1.0)
        unit: Unit of measurement (e.g., 'kg', 'lbs', 'pieces')
        category: Category of the item (e.g., 'dairy', 'produce', 'meat')
        notes: Additional notes about the item
    
    Returns:
        Success message with item details
    """
    user_id = ctx.client_id
    get_or_create_user(user_id)
    
    item = {
        "item_id": str(uuid.uuid4()),
        "name": item_name,
        "quantity": quantity,
        "unit": unit,
        "category": category,
        "notes": notes,
        "checked": False,
        "added_at": datetime.utcnow()
    }
    
    result = shopping_lists_collection.update_one(
        {"user_id": user_id},
        {
            "$push": {"items": item},
            "$set": {"updated_at": datetime.utcnow()}
        },
        upsert=True
    )
    
    return f"Added '{item_name}' (quantity: {quantity} {unit}) to your shopping list."


@mcp.tool()
def remove_item(item_name: str) -> str:
    """
    Remove an item from the user's shopping list by name.
    
    Args:
        #user_id: Claude user identifier
        item_name: Name of the item to remove
    
    Returns:
        Success message or error if item not found
    """
    result = shopping_lists_collection.update_one(
        {"user_id": ctx.client_id},
        {
            "$pull": {"items": {"name": {"$regex": f"^{item_name}$", "$options": "i"}}},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    if result.modified_count > 0:
        return f"Removed '{item_name}' from your shopping list."
    else:
        return f"Could not find '{item_name}' in your shopping list."


@mcp.tool()
def update_item(
    item_name: str,
    quantity: float = None,
    unit: str = None,
    category: str = None,
    notes: str = None,
) -> str:
    """
    Update details of an item in the shopping list.
    
    Args:
        #user_id: Claude user identifier
        item_name: Name of the item to update
        quantity: New quantity (optional)
        unit: New unit (optional)
        category: New category (optional)
        notes: New notes (optional)
    
    Returns:
        Success message with updated details
    """
    user_id=ctx.client_id
    shopping_list = shopping_lists_collection.find_one({"user_id": user_id})
    
    if not shopping_list:
        return "No shopping list found for this user."
    
    # Find the item
    item_found = False
    for item in shopping_list.get("items", []):
        if item["name"].lower() == item_name.lower():
            item_found = True
            # Update fields if provided
            if quantity is not None:
                item["quantity"] = quantity
            if unit is not None:
                item["unit"] = unit
            if category is not None:
                item["category"] = category
            if notes is not None:
                item["notes"] = notes
            break
    
    if not item_found:
        return f"Could not find '{item_name}' in your shopping list."
    
    # Save the updated list
    shopping_lists_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "items": shopping_list["items"],
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return f"Updated '{item_name}' in your shopping list."


@mcp.tool()
def check_item(item_name: str) -> str:
    """
    Mark an item as checked/purchased.
    
    Args:
        #user_id: Claude user identifier
        item_name: Name of the item to check
    
    Returns:
        Success message
    """
    result = shopping_lists_collection.update_one(
        {
            "user_id": ctx.client_id,
            "items.name": {"$regex": f"^{item_name}$", "$options": "i"}
        },
        {
            "$set": {
                "items.$.checked": True,
                "items.$.checked_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count > 0:
        return f"Marked '{item_name}' as purchased."
    else:
        return f"Could not find '{item_name}' in your shopping list."


@mcp.tool()
def uncheck_item(item_name: str) -> str:
    """
    Unmark an item (mark as not purchased).
    
    Args:
        #user_id: Claude user identifier
        item_name: Name of the item to uncheck
    
    Returns:
        Success message
    """
    result = shopping_lists_collection.update_one(
        {
            "user_id": ctx.client_id,
            "items.name": {"$regex": f"^{item_name}$", "$options": "i"}
        },
        {
            "$set": {
                "items.$.checked": False,
                "updated_at": datetime.utcnow()
            },
            "$unset": {"items.$.checked_at": ""}
        }
    )
    
    if result.modified_count > 0:
        return f"Unmarked '{item_name}'."
    else:
        return f"Could not find '{item_name}' in your shopping list."


@mcp.tool()
def get_shopping_list() -> str:
    """
    Get the user's complete shopping list.
    
    Args:
        #user_id: Claude user identifier
    
    Returns:
        Formatted shopping list with all items
    """
    user_id=ctx.client_id
    get_or_create_user(user_id)
    shopping_list = get_or_create_shopping_list(user_id)
    
    items = shopping_list.get("items", [])
    
    if not items:
        return "Your shopping list is empty."
    
    # Separate checked and unchecked items
    unchecked = [item for item in items if not item.get("checked", False)]
    checked = [item for item in items if item.get("checked", False)]
    
    result = f"**{shopping_list.get('list_name', 'Shopping List')}**\n\n"
    
    if unchecked:
        result += "**Items to Buy:**\n"
        for item in unchecked:
            qty_unit = f"{item['quantity']} {item['unit']}".strip()
            category = f" [{item['category']}]" if item.get('category') else ""
            notes = f" - {item['notes']}" if item.get('notes') else ""
            result += f"• {item['name']} ({qty_unit}){category}{notes}\n"
    
    if checked:
        result += "\n**Purchased:**\n"
        for item in checked:
            qty_unit = f"{item['quantity']} {item['unit']}".strip()
            result += f"✓ {item['name']} ({qty_unit})\n"
    
    result += f"\n**Total items:** {len(unchecked)} to buy, {len(checked)} purchased"
    
    return result


@mcp.tool()
def clear_checked_items() -> str:
    """
    Remove all checked/purchased items from the shopping list.
    
    Args:
        user_id: Claude user identifier
    
    Returns:
        Success message with count of removed items
    """
    user_id = ctx.client_id
    shopping_list = shopping_lists_collection.find_one({"user_id": user_id})
    
    if not shopping_list:
        return "No shopping list found."
    
    items = shopping_list.get("items", [])
    checked_count = sum(1 for item in items if item.get("checked", False))
    
    result = shopping_lists_collection.update_one(
        {"user_id": user_id},
        {
            "$pull": {"items": {"checked": True}},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return f"Removed {checked_count} purchased item(s) from your shopping list."


@mcp.tool()
def clear_all_items() -> str:
    """
    Clear all items from the shopping list.
    
    Args:
        user_id: Claude user identifier
    
    Returns:
        Success message
    """
    result = shopping_lists_collection.update_one(
        {"user_id": ctx.client_id},
        {
            "$set": {
                "items": [],
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return "Cleared all items from your shopping list."


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()