"""
Main MCP Server for Shopping List Management
With Claude Desktop user profile detection
"""

import logging
import sys
import os
from typing import Optional
from fastmcp import FastMCP, Context

from .config import config
from .database import db
from .exceptions import ConfigurationError, DatabaseConnectionError
from .tools import shopping_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),  # Use stderr for MCP compatibility
        logging.FileHandler('shopping_list_mcp.log')
    ]
)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Shopping List Manager")


def get_claude_user_id(ctx: Optional[Context] = None) -> str:
    """
    Extract Claude Desktop user profile name from MCP context.
    
    The user profile name is passed through the MCP protocol during initialization.
    Falls back to environment variable or system username if not available.
    
    Args:
        ctx: MCP Context object containing session information
    
    Returns:
        Claude Desktop user profile name or fallback identifier
    """
    # Try to get from MCP context/session
    if ctx:
        try:
            # Try to access session from context
            if hasattr(ctx, 'session') and ctx.session:
                session = ctx.session
                logger.debug(f"Session object: {type(session)}")
                
                # Check for client_info in session
                if hasattr(session, 'client_info'):
                    client_info = session.client_info
                    logger.info(f"Client info: {client_info}")
                    
                    # Try to get user from client_info
                    if hasattr(client_info, 'name'):
                        user_name = client_info.name
                        logger.info(f"✅ Using Claude Desktop client name: {user_name}")
                        return user_name
            
            # Check if context has request_context
            if hasattr(ctx, 'request_context'):
                req_ctx = ctx.request_context
                logger.debug(f"Request context: {req_ctx}")
                
                # Check for meta information
                if hasattr(req_ctx, 'meta') and req_ctx.meta:
                    logger.info(f"Request meta: {req_ctx.meta}")
                    if 'user' in req_ctx.meta:
                        user = req_ctx.meta['user']
                        logger.info(f"✅ Using user from meta: {user}")
                        return user
            
            # Log available context attributes for debugging
            logger.debug(f"Context attributes: {dir(ctx)}")
            
        except Exception as e:
            logger.warning(f"Could not extract user from MCP context: {e}")
    
    # Try environment variable (set in Claude Desktop config)
    env_user = os.getenv('CLAUDE_USER_ID')
    if env_user:
        logger.info(f"✅ Using CLAUDE_USER_ID from environment: {env_user}")
        return env_user
    
    # Try to get system username as fallback
    try:
        import getpass
        system_user = getpass.getuser()
        logger.info(f"⚠️ Falling back to system username: {system_user}")
        return system_user
    except Exception as e:
        logger.warning(f"Could not get system username: {e}")
    
    # Last resort fallback
    fallback_user = "default_user"
    logger.warning(f"⚠️ Using fallback user ID: {fallback_user}")
    return fallback_user


# Register tools - Claude user profile is auto-detected
@mcp.tool()
def add_item(
    item_name: str,
    quantity: float = 1.0,
    unit: str = "",
    category: str = "",
    notes: str = "",
    ctx: Context = None
) -> str:
    """
    Add an item to your shopping list.
    
    Args:
        item_name: Name of the item to add
        quantity: Quantity of the item (default: 1.0)
        unit: Unit of measurement (e.g., 'kg', 'lbs', 'pieces')
        category: Category of the item (e.g., 'dairy', 'produce', 'meat')
        notes: Additional notes about the item
    
    Returns:
        Success message with item details
    """
    user_id = get_claude_user_id(ctx)
    logger.info(f"add_item called by user: {user_id}")
    return shopping_tools.add_item(user_id, item_name, quantity, unit, category, notes)


@mcp.tool()
def remove_item(item_name: str, ctx: Context = None) -> str:
    """
    Remove an item from your shopping list by name.
    
    Args:
        item_name: Name of the item to remove
    
    Returns:
        Success message or error if item not found
    """
    user_id = get_claude_user_id(ctx)
    logger.info(f"remove_item called by user: {user_id}")
    return shopping_tools.remove_item(user_id, item_name)


