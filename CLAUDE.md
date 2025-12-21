# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains **The Undertaking**, a procedural, ledger-driven multiplayer interactive fiction system. The current codebase is a **proof-of-concept MUD server** that validates the technical architecture while working toward the full design vision.

### What is The Undertaking?

**The Undertaking** is a procedural accountability system where:
- **Characters are issued, not built** - Players receive complete, immutable goblins with uneven attributes, mandatory quirks, persistent failings, and inherited reputations
- **Failure is recorded as data** - Actions are resolved through multiple axes (Timing, Precision, Stability, Visibility, Interpretability, Recovery Cost) and recorded in an immutable ledger
- **Ledgers are truth, newspapers are stories** - Hard truth (deterministic ledger) is separated from soft truth (narrative interpretation)
- **Optimization is resisted** - No "best builds" or meta-gaming; success comes from understanding your specific goblin's flaws
- **Players become creators** - The journey from functionary → tinkerer → creator, eventually using the same tools as developers to build content

See `docs/README.md` for complete design documentation.

### Current Implementation Status

The current codebase implements:
- ✅ FastAPI backend with authentication and session management
- ✅ Gradio web interface for client interaction
- ✅ SQLite database for persistence
- ✅ Basic room navigation and chat system
- ✅ Role-based access control (Player/WorldBuilder/Admin/Superuser)
- ✅ JSON-based world data structure

The following features are designed but not yet implemented:
- ⏳ Character issuance system with quirks, failings, and useless bits
- ⏳ Axis-based action resolution engine
- ⏳ Ledger and newspaper (hard truth vs. soft truth)
- ⏳ Item quirks and frozen decision-making
- ⏳ Environmental quirks and room properties
- ⏳ Reputation system and blame attribution
- ⏳ Creator's toolkit (Gradio authoring environment)

This is a Python-based MUD (Multi-User Dungeon) server with a web-based client interface, organized using a modern Python src-layout structure.

### Design Documentation

Comprehensive design documentation is located in `docs/`:

- **`docs/README.md`** - Overview and guide to all design documents
- **`docs/the_undertaking_articulation.md`** - Core design articulation with five design pillars
- **`docs/the_undertaking_platform_vision.md`** - Unified platform vision (Engine + Toolkit)
- **`docs/undertaking_code_examples.md`** - Pseudo-code examples and database schema for full implementation
- **`docs/undertaking_supplementary_examples.md`** - Additional implementation details, content libraries, API examples

**Key Design Concepts:**
- **Character Issuance** - Goblins issued with immutable attributes, quirks, failings, useless bits
- **Axis-Based Resolution** - Six axes determine how actions fail (Timing, Precision, Stability, Visibility, Interpretability, Recovery Cost)
- **Ledger Layer (Hard Truth)** - Deterministic, replayable, never calls LLMs
- **Interpretation Layer (Soft Truth)** - Narrative generation, newspaper articles, context-dependent
- **Items as Frozen Decisions** - Items carry maker's quirks and habits
- **Creator's Toolkit** - Gradio authoring environment for player-created content

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
├── docs/                  # Design documentation for The Undertaking
│   ├── README.md          # Documentation overview
│   ├── the_undertaking_articulation.md
│   ├── the_undertaking_platform_vision.md
│   ├── undertaking_code_examples.md
│   └── undertaking_supplementary_examples.md
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

#### Current Implementation (Proof-of-Concept)

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

#### Planned Implementation (Full Design)

The full implementation will expand the database schema to include:

**characters table** - Issued goblin characters with immutable attributes
- Character identity (given_name, family_name, honorific)
- Seven core attributes (cunning, grip_strength, patience, spatial_sense, stamina, book_learning, luck_administrative)
- Quirk IDs (2-4 mandatory traits affecting resolution)
- Failing IDs (persistent deficiencies)
- Useless bit IDs (rarely helpful specializations)
- Reputation score and notes

**quirks table** - Mechanical traits with axis modifiers
**failings table** - Persistent deficiencies that apply even on success
**items table** - Items with quirks and maker profile (frozen decisions)
**item_quirks table** - Item-specific mechanical properties
**rooms table** - Locations with environmental quirks and difficulty
**ledger table** - Immutable action records (hard truth)
**newspaper table** - Narrative interpretations (soft truth)

See `docs/undertaking_code_examples.md` for complete schema definitions with all fields and relationships.

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

