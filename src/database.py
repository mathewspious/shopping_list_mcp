"""
Database connection and operations for Shopping List MCP Server
"""

import logging
from typing import Optional, Dict, Any, List
from pymongo import MongoClient, ASCENDING
from pymongo.errors import (
    ConnectionFailure,
    ServerSelectionTimeoutError,
    OperationFailure,
    DuplicateKeyError,
    PyMongoError
)

from .config import config
from .exceptions import (
    DatabaseError,
    DatabaseConnectionError,
    UserNotFoundError,
    UserCreationError,
    ShoppingListNotFoundError
)
from .models import User, ShoppingList, ShoppingItem

logger = logging.getLogger(__name__)


class Database:
    """Database connection and operations manager"""
    
    def __init__(self):
        self._client: Optional[MongoClient] = None
        self._db = None
        self._users_collection = None
        self._shopping_lists_collection = None
        self._connected = False
    
    def connect(self) -> None:
        """Establish database connection"""
        try:
            logger.info("Connecting to MongoDB...")
            
            self._client = MongoClient(
                config.mongodb_uri,
                connectTimeoutMS=config.connection_timeout,
                serverSelectionTimeoutMS=config.server_selection_timeout,
                maxPoolSize=config.max_pool_size,
                minPoolSize=config.min_pool_size
            )
            
            # Test connection
            self._client.admin.command('ping')
            
            self._db = self._client[config.db_name]
            self._users_collection = self._db.users
            self._shopping_lists_collection = self._db.shopping_lists
            
            # Create indexes
            # self._create_indexes()
            
            self._connected = True
            logger.info("Successfully connected to MongoDB")
            
        except ServerSelectionTimeoutError as e:
            logger.error(f"MongoDB server selection timeout: {e}")
            raise DatabaseConnectionError(
                "Could not connect to MongoDB server (timeout)",
                details={"error": str(e)}
            )
        except ConnectionFailure as e:
            logger.error(f"MongoDB connection failure: {e}")
            raise DatabaseConnectionError(
                "Failed to connect to MongoDB",
                details={"error": str(e)}
            )
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise DatabaseConnectionError(
                f"Database connection error: {str(e)}",
                details={"error": str(e)}
            )
    
    def _create_indexes(self) -> None:
        """Create database indexes"""
        try:
            # Users collection indexes
            self._users_collection.create_index(
                [("claude_user_id", ASCENDING)],
                unique=True,
                name="claude_user_id_unique"
            )
            
            # Shopping lists collection indexes
            self._shopping_lists_collection.create_index(
                [("user_id", ASCENDING)],
                name="user_id_index"
            )
            
            logger.info("Database indexes created successfully")
            
        except OperationFailure as e:
            logger.error(f"Failed to create indexes: {e}")
            raise DatabaseError(
                "Failed to create database indexes",
                details={"error": str(e)}
            )
    
    def disconnect(self) -> None:
        """Close database connection"""
        if self._client:
            try:
                self._client.close()
                self._connected = False
                logger.info("Disconnected from MongoDB")
            except Exception as e:
                logger.error(f"Error disconnecting from MongoDB: {e}")
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._connected
    
    def ensure_connected(self) -> None:
        """Ensure database is connected"""
        if not self.is_connected():
            self.connect()
    
    # User operations
    
    def get_user(self, claude_user_id: str) -> Optional[User]:
        """Get user by Claude user ID"""
        try:
            self.ensure_connected()
            user_doc = self._users_collection.find_one(
                {"claude_user_id": claude_user_id}
            )
            
            if user_doc:
                user_doc.pop('_id', None)  # Remove MongoDB _id
                return User.from_dict(user_doc)
            
            return None
            
        except PyMongoError as e:
            logger.error(f"Error fetching user: {e}")
            raise DatabaseError(
                f"Failed to fetch user: {str(e)}",
                details={"user_id": claude_user_id, "error": str(e)}
            )
    
    def create_user(self, user: User) -> User:
        """Create new user"""
        try:
            self.ensure_connected()
            user_doc = user.to_dict()
            
            try:
                self._users_collection.insert_one(user_doc)
                logger.info(f"Created user: {user.claude_user_id}")
                return user
                
            except DuplicateKeyError:
                logger.warning(f"User already exists: {user.claude_user_id}")
                # Return existing user
                existing_user = self.get_user(user.claude_user_id)
                if existing_user:
                    return existing_user
                raise
                
        except DuplicateKeyError:
            raise UserCreationError(
                "User already exists",
                details={"user_id": user.claude_user_id}
            )
        except PyMongoError as e:
            logger.error(f"Error creating user: {e}")
            raise UserCreationError(
                f"Failed to create user: {str(e)}",
                details={"user_id": user.claude_user_id, "error": str(e)}
            )
    
    def get_or_create_user(self, claude_user_id: str) -> User:
        """Get existing user or create new one"""
        try:
            user = self.get_user(claude_user_id)
            if user:
                return user
            
            new_user = User(claude_user_id=claude_user_id)
            return self.create_user(new_user)
            
        except Exception as e:
            if isinstance(e, (DatabaseError, UserCreationError)):
                raise
            logger.error(f"Error in get_or_create_user: {e}")
            raise DatabaseError(
                f"Failed to get or create user: {str(e)}",
                details={"user_id": claude_user_id, "error": str(e)}
            )
    
    # Shopping list operations
    
    def get_shopping_list(self, user_id: str) -> Optional[ShoppingList]:
        """Get shopping list for user"""
        try:
            self.ensure_connected()
            list_doc = self._shopping_lists_collection.find_one(
                {"user_id": user_id}
            )
            
            if list_doc:
                list_doc.pop('_id', None)  # Remove MongoDB _id
                return ShoppingList.from_dict(list_doc)
            
            return None
            
        except PyMongoError as e:
            logger.error(f"Error fetching shopping list: {e}")
            raise DatabaseError(
                f"Failed to fetch shopping list: {str(e)}",
                details={"user_id": user_id, "error": str(e)}
            )
    
    def create_shopping_list(self, shopping_list: ShoppingList) -> ShoppingList:
        """Create new shopping list"""
        try:
            self.ensure_connected()
            list_doc = shopping_list.to_dict()
            
            self._shopping_lists_collection.insert_one(list_doc)
            logger.info(f"Created shopping list for user: {shopping_list.user_id}")
            return shopping_list
            
        except PyMongoError as e:
            logger.error(f"Error creating shopping list: {e}")
            raise DatabaseError(
                f"Failed to create shopping list: {str(e)}",
                details={"user_id": shopping_list.user_id, "error": str(e)}
            )
    
    def update_shopping_list(self, shopping_list: ShoppingList) -> ShoppingList:
        """Update existing shopping list"""
        try:
            self.ensure_connected()
            list_doc = shopping_list.to_dict()
            
            result = self._shopping_lists_collection.update_one(
                {"user_id": shopping_list.user_id},
                {"$set": list_doc},
                upsert=True
            )
            
            if result.matched_count == 0 and result.upserted_id is None:
                logger.warning(f"Shopping list not found for update: {shopping_list.user_id}")
                raise ShoppingListNotFoundError(
                    "Shopping list not found",
                    details={"user_id": shopping_list.user_id}
                )
            
            logger.info(f"Updated shopping list for user: {shopping_list.user_id}")
            return shopping_list
            
        except ShoppingListNotFoundError:
            raise
        except PyMongoError as e:
            logger.error(f"Error updating shopping list: {e}")
            raise DatabaseError(
                f"Failed to update shopping list: {str(e)}",
                details={"user_id": shopping_list.user_id, "error": str(e)}
            )
    
    def get_or_create_shopping_list(self, user_id: str) -> ShoppingList:
        """Get existing shopping list or create new one"""
        try:
            shopping_list = self.get_shopping_list(user_id)
            if shopping_list:
                return shopping_list
            
            new_list = ShoppingList(user_id=user_id)
            return self.create_shopping_list(new_list)
            
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            logger.error(f"Error in get_or_create_shopping_list: {e}")
            raise DatabaseError(
                f"Failed to get or create shopping list: {str(e)}",
                details={"user_id": user_id, "error": str(e)}
            )
    
    def delete_shopping_list(self, user_id: str) -> bool:
        """Delete shopping list for user"""
        try:
            self.ensure_connected()
            result = self._shopping_lists_collection.delete_one(
                {"user_id": user_id}
            )
            
            deleted = result.deleted_count > 0
            if deleted:
                logger.info(f"Deleted shopping list for user: {user_id}")
            
            return deleted
            
        except PyMongoError as e:
            logger.error(f"Error deleting shopping list: {e}")
            raise DatabaseError(
                f"Failed to delete shopping list: {str(e)}",
                details={"user_id": user_id, "error": str(e)}
            )


# Global database instance
db = Database()