# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based MUD (Multi-User Dungeon) server with a web-based client interface, organized using a modern Python src-layout structure.

### Directory Structure
```
pipeworks_mud_server/
├── src/mud_server/        # Main package
│   ├── api/               # FastAPI REST API
│   │   ├── server.py      # App initialization and startup
│   │   ├── routes.py      # All API endpoints
│   │   ├── models.py      # Pydantic request/response models
│   │   ├── auth.py        # Session validation and role tracking
│   │   ├── password.py    # Password hashing utilities (bcrypt)
│   │   └── permissions.py # Role-based access control system
│   ├── core/              # Game engine logic
│   │   ├── engine.py      # GameEngine class
│   │   └── world.py       # World, Room, Item classes
│   ├── db/                # Database layer
│   │   └── database.py    # SQLite operations
│   └── client/            # Frontend
│       └── app.py         # Gradio web interface
├── data/                  # Data files
│   ├── world_data.json    # Room and item definitions
│   └── mud.db             # SQLite database (generated)
├── docs/                  # Documentation
├── logs/                  # Server and client logs
└── tests/                 # Test files
```

### Architecture Components
- **FastAPI backend** (src/mud_server/api/) - RESTful API server on port 8000
- **Gradio frontend** (src/mud_server/client/) - Web interface on port 7860
- **Game engine** (src/mud_server/core/) - Core game logic and world management
- **SQLite database** (src/mud_server/db/) - Player state, sessions, and chat persistence
- **JSON world data** (data/) - Room and item definitions

## Common Commands

### Setup and Installation
```bash
# Setup virtual environment and dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize database (required before first run)
PYTHONPATH=src python3 -m mud_server.db.database
```

**Note**: The project uses src-layout structure, so `PYTHONPATH=src` is required when running modules directly. The `run.sh` script handles this automatically.

### Running the Server
```bash
# Start both server and client
./run.sh

# The script starts:
# - FastAPI server on http://0.0.0.0:8000
# - Gradio client on http://0.0.0.0:7860
# Press Ctrl+C to stop both services
```

### Development
```bash
# Run server only (for API development)
PYTHONPATH=src python3 src/mud_server/api/server.py

# Run client only (ensure server is running first)
PYTHONPATH=src python3 src/mud_server/client/app.py

# Check server health
curl http://localhost:8000/health

# Reset database (deletes all player data)
rm data/mud.db && PYTHONPATH=src python3 -m mud_server.db.database
```

### Environment Variables
```bash
# Configure server binding (defaults shown)
export MUD_HOST="0.0.0.0"
export MUD_PORT=8000
export MUD_SERVER_URL="http://localhost:8000"
```

## Architecture

### Three-Tier Design

**Client Layer (src/mud_server/client/app.py)**
- Gradio web interface with login, game, and help tabs
- Stateful session management using `gr.State`
- HTTP requests to backend API endpoints
- Real-time display updates for room, inventory, chat, and player status

**Server Layer (src/mud_server/api/)**
- **server.py**: FastAPI app initialization, CORS middleware, engine instance
- **routes.py**: All API endpoint definitions, command parsing
- **models.py**: Pydantic request/response models
- **auth.py**: Session validation and in-memory session tracking

**Game Engine Layer (src/mud_server/core/)**
- **world.py**: `World`, `Room`, `Item` classes - loads and manages data from JSON
- **engine.py**: `GameEngine` class - implements game logic (movement, inventory, chat)
- Database interface for persistence
- Room-based chat and player presence system

### Data Flow Patterns

**Session Management**
- Login creates UUID session_id stored in both database and server memory (auth.py:active_sessions)
- Sessions stored as `(username, role)` tuples for role-based authorization
- All API requests require valid session_id for authentication
- Sessions are not persisted to disk (lost on server restart)
- Session activity updated on each API call via `update_session_activity()`

**Player Movement**
1. Client sends command to `/command` endpoint
2. Server validates session and parses direction
3. Engine checks current room exits via `world.can_move()`
4. Database updated with new room via `set_player_room()`
5. Engine generates room description including items, players, exits
6. Broadcast messages sent (not yet implemented - see `_broadcast_to_room()`)