## The Undertaking: Planned Features

The current proof-of-concept validates the technical architecture. The following systems are designed and documented but not yet implemented:

### Character Issuance System

Instead of character creation, players receive **issued goblins**:

1. **Player chooses only sex** - everything else is procedurally generated
2. **Immutable once sealed** - no respeccing, no optimization
3. **Deliberately uneven** - some goblins are naturally better at certain things
4. **Quirks** (2-4 mandatory) - mechanical traits affecting resolution (e.g., "Panics When Watched")
5. **Failings** - persistent deficiencies that apply even on success (e.g., "Poor Numeracy")
6. **Useless Bits** - specializations that sound helpful but rarely are (e.g., "Expert in Obsolete Measurement Systems")
7. **Inherited Reputation** - bias before the player has done anything

See `docs/the_undertaking_articulation.md` sections on Character Issuance.

### Axis-Based Resolution Engine

Actions resolve through six axes, not dice rolls:

- **Timing** - When something happens in an action
- **Precision** - How exact an action must be
- **Stability** - How tolerant the system is to deviation
- **Visibility** - How observable an error is
- **Interpretability** - How outcomes are judged
- **Recovery Cost** - Effort to correct or undo

**How it works:**
1. Character quirks and failings bias the axes before action starts
2. Item quirks modify which axes matter most
3. Environmental quirks (room properties) further modify axes
4. Deterministic deviations calculated (seeded for replay)
5. Outcome determined: success, partial success, or failure
6. Contributing factors recorded in ledger

Attributes don't add success—they change **how bad failure looks**. High cunning doesn't prevent failure; it lets you blame someone else.

See `docs/undertaking_code_examples.md` Part 5 for resolution engine pseudo-code.

### Ledger and Newspaper (Two-Layer Truth)

**The Ledger (Hard Truth)**
- Deterministic, replayable from seed
- Never calls an LLM
- Records facts: what happened, which attributes were consulted, which quirks triggered
- Source of authority for all game logic
- Immutable once written

**The Newspaper (Soft Truth)**
- Consumes ledger facts and produces language
- May vary per context and contradict itself narratively
- Influenced by reputation, luck, and name
- Can be regenerated without affecting game state
- Provides narrative interpretation of failure

Example:
- **Ledger**: "Action: fishing. Outcome: failure. Contributing factors: [failing_patience_low, item_quirk_delayed_feedback]. Interpretation: avoidable. Blame weight: 0.8"
- **Newspaper**: "Third time this week a catch slipped from Grindlewick's pole. Locals blame impatience. Experts disagree."

### Items as Frozen Decisions

Items carry the maker's habits, shortcuts, grudges, and mistakes:

- **Maker Profile** - Item stores creator's attributes and quirks
- **Item Quirks** - Mechanical properties that interact with character quirks
- **Context-Dependent** - Same item fails differently for different goblins
- **No "Best" Items** - A pole with "Delayed Feedback" helps patient goblins but hurts impatient ones

A fishing pole made by a goblin with low patience might have a loose reel (made in a hurry) and delayed feedback (attempt to compensate). When you use that pole, you're using their solutions to their problems.

### Creator's Toolkit

The Gradio interface will expand into a player-facing authoring environment:

- **Quirk Studio** - Design new quirks and test mechanical effects
- **Item Forge** - Create items with unique properties and histories
- **Room Builder** - Design new rooms and link them to the world
- **NPC Scripter** - Write dialogue and behavior for custom NPCs
- **Newspaper Editor** - Write and publish interpretations of world events

Players progress: Functionary (survive) → Tinkerer (understand) → Creator (build)

### Implementation Roadmap

The proof-of-concept establishes the foundation. Planned implementation phases:

**Phase 1: Character Issuance** (extends current player system)
- Character generator with quirks, failings, useless bits
- Attribute distribution system
- Immutable character sealing

**Phase 2: Resolution Engine** (replaces simple command parsing)
- Axis-based resolution system
- Quirk and failing modifiers
- Deterministic outcome calculation

**Phase 3: Ledger System** (extends database)
- Ledger table for action records
- Contributing factors tracking
- Blame weight calculation

**Phase 4: Interpretation Layer** (adds narrative)
- Newspaper generation
- Reputation system
- Narrative tone based on character history

**Phase 5: Items and Rooms** (extends world system)
- Item quirks and maker profiles
- Environmental quirks for rooms
- Player-created content support

