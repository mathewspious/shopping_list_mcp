# Shopping List MCP Server - Technical Documentation

## Overview

A Model Context Protocol (MCP) server that provides shopping list management capabilities for Claude Desktop. The server uses MongoDB Atlas for persistent storage and automatically detects the Claude Desktop user profile to maintain separate shopping lists per user.

## Architecture

### Technology Stack
- **Framework**: FastMCP 2.12.4+
- **Database**: MongoDB Atlas (via PyMongo)
- **Python Version**: 3.12.3+
- **Deployment**: FastMCP Cloud compatible

### Project Structure

```
shopping-list-mcp/
├── main.py                      # Entry point & module initialization
├── pyproject.toml              # Project dependencies & metadata
└── src/
    ├── __init__.py
    ├── server.py               # MCP server & tool definitions
    ├── config.py               # Configuration management
    ├── database.py             # MongoDB operations
    ├── models.py               # Data models
    ├── exceptions.py           # Custom exceptions
    ├── services/
    │   ├── __init__.py
    │   ├── user_service.py     # User business logic
    │   └── shopping_list_service.py  # Shopping list operations
    └── tools/
        ├── __init__.py
        └── shopping_tools.py   # MCP tool implementations
```

## Core Components

### 1. Data Models (`models.py`)

#### ShoppingItem
Represents a single item in a shopping list.

**Fields:**
- `name` (str): Item name (max 200 chars, required)
- `quantity` (float): Item quantity (default: 1.0, must be ≥ 0)
- `unit` (str): Unit of measurement (e.g., "kg", "lbs")
- `category` (str): Item category (e.g., "dairy", "produce")
- `notes` (str): Additional notes (max 500 chars)
- `checked` (bool): Purchase status
- `item_id` (str): Unique identifier (UUID)
- `added_at` (datetime): Timestamp when added
- `checked_at` (datetime): Timestamp when checked

**Key Methods:**
- `validate()`: Validates item data constraints
- `mark_checked()`: Marks item as purchased
- `mark_unchecked()`: Marks item as not purchased
- `to_dict()` / `from_dict()`: Serialization for MongoDB

#### ShoppingList
Represents a user's complete shopping list.

**Fields:**
- `user_id` (str): Claude Desktop user identifier
- `list_name` (str): List name (default: "My Shopping List", max 100 chars)
- `items` (List[ShoppingItem]): List of shopping items
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last modification timestamp

**Key Methods:**
- `add_item(item)`: Adds item to list
- `remove_item(item_name)`: Removes item by name (case-insensitive)
- `find_item(item_name)`: Finds item by name (case-insensitive)
- `get_unchecked_items()`: Returns items to buy
- `get_checked_items()`: Returns purchased items
- `clear_checked_items()`: Removes all purchased items
- `clear_all_items()`: Removes all items

#### User
Represents a Claude Desktop user.

**Fields:**
- `claude_user_id` (str): Unique Claude Desktop profile identifier
- `name` (str): Display name (auto-generated if empty)
- `email` (str): Email address (optional, validated)
- `created_at` (datetime): Account creation timestamp
- `updated_at` (datetime): Last update timestamp

### 2. Database Layer (`database.py`)

#### Database Class
Manages MongoDB connection and CRUD operations.

**Connection Management:**
- `connect()`: Establishes MongoDB Atlas connection
- `disconnect()`: Closes connection
- `is_connected()`: Checks connection status
- `ensure_connected()`: Reconnects if disconnected

**Configuration:**
- Connection timeout: 10 seconds
- Server selection timeout: 5 seconds
- Connection pool: 10-50 connections

**User Operations:**
- `get_user(claude_user_id)`: Retrieves user by ID
- `create_user(user)`: Creates new user
- `get_or_create_user(claude_user_id)`: Gets or creates user

**Shopping List Operations:**
- `get_shopping_list(user_id)`: Retrieves user's list
- `create_shopping_list(shopping_list)`: Creates new list
- `update_shopping_list(shopping_list)`: Updates existing list
- `get_or_create_shopping_list(user_id)`: Gets or creates list
- `delete_shopping_list(user_id)`: Deletes user's list

