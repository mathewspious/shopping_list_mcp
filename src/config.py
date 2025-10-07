"""
Configuration management for Shopping List MCP Server
"""

import os
from typing import Optional
from .exceptions import ConfigurationError


class Config:
    """Application configuration"""
    
    def __init__(self):
        self._mongodb_uri: Optional[str] = None
        self._db_name: str = "shopping_list_db"
        self._connection_timeout: int = 10000  # milliseconds
        self._server_selection_timeout: int = 5000  # milliseconds
        self._max_pool_size: int = 50
        self._min_pool_size: int = 10
        
    @property
    def mongodb_uri(self) -> str:
        """Get MongoDB connection URI"""
        if self._mongodb_uri is None:
            self._mongodb_uri = os.getenv("MONGODB_URI")
            
        if not self._mongodb_uri:
            raise ConfigurationError(
                "MONGODB_URI environment variable is not set",
                details={"env_var": "MONGODB_URI"}
            )
        
        return self._mongodb_uri
    
    @property
    def db_name(self) -> str:
        """Get database name"""
        return os.getenv("DB_NAME", self._db_name)
    
    @property
    def connection_timeout(self) -> int:
        """Get connection timeout in milliseconds"""
        return int(os.getenv("CONNECTION_TIMEOUT", self._connection_timeout))
    
    @property
    def server_selection_timeout(self) -> int:
        """Get server selection timeout in milliseconds"""
        return int(os.getenv("SERVER_SELECTION_TIMEOUT", self._server_selection_timeout))
    
    @property
    def max_pool_size(self) -> int:
        """Get maximum connection pool size"""
        return int(os.getenv("MAX_POOL_SIZE", self._max_pool_size))
    
    @property
    def min_pool_size(self) -> int:
        """Get minimum connection pool size"""
        return int(os.getenv("MIN_POOL_SIZE", self._min_pool_size))
    
    def validate(self) -> bool:
        """Validate configuration"""
        try:
            # Check MongoDB URI
            uri = self.mongodb_uri
            if not uri.startswith(("mongodb://", "mongodb+srv://")):
                raise ConfigurationError(
                    "Invalid MongoDB URI format",
                    details={"uri_prefix": uri[:20]}
                )
            
            # Check timeouts
            if self.connection_timeout <= 0:
                raise ConfigurationError("Connection timeout must be positive")
            
            if self.server_selection_timeout <= 0:
                raise ConfigurationError("Server selection timeout must be positive")
            
            # Check pool sizes
            if self.max_pool_size < self.min_pool_size:
                raise ConfigurationError(
                    "Max pool size must be greater than or equal to min pool size"
                )
            
            return True
            
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(f"Configuration validation failed: {str(e)}")


# Global configuration instance
config = Config()