**Chat System**
- Messages stored in `chat_messages` table with room association
- Only messages from player's current room are retrieved
- Room-based isolation (players only see messages from their location)
- Chat retrieval limited to 20 recent messages by default

**Inventory Management**
- Stored as JSON array in players table
- Items picked up are NOT removed from room (intentional design)
- Items dropped are NOT added back to room
- Item matching uses case-insensitive name comparison

### Database Schema

**players table**
- `id` - Auto-increment primary key
- `username` (unique) - Player identifier
- `password_hash` - Bcrypt hashed password
- `role` - User role (player/worldbuilder/admin/superuser)
- `current_room` - Current location (room ID)
- `inventory` - JSON array of item IDs
- `is_active` - Account status (1=active, 0=banned/deactivated)
- Timestamps for created_at and last_login

**sessions table**
- `username` (unique) - One session per player
- `session_id` (unique) - UUID for API authentication
- Timestamps for connected_at and last_activity

**chat_messages table**
- `username` - Message sender
- `message` - Message content
- `room` - Room where message was sent
- `timestamp` - Message time

### World Data Structure

World is defined in `data/world_data.json`:
- **Rooms**: id, name, description, exits dict, items list
- **Items**: id, name, description
- Default spawn room is "spawn" (central hub)
- Exits are one-way unless explicitly defined in both directions

## Key Design Patterns

**Command Parsing** (routes.py:60-150)
- Commands split into `cmd` and `args`
- Directional shortcuts (n/s/e/w) mapped to full names
- Each command type delegates to specific engine method
- Returns `CommandResponse` with success flag and message

**Room Description Generation** (world.py:77-112)
- Combines room name, description, items, players, and exits
- Players list excludes requesting user
- Active players determined by session table JOIN
- Exit names resolved from room IDs

**Session Validation** (auth.py)
- All protected endpoints call `validate_session()`
- Returns `(username, role)` tuple for authorization
- Raises 401 HTTPException on invalid session
- Updates session activity timestamp on success
- `validate_session_with_permission()` checks specific permissions

## Important Considerations

**Item Pickup Behavior**
- Items remain in room after pickup (not removed from `data/world_data.json`)
- Multiple players can pick up same item
- Dropping items doesn't add them back to room
- This is intentional for the current proof-of-concept design

**Broadcast Messages**
- `_broadcast_to_room()` is stubbed (engine.py:185-189)
- Movement notifications not actually sent to other players
- Would require WebSocket implementation for real-time delivery

**Session Persistence**
- Sessions stored only in memory (`active_sessions` dict in auth.py)
- Server restart disconnects all players
- Database sessions table also tracks sessions but server memory is source of truth

**Concurrency**
- SQLite handles basic locking for concurrent writes
- No explicit transaction management or optimistic locking
- Suitable for ~50-100 concurrent players

**Authentication & Authorization**
- Password-based authentication with bcrypt hashing
- Role-based access control (RBAC) with 4 user types
- Session-based authentication with (username, role) tuples
- Default superuser created on database initialization

## Authentication & Security

### User Roles & Permissions

The system implements role-based access control (RBAC) with four user types:

**Player** (default for new registrations)
- Standard gameplay permissions
- Can move, chat, use inventory, explore the world
- No administrative or world-editing capabilities

**World Builder**
- All Player permissions
- Create and edit rooms (future feature)
- Create and modify items (future feature)
- Design world content without admin powers

**Admin**
- All Player permissions
- Limited world-editing capabilities
- Kick and ban users (future feature)
- View server logs (future feature)
- Cannot change user roles or manage superusers

**Superuser**
- Full system access
- Manage user accounts and roles
- Change passwords for any user
- Promote/demote users between roles
- Default superuser created on database initialization

### Default Credentials

⚠️ **IMPORTANT**: On first database initialization, a default superuser is created:

```
Username: admin
Password: admin123
```

**You should change this password immediately!** The system prints a warning on database initialization reminding you to change the default credentials.

### Password Requirements