**Global Instance:**
```python
from src.database import db
```

### 3. Configuration (`config.py`)

#### Config Class
Manages environment-based configuration.

**Environment Variables:**
- `MONGODB_URI` (required): MongoDB Atlas connection string
- `DB_NAME` (optional): Database name (default: "shopping_list_db")
- `CONNECTION_TIMEOUT`: Connection timeout in ms (default: 10000)
- `SERVER_SELECTION_TIMEOUT`: Server selection timeout in ms (default: 5000)
- `MAX_POOL_SIZE`: Maximum connections (default: 50)
- `MIN_POOL_SIZE`: Minimum connections (default: 10)

**Validation:**
- Validates MongoDB URI format
- Ensures positive timeout values
- Validates pool size constraints

**Global Instance:**
```python
from src.config import config
```

### 4. Service Layer

#### UserService (`user_service.py`)
Handles user-related business logic.

**Methods:**
- `get_or_create_user(claude_user_id)`: Ensures user exists

#### ShoppingListService (`shopping_list_service.py`)
Handles shopping list business logic.

**Methods:**
- `add_item(user_id, item_name, ...)`: Adds item to list
- `remove_item(user_id, item_name)`: Removes item
- `update_item(user_id, item_name, ...)`: Updates item properties
- `check_item(user_id, item_name)`: Marks item as purchased
- `uncheck_item(user_id, item_name)`: Unmarks item
- `get_shopping_list(user_id)`: Retrieves list
- `clear_checked_items(user_id)`: Removes purchased items
- `clear_all_items(user_id)`: Removes all items
- `format_shopping_list(shopping_list)`: Formats list for display

### 5. MCP Server (`server.py`)

#### User Detection
The `get_claude_user_id()` function extracts the Claude Desktop user profile:

1. **Primary**: MCP Context session data (`ctx.session.client_info.name`)
2. **Secondary**: Environment variable (`CLAUDE_USER_ID`)
3. **Fallback**: System username (`getpass.getuser()`)
4. **Last Resort**: "default_user"

#### Registered MCP Tools

All tools automatically detect the Claude Desktop user profile via the `Context` parameter.

1. **add_item**(item_name, quantity=1.0, unit="", category="", notes="")
   - Adds item to shopping list
   - Returns: Success message

2. **remove_item**(item_name)
   - Removes item by name
   - Returns: Success or error message

3. **update_item**(item_name, quantity=None, unit=None, category=None, notes=None)
   - Updates item properties
   - Returns: Success message

4. **check_item**(item_name)
   - Marks item as purchased
   - Returns: Success message

5. **uncheck_item**(item_name)
   - Unmarks item
   - Returns: Success message

6. **get_shopping_list**()
   - Retrieves formatted shopping list
   - Returns: Formatted list or "empty" message

7. **clear_checked_items**()
   - Removes all purchased items
   - Returns: Count of removed items

8. **clear_all_items**()
   - Clears entire list
   - Returns: Success message

9. **get_my_profile**()
   - Shows user profile information
   - Returns: Profile details

### 6. Exception Handling (`exceptions.py`)

#### Exception Hierarchy

```
ShoppingListError (base)
├── DatabaseError
│   └── DatabaseConnectionError
├── UserNotFoundError
├── UserCreationError
├── ShoppingListNotFoundError
├── ItemNotFoundError
├── ItemOperationError
├── ValidationError
└── ConfigurationError
```

All exceptions include:
- `message`: Human-readable error description
- `details`: Dictionary with additional context

## Data Flow

### Adding an Item

```
User Request → MCP Tool (add_item)
    ↓
Extract user_id from Context
    ↓
shopping_tools.add_item()
    ↓
user_service.get_or_create_user()
    ↓
shopping_list_service.add_item()
    ↓
Create ShoppingItem (validates)
    ↓
db.get_or_create_shopping_list()
    ↓
shopping_list.add_item()
    ↓
db.update_shopping_list()
    ↓
MongoDB Atlas (persisted)
    ↓
Success message returned
```

