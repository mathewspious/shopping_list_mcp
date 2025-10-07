"""
User service layer
Business logic for user operations
"""

import logging
from ..models import User
from ..database import db
from ..exceptions import DatabaseError, UserCreationError

logger = logging.getLogger(__name__)


class UserService:
    """Service for user operations"""
    
    @staticmethod
    def get_or_create_user(claude_user_id: str) -> User:
        """
        Get existing user or create new one
        
        Args:
            claude_user_id: Claude user identifier
        
        Returns:
            User object
        """
        try:
            user = db.get_or_create_user(claude_user_id)
            logger.info(f"Retrieved/created user: {claude_user_id}")
            return user
            
        except (DatabaseError, UserCreationError) as e:
            logger.error(f"Error getting/creating user: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_or_create_user: {e}")
            raise DatabaseError(
                f"Failed to get or create user: {str(e)}",
                details={"user_id": claude_user_id, "error": str(e)}
            )


# Global service instance
user_service = UserService()