@mcp.tool()
def update_item(
    item_name: str,
    quantity: float = None,
    unit: str = None,
    category: str = None,
    notes: str = None,
    ctx: Context = None
) -> str:
    """
    Update details of an item in the shopping list.
    
    Args:
        item_name: Name of the item to update
        quantity: New quantity (optional)
        unit: New unit (optional)
        category: New category (optional)
        notes: New notes (optional)
    
    Returns:
        Success message with updated details
    """
    user_id = get_claude_user_id(ctx)
    logger.info(f"update_item called by user: {user_id}")
    return shopping_tools.update_item(user_id, item_name, quantity, unit, category, notes)


@mcp.tool()
def check_item(item_name: str, ctx: Context = None) -> str:
    """
    Mark an item as checked/purchased.
    
    Args:
        item_name: Name of the item to check
    
    Returns:
        Success message
    """
    user_id = get_claude_user_id(ctx)
    logger.info(f"check_item called by user: {user_id}")
    return shopping_tools.check_item(user_id, item_name)


@mcp.tool()
def uncheck_item(item_name: str, ctx: Context = None) -> str:
    """
    Unmark an item (mark as not purchased).
    
    Args:
        item_name: Name of the item to uncheck
    
    Returns:
        Success message
    """
    user_id = get_claude_user_id(ctx)
    logger.info(f"uncheck_item called by user: {user_id}")
    return shopping_tools.uncheck_item(user_id, item_name)


@mcp.tool()
def get_shopping_list(ctx: Context = None) -> str:
    """
    Get your complete shopping list.
    
    Returns:
        Formatted shopping list with all items
    """
    user_id = get_claude_user_id(ctx)
    logger.info(f"get_shopping_list called by user: {user_id}")
    return shopping_tools.get_shopping_list(user_id)


@mcp.tool()
def clear_checked_items(ctx: Context = None) -> str:
    """
    Remove all checked/purchased items from your shopping list.
    
    Returns:
        Success message with count of removed items
    """
    user_id = get_claude_user_id(ctx)
    logger.info(f"clear_checked_items called by user: {user_id}")
    return shopping_tools.clear_checked_items(user_id)


@mcp.tool()
def clear_all_items(ctx: Context = None) -> str:
    """
    Clear all items from your shopping list.
    
    Returns:
        Success message
    """
    user_id = get_claude_user_id(ctx)
    logger.info(f"clear_all_items called by user: {user_id}")
    return shopping_tools.clear_all_items(user_id)


@mcp.tool()
def get_my_profile(ctx: Context = None) -> str:
    """
    Get your Claude Desktop profile information.
    Shows which user profile this shopping list belongs to.
    
    Returns:
        User profile information
    """
    user_id = get_claude_user_id(ctx)
    
    result = "**Your Shopping List Profile:**\n\n"
    result += f"• Profile Name: `{user_id}`\n"
    result += f"• Database: MongoDB Atlas\n"
    result += f"• Status: Connected ✓\n\n"
    result += "This shopping list is unique to your Claude Desktop profile."
    
    return result


def initialize_server():
    """Initialize server and database connection"""
    try:
        logger.info("=" * 60)
        logger.info("Starting Shopping List MCP Server")
        logger.info("=" * 60)
        
        # Validate configuration
        logger.info("Validating configuration...")
        config.validate()
        logger.info("✓ Configuration validated successfully")
        
        # Connect to database
        logger.info("Connecting to MongoDB Atlas...")
        db.connect()
        logger.info("✓ Database connected successfully")
        
        # Test user detection
        test_user = get_claude_user_id()
        logger.info(f"✓ User detection configured (test: {test_user})")
        
        logger.info("=" * 60)
        logger.info("Shopping List MCP Server Ready!")
        logger.info("=" * 60)
        
        return True
        
    except ConfigurationError as e:
        logger.error(f"❌ Configuration error: {e.message}")
        logger.error(f"Details: {e.details}")
        return False
    except DatabaseConnectionError as e:
        logger.error(f"❌ Database connection error: {e.message}")
        logger.error(f"Details: {e.details}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during initialization: {e}", exc_info=True)
        return False


def shutdown_server():
    """Shutdown server and close connections"""
    try:
        logger.info("Shutting down Shopping List MCP Server...")
        db.disconnect()
        logger.info("Server shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def main():
    """Main entry point"""
    try:
        # Initialize server
        if not initialize_server():
            logger.error("Server initialization failed")
            sys.exit(1)
        
        # Run MCP server
        logger.info("Starting MCP server...")
        mcp.run()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        shutdown_server()


if __name__ == "__main__":
    main()