### Retrieving Shopping List

```
User Request → MCP Tool (get_shopping_list)
    ↓
Extract user_id from Context
    ↓
shopping_tools.get_shopping_list()
    ↓
shopping_list_service.get_shopping_list()
    ↓
db.get_or_create_shopping_list()
    ↓
MongoDB Atlas query
    ↓
shopping_list_service.format_shopping_list()
    ↓
Formatted markdown returned
```

## Deployment

### Local Development

1. **Set environment variables:**
```bash
export MONGODB_URI="mongodb+srv://user:pass@cluster.mongodb.net/"
```

2. **Install dependencies:**
```bash
pip install -e .
```

3. **Run server:**
```bash
python main.py
```

### FastMCP Cloud Deployment

The project is configured for FastMCP Cloud deployment:

- `main.py` exposes the `mcp` instance
- Auto-initialization on import (not in `__main__`)
- MongoDB connection established during module import

## Configuration for Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "shopping-list": {
      "command": "python",
      "args": ["/path/to/main.py"],
      "env": {
        "MONGODB_URI": "mongodb+srv://user:pass@cluster.mongodb.net/"
      }
    }
  }
}
```

## Database Schema

### Users Collection
```javascript
{
  claude_user_id: String (unique),
  name: String,
  email: String,
  created_at: DateTime,
  updated_at: DateTime
}
```

### Shopping Lists Collection
```javascript
{
  user_id: String (indexed),
  list_name: String,
  items: [{
    name: String,
    quantity: Number,
    unit: String,
    category: String,
    notes: String,
    checked: Boolean,
    item_id: String (UUID),
    added_at: DateTime,
    checked_at: DateTime
  }],
  created_at: DateTime,
  updated_at: DateTime
}
```

## Error Handling

### User-Facing Messages
- Tools return user-friendly error messages
- Database errors are sanitized
- Validation errors include specific field information

### Logging
- All operations logged with appropriate levels
- Errors include stack traces for debugging
- User actions tracked for audit

## Security Considerations

1. **User Isolation**: Each Claude Desktop profile maintains separate data
2. **Input Validation**: All user inputs validated before database operations
3. **Connection Security**: MongoDB Atlas uses TLS encryption
4. **No Sensitive Data**: Shopping items contain no PII
5. **Error Sanitization**: Database details not exposed to users

## Performance Characteristics

- **Connection Pooling**: 10-50 concurrent connections
- **Case-Insensitive Search**: Item lookup uses lowercase comparison
- **Atomic Updates**: Shopping list updates are atomic
- **Lazy Connection**: Database connects on first use

## Limitations

1. **Single List Per User**: Each user has one shopping list
2. **No Sharing**: Lists cannot be shared between users
3. **No History**: Item history not maintained after removal
4. **No Sync**: No real-time synchronization (request-based)

## Future Enhancements

- Multiple lists per user
- List sharing capabilities
- Purchase history tracking
- Recipe integration
- Store location mapping
- Price tracking
- Barcode scanning support

## Testing

### Unit Tests
Run tests with pytest:
```bash
pytest tests/
```

### Manual Testing
Use the MCP Inspector or Claude Desktop to test tools:
```python
# Add item
add_item("Milk", 2, "liters", "dairy")

# Get list
get_shopping_list()

# Check item
check_item("Milk")

# Clear purchased
clear_checked_items()
```

## Troubleshooting

### Connection Issues
- Verify `MONGODB_URI` is set correctly
- Check MongoDB Atlas IP whitelist
- Ensure network connectivity

### User Detection Issues
- Check Claude Desktop configuration
- Verify `CLAUDE_USER_ID` environment variable
- Review server logs for user detection

### Data Not Persisting
- Confirm database connection is established
- Check MongoDB Atlas cluster status
- Review error logs for database errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Support

For issues or questions:
- Check the troubleshooting section
- Review server logs in stderr
- Open an issue on GitHub

---

**Version**: 1.0.0  
**Last Updated**: October 2025  
**Author**: Shopping List MCP Team  
**License**: See LICENSE file