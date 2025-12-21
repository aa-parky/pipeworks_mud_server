"""Main game engine with game logic."""

from typing import List, Optional, Tuple
from mud_server.core.world import World
from mud_server.db import database


class GameEngine:
    """Main game engine managing game logic."""

    def __init__(self):
        self.world = World()
        database.init_database()

    def login(self, username: str, password: str, session_id: str) -> Tuple[bool, str, Optional[str]]:
        """
        Handle player login.

        Args:
            username: Username
            password: Plain text password
            session_id: Session ID to create

        Returns:
            Tuple of (success, message, role)
            role is None if login fails
        """
        # Check if player exists
        if not database.player_exists(username):
            return False, "Invalid username or password.", None

        # Verify password
        if not database.verify_password_for_user(username, password):
            return False, "Invalid username or password.", None

        # Check if player is active (not banned)
        if not database.is_player_active(username):
            return False, "This account has been deactivated. Please contact an administrator.", None

        # Get player role
        role = database.get_player_role(username)
        if not role:
            return False, "Failed to retrieve account information.", None

        # Create session
        if not database.create_session(username, session_id):
            return False, "Failed to create session.", None

        # Get current room
        room = database.get_player_room(username)
        if not room:
            room = "spawn"
            database.set_player_room(username, room)

        # Generate welcome message
        message = f"Welcome, {username}!\n"
        message += f"Role: {role.capitalize()}\n\n"
        message += self.world.get_room_description(room, username)

        return True, message, role

    def logout(self, username: str) -> bool:
        """Handle player logout."""
        return database.remove_session(username)

    def move(self, username: str, direction: str) -> Tuple[bool, str]:
        """Handle player movement."""
        current_room = database.get_player_room(username)
        if not current_room:
            return False, "You are not in a valid room."

        can_move, destination = self.world.can_move(current_room, direction)
        if not can_move:
            return False, f"You cannot move {direction} from here."

        # Update player room
        if not database.set_player_room(username, destination):
            return False, "Failed to move."

        # Get room description
        room_desc = self.world.get_room_description(destination, username)
        message = f"You move {direction}.\n{room_desc}"

        # Notify other players
        self._broadcast_to_room(
            current_room, f"{username} leaves {direction}.", exclude=username
        )
        self._broadcast_to_room(
            destination, f"{username} arrives from {self._opposite_direction(direction)}.", exclude=username
        )

        return True, message

    def chat(self, username: str, message: str) -> Tuple[bool, str]:
        """Handle player chat."""
        room = database.get_player_room(username)
        if not room:
            return False, "You are not in a valid room."

        if not database.add_chat_message(username, message, room):
            return False, "Failed to send message."

        return True, f"You say: {message}"

    def yell(self, username: str, message: str) -> Tuple[bool, str]:
        """Yell to current room and all adjoining rooms."""
        current_room_id = database.get_player_room(username)
        if not current_room_id:
            return False, "You are not in a valid room."

        # Get current room to find adjoining rooms
        current_room = self.world.get_room(current_room_id)
        if not current_room:
            return False, "Invalid room."

        # Add [YELL] prefix to message
        yell_message = f"[YELL] {message}"

        # Send to current room
        if not database.add_chat_message(username, yell_message, current_room_id):
            return False, "Failed to send message."

        # Send to all adjoining rooms
        for direction, room_id in current_room.exits.items():
            database.add_chat_message(username, yell_message, room_id)

        return True, f"You yell: {message}"

    def whisper(self, username: str, target: str, message: str) -> Tuple[bool, str]:
        """Send a private whisper to a specific player in the same room."""
        import logging
        logger = logging.getLogger(__name__)

        sender_room = database.get_player_room(username)
        logger.info(f"Whisper: {username} in room {sender_room} attempting to whisper to {target}")

        if not sender_room:
            logger.warning(f"Whisper failed: {username} not in valid room")
            return False, "You are not in a valid room."

        # Check if target player exists
        if not database.player_exists(target):
            logger.warning(f"Whisper failed: target {target} does not exist")
            return False, f"Player '{target}' does not exist."

        # Check if target is online (has an active session)
        active_players = database.get_active_players()
        logger.info(f"Active players: {active_players}")
        if target not in active_players:
            logger.warning(f"Whisper failed: target {target} not online")
            return False, f"Player '{target}' is not online."

        # Check if target is in the same room
        target_room = database.get_player_room(target)
        logger.info(f"Target {target} is in room {target_room}")
        if target_room != sender_room:
            logger.warning(f"Whisper failed: {target} in {target_room}, sender in {sender_room}")
            return False, f"Player '{target}' is not in this room."

        # Add whisper message with recipient (include both sender and target for clarity)
        whisper_message = f"[WHISPER: {username} → {target}] {message}"
        result = database.add_chat_message(username, whisper_message, sender_room, recipient=target)
        logger.info(f"Whisper message save result: {result}")

        if not result:
            logger.error("Failed to save whisper to database")
            return False, "Failed to send whisper."

        logger.info(f"Whisper successful: {username} -> {target}: {message}")
        return True, f"You whisper to {target}: {message}"

    def get_room_chat(self, username: str, limit: int = 20) -> str:
        """Get recent chat from current room, filtered for this user."""
        room = database.get_player_room(username)
        if not room:
            return "No messages."

        messages = database.get_room_messages(room, limit, username=username)
        if not messages:
            return "[No messages in this room yet]"

        chat_text = "[Recent messages]:\n"
        for msg in messages:
            chat_text += f"{msg['username']}: {msg['message']}\n"
        return chat_text

    def get_inventory(self, username: str) -> str:
        """Get player inventory."""
        inventory = database.get_player_inventory(username)
        if not inventory:
            return "Your inventory is empty."

        inv_text = "Your inventory:\n"
        for item_id in inventory:
            item = self.world.get_item(item_id)
            if item:
                inv_text += f"  - {item.name}\n"
        return inv_text

    def pickup_item(self, username: str, item_name: str) -> Tuple[bool, str]:
        """Pick up an item from the current room."""
        room_id = database.get_player_room(username)
        if not room_id:
            return False, "You are not in a valid room."

        room = self.world.get_room(room_id)
        if not room:
            return False, "Invalid room."

        # Find matching item
        matching_item = None
        for item_id in room.items:
            item = self.world.get_item(item_id)
            if item and item.name.lower() == item_name.lower():
                matching_item = item_id
                break

        if not matching_item:
            return False, f"There is no '{item_name}' here."

        # Add to inventory
        inventory = database.get_player_inventory(username)
        if matching_item not in inventory:
            inventory.append(matching_item)
            database.set_player_inventory(username, inventory)

        item = self.world.get_item(matching_item)
        return True, f"You picked up the {item.name}."

    def drop_item(self, username: str, item_name: str) -> Tuple[bool, str]:
        """Drop an item from inventory."""
        inventory = database.get_player_inventory(username)

        # Find matching item in inventory
        matching_item = None
        for item_id in inventory:
            item = self.world.get_item(item_id)
            if item and item.name.lower() == item_name.lower():
                matching_item = item_id
                break

        if not matching_item:
            return False, f"You don't have a '{item_name}'."

        # Remove from inventory
        inventory.remove(matching_item)
        database.set_player_inventory(username, inventory)

        item = self.world.get_item(matching_item)
        return True, f"You dropped the {item.name}."

    def look(self, username: str) -> str:
        """Look around the current room."""
        room_id = database.get_player_room(username)
        if not room_id:
            return "You are not in a valid room."

        return self.world.get_room_description(room_id, username)

    def get_active_players(self) -> List[str]:
        """Get list of active players."""
        return database.get_active_players()

    def _broadcast_to_room(
        self, room_id: str, message: str, exclude: Optional[str] = None
    ):
        """Broadcast a message to all players in a room."""
        # This would be handled by the server's message queue
        pass

    @staticmethod
    def _opposite_direction(direction: str) -> str:
        """Get the opposite direction."""
        opposites = {"north": "south", "south": "north", "east": "west", "west": "east"}
        return opposites.get(direction.lower(), "somewhere")
