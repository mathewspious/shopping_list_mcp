"""
Data models for Shopping List MCP Server
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
import uuid
from .exceptions import ValidationError


@dataclass
class ShoppingItem:
    """Shopping list item model"""
    name: str
    quantity: float = 1.0
    unit: str = ""
    category: str = ""
    notes: str = ""
    checked: bool = False
    item_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    added_at: datetime = field(default_factory=datetime.utcnow)
    checked_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate item data"""
        self.validate()
    
    def validate(self) -> None:
        """Validate item data"""
        if not self.name or not self.name.strip():
            raise ValidationError(
                "Item name cannot be empty",
                details={"field": "name"}
            )
        
        if self.quantity < 0:
            raise ValidationError(
                "Item quantity cannot be negative",
                details={"field": "quantity", "value": self.quantity}
            )
        
        if len(self.name) > 200:
            raise ValidationError(
                "Item name is too long (max 200 characters)",
                details={"field": "name", "length": len(self.name)}
            )
        
        if len(self.notes) > 500:
            raise ValidationError(
                "Item notes are too long (max 500 characters)",
                details={"field": "notes", "length": len(self.notes)}
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert datetime objects to ISO format
        data['added_at'] = self.added_at.isoformat() if self.added_at else None
        data['checked_at'] = self.checked_at.isoformat() if self.checked_at else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ShoppingItem':
        """Create from dictionary"""
        # Convert ISO format strings back to datetime
        if 'added_at' in data and isinstance(data['added_at'], str):
            data['added_at'] = datetime.fromisoformat(data['added_at'])
        if 'checked_at' in data and isinstance(data['checked_at'], str):
            data['checked_at'] = datetime.fromisoformat(data['checked_at'])
        
        return cls(**data)
    
    def mark_checked(self) -> None:
        """Mark item as checked/purchased"""
        self.checked = True
        self.checked_at = datetime.utcnow()
    
    def mark_unchecked(self) -> None:
        """Mark item as unchecked"""
        self.checked = False
        self.checked_at = None


@dataclass
class ShoppingList:
    """Shopping list model"""
    user_id: str
    list_name: str = "My Shopping List"
    items: List[ShoppingItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate list data"""
        self.validate()
    
    def validate(self) -> None:
        """Validate list data"""
        if not self.user_id or not self.user_id.strip():
            raise ValidationError(
                "User ID cannot be empty",
                details={"field": "user_id"}
            )
        
        if not self.list_name or not self.list_name.strip():
            raise ValidationError(
                "List name cannot be empty",
                details={"field": "list_name"}
            )
        
        if len(self.list_name) > 100:
            raise ValidationError(
                "List name is too long (max 100 characters)",
                details={"field": "list_name", "length": len(self.list_name)}
            )
    
    def add_item(self, item: ShoppingItem) -> None:
        """Add item to list"""
        self.items.append(item)
        self.updated_at = datetime.utcnow()
    
    def remove_item(self, item_name: str) -> bool:
        """Remove item from list by name (case-insensitive)"""
        initial_count = len(self.items)
        self.items = [
            item for item in self.items
            if item.name.lower() != item_name.lower()
        ]
        removed = len(self.items) < initial_count
        if removed:
            self.updated_at = datetime.utcnow()
        return removed
    
    def find_item(self, item_name: str) -> Optional[ShoppingItem]:
        """Find item by name (case-insensitive)"""
        for item in self.items:
            if item.name.lower() == item_name.lower():
                return item
        return None
    
    def get_unchecked_items(self) -> List[ShoppingItem]:
        """Get list of unchecked items"""
        return [item for item in self.items if not item.checked]
    
    def get_checked_items(self) -> List[ShoppingItem]:
        """Get list of checked items"""
        return [item for item in self.items if item.checked]
    
    def clear_checked_items(self) -> int:
        """Remove all checked items and return count"""
        checked_count = len(self.get_checked_items())
        self.items = self.get_unchecked_items()
        if checked_count > 0:
            self.updated_at = datetime.utcnow()
        return checked_count
    
    def clear_all_items(self) -> int:
        """Clear all items and return count"""
        item_count = len(self.items)
        self.items = []
        if item_count > 0:
            self.updated_at = datetime.utcnow()
        return item_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB"""
        return {
            "user_id": self.user_id,
            "list_name": self.list_name,
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ShoppingList':
        """Create from dictionary"""
        items_data = data.pop('items', [])
        items = [ShoppingItem.from_dict(item_data) for item_data in items_data]
        return cls(items=items, **data)


@dataclass
class User:
    """User model"""
    claude_user_id: str
    name: str = ""
    email: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Set default name if not provided"""
        if not self.name:
            self.name = f"User {self.claude_user_id[:8]}"
        self.validate()
    
    def validate(self) -> None:
        """Validate user data"""
        if not self.claude_user_id or not self.claude_user_id.strip():
            raise ValidationError(
                "Claude user ID cannot be empty",
                details={"field": "claude_user_id"}
            )
        
        if self.email and '@' not in self.email:
            raise ValidationError(
                "Invalid email format",
                details={"field": "email", "value": self.email}
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create from dictionary"""
        return cls(**data)