**Phase 6: Creator's Toolkit** (extends Gradio UI)
- Content authoring interfaces
- Player-facing scripting tools
- Content sharing and publication

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

## Development Guidelines for The Undertaking

When implementing features from the design vision, follow these principles:

### Programmatic vs. LLM Responsibilities

**Programmatic systems are AUTHORITATIVE for:**
- Character names (structure, uniqueness, cadence)
- Attributes and their distributions
- Quirks, failings, useless bits (IDs, triggers, mechanical effects)
- Items, item quirks, provenance
- Resolution math and axis calculations
- Ledger truth and contributing factors
- All game logic and state

**LLMs are NON-AUTHORITATIVE and used ONLY for:**
- Descriptions and flavor text
- Explanations and help text
- Tone and voice
- In-world paperwork language
- Newspaper copy and narrative interpretation
- NPC dialogue gloss
- "Tell the truth without lying" summaries

This separation prevents hallucinated mechanics, balance drift, and schema corruption.

### Key Implementation Principles

1. **Determinism First** - All game logic must be deterministic and replayable from seed
2. **Ledger is Truth** - The ledger is the source of authority; everything else is interpretation
3. **No Silent Failures** - All quirks, failings, and modifiers must be explicitly tracked
4. **Context Matters** - Same action fails differently based on character + item + room combination
5. **Resistance to Optimization** - Design choices should resist meta-gaming and optimization
6. **Gradual Disclosure** - Some quirks are hidden; players discover them through failure
7. **Blame Attribution** - Always track who/what is responsible for outcomes

### Database Migration Strategy

When implementing new tables (characters, quirks, items, ledger, newspaper):
- Keep existing `players` table for authentication and sessions
- Add `characters` table separately for goblin profiles
- Link characters to players via `account_id` field
- This allows multiple characters per account in the future
- Preserve backward compatibility during migration

### Testing Requirements

When implementing axis-based resolution:
- **Test determinism** - Same seed must produce same outcome
- **Test axis interactions** - Verify quirk stacking and cancellation
- **Test edge cases** - Zero attributes, maximum modifiers, conflicting quirks
- **Test replay** - Ledger entries must be replayable exactly
- **Test narrative variation** - Same ledger entry can produce different newspaper text

### Content Library Structure

Store quirks, failings, useless bits, and item quirks as JSON files in `data/`:
- `data/quirks.json` - Character quirks library
- `data/failings.json` - Failings library
- `data/useless_bits.json` - Useless specializations
- `data/item_quirks.json` - Item quirk library
- `data/environmental_quirks.json` - Room quirks

See `docs/undertaking_supplementary_examples.md` Part 1-3 for complete content library structures.

### Gradio UI Evolution

The Gradio interface should evolve in phases:
1. **Current**: Simple tabs for login, game, help
2. **Phase 1**: Add character issuance interface (limited choices)
3. **Phase 2**: Add action resolution feedback (show axis deviations)
4. **Phase 3**: Add newspaper view (narrative interpretation)
5. **Phase 4**: Add content authoring tabs (Creator's Toolkit)
6. **Phase 5**: Add content sharing and publication

Each phase should maintain backward compatibility with existing functionality.

### API Evolution

When extending the API for new features:
- Add new endpoints; don't break existing ones
- Version API routes if breaking changes are necessary (`/v2/...`)
- Maintain current `/command` endpoint for basic navigation during transition
- Add specialized endpoints for complex actions (e.g., `/actions/resolve`)
- Return both ledger data and narrative interpretation in responses

### Code Organization for New Systems

Suggested file organization for planned features:

```
src/mud_server/
├── core/
│   ├── character/
│   │   ├── issuer.py          # Character issuance system
│   │   ├── attributes.py      # Attribute generation
│   │   └── quirks.py          # Quirk application logic
│   ├── resolution/
│   │   ├── engine.py          # Axis-based resolution
│   │   ├── axes.py            # Axis definitions and math
│   │   └── modifiers.py       # Modifier application
│   ├── ledger/
│   │   ├── recorder.py        # Ledger writing
│   │   └── replay.py          # Deterministic replay
│   └── interpretation/
│       ├── newspaper.py       # Narrative generation
│       └── reputation.py      # Reputation tracking
```

This keeps new systems modular while preserving existing `engine.py` and `world.py` during transition.