- **Minimum length**: 8 characters
- **Hashing**: bcrypt with passlib (intentionally slow for security)
- **Storage**: Only password hashes stored in database, never plaintext
- **Verification**: Password checked against hash during login

### Registration

- Open registration enabled by default
- All new accounts default to **Player** role
- Username requirements: 2-20 characters, must be unique
- Password must be entered twice for confirmation
- Registration endpoint: `POST /register`

### Session Management

Sessions track both username and role:
- Session format: `(username: str, role: str)`
- Sessions stored in memory (lost on server restart)
- Session IDs are UUIDs (hard to guess)
- All API endpoints validate session and extract role
- Session activity updated on each API call

### Security Features

**Password Hashing** (password.py)
- Uses passlib with bcrypt scheme
- Bcrypt is intentionally slow (~100ms per hash) to prevent brute force
- Password hashes are one-way (cannot be reversed)

**Permission Checking** (permissions.py)
- Enum-based permission system with `Permission` class
- Role hierarchy enforced: Player < World Builder < Admin < Superuser
- Decorator functions for route protection: `@require_permission()`, `@require_role()`
- Permission inheritance: higher roles have all lower role permissions

**Account Management**
- Accounts can be deactivated/banned via `is_active` flag
- Deactivated accounts cannot login
- Role changes require superuser permission
- Users cannot elevate their own privileges

### Security Considerations

**Known Limitations**:
- Sessions not persisted (lost on restart)
- No session expiration time
- No rate limiting on login attempts
- No password complexity requirements (only minimum length)
- No email verification or password recovery
- No two-factor authentication

**Future Enhancements**:
- Add session expiration (timeout after inactivity)
- Implement rate limiting on auth endpoints
- Add password complexity requirements
- Force password change on first login for default admin
- Add audit logging for administrative actions
- Consider JWT tokens for stateless authentication

## File Responsibilities

### API Layer (src/mud_server/api/)
**server.py**
- FastAPI app initialization and configuration
- CORS middleware setup
- GameEngine instantiation
- Route registration
- Main entry point with uvicorn

**routes.py**
- All API endpoint definitions
- Command parsing and routing to game engine
- Request validation and error handling
- Authentication endpoints (login, register)

**models.py**
- Pydantic request models (LoginRequest, RegisterRequest, CommandRequest, etc.)
- Pydantic response models (LoginResponse, CommandResponse, StatusResponse)
- User management request/response models

**auth.py**
- In-memory session storage with (username, role) tuples
- Session validation logic returning both username and role
- Permission-based session validation
- Session activity tracking

**password.py**
- Password hashing with bcrypt via passlib
- `hash_password()` - Create bcrypt hash from plaintext
- `verify_password()` - Verify plaintext against hash

**permissions.py**
- Role enum (Player, WorldBuilder, Admin, Superuser)
- Permission enum (all permission types)
- ROLE_PERMISSIONS mapping roles to permission sets
- Helper functions: `has_permission()`, `can_manage_role()`
- Decorator functions: `require_permission()`, `require_role()`

### Core Layer (src/mud_server/core/)
**engine.py**
- GameEngine class with all game logic
- Player actions (movement, inventory, chat)
- Room navigation and validation
- Database integration

**world.py**
- World, Room, Item dataclasses
- JSON world data loading
- Room description generation
- Exit validation

### Database Layer (src/mud_server/db/)
**database.py**
- SQLite connection management
- Table schema definitions (players, sessions, chat_messages)
- CRUD operations for all entities
- JSON serialization for inventory
- Password verification and user authentication
- Role management functions (get/set role)
- Account status management (activate/deactivate)
- Default superuser creation on initialization

### Client Layer (src/mud_server/client/)
**app.py**
- Gradio interface components
- Tab layouts (login, register, game, help)
- Password input fields and validation
- Event handlers for buttons and inputs
- API request formatting and response handling
- Session state management including role display

### Data Files
**data/world_data.json**
- Static world definition (rooms and items)
- Not modified during gameplay
- Loaded once at engine initialization

**data/mud.db**
- SQLite database (generated at runtime)
- Stores players, sessions, chat messages
