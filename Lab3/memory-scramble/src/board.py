"""
This module implements a thread-safe mutable board for the Memory Scramble game.
"""
import threading
import asyncio
from typing import Optional, List, Tuple, Callable
from dataclasses import dataclass
from enum import Enum


class CardState(Enum):
    """State of a card on the board."""
    FACE_DOWN = "down"
    FACE_UP = "up"


@dataclass
class Card:
    """Represents a card in the game.
    
    Attributes:
        value: The string value/picture on the card
        state: Whether the card is face up or face down
        controller: The player ID who controls this card, or None if no controller
    """
    value: str
    state: CardState
    controller: Optional[str]

    """
    example of card state would be "A", cardstate.FACE_UP/FACE_DOWN, "player1"/None
    """

@dataclass
class PlayerState:
    """Tracks the state of a player's current move.
    
    Attributes:
        first_card: Position of the first card flipped (row, col), or None
        second_card: Position of the second card flipped (row, col), or None
        matched: Whether the two cards matched
    """
    first_card: Optional[Tuple[int, int]] = None #position of first card (row,col)
    second_card: Optional[Tuple[int, int]] = None #position of second card (row,col)
    matched: bool = False #whether the two cards matched


class Board:
    """
    A mutable, thread-safe game board for Memory Scramble.
    
    The board is a grid of cards. Players can flip cards to try to find matching pairs.
    Multiple players can interact with the board concurrently.
    
    Abstraction Function:
        AF(rows, cols, grid, player_states, lock, change_event) = 
            A rows x cols game board where:
            - grid[r][c] represents the card at position (r, c), or None if no card
            - player_states tracks each player's current move state
            - lock ensures thread-safe access
            - change_event notifies watchers of board changes
    
    Representation Invariant:
        - rows > 0 and cols > 0
        - len(grid) == rows
        - for all rows r: len(grid[r]) == cols
        - for all cards: if card.controller is not None, then card.state == FACE_UP
        - for all player_states: if first_card is set, the card at that position 
          must be controlled by that player (unless it was removed)
    
    Safety from Rep Exposure:
        - All fields are private
        - grid is never returned directly; methods return copies or specific values
        - Card objects are not exposed; only their values and states are returned
        - All mutable operations are protected by locks
    """ 
    
    def __init__(self, rows: int, cols: int, cards: List[str]):
        """
        Create a new game board.
        
        Preconditions:
            - rows > 0 and cols > 0
            - len(cards) == rows * cols
        
        Postconditions:
            - Creates a board with all cards face down and no controllers
            - Rep invariant holds
        """
        if rows <= 0 or cols <= 0:
            raise ValueError("Board dimensions must be positive")
        if len(cards) != rows * cols:
            raise ValueError(f"Expected {rows * cols} cards, got {len(cards)}")
        
        self.rows = rows
        self.cols = cols
        self.grid: List[List[Optional[Card]]] = []
        self.player_states: dict[str, PlayerState] = {}
        self.lock = threading.RLock()
        self.change_event = asyncio.Event()
        
        # Initialize grid with face-down cards
        idx = 0
        for r in range(rows):
            row = []
            for c in range(cols):
                card = Card(value=cards[idx], state=CardState.FACE_DOWN, controller=None)
                row.append(card)
                idx += 1
            self.grid.append(row)
        
        self._check_rep()
    
    def _check_rep(self):
        """Check that the representation invariant holds."""
        assert self.rows > 0, "rows must be positive"
        assert self.cols > 0, "cols must be positive"
        assert len(self.grid) == self.rows, "grid must have correct number of rows"
        
        for r in range(self.rows):
            assert len(self.grid[r]) == self.cols, f"row {r} must have correct number of columns"
            for c in range(self.cols):
                card = self.grid[r][c]
                if card is not None:
                    # If a card has a controller, it must be face up
                    if card.controller is not None:
                        assert card.state == CardState.FACE_UP, \
                            f"controlled card at ({r},{c}) must be face up"
    
    @staticmethod
    async def parse_from_file(filename: str) -> 'Board':
        """
        Make a new board by parsing a file.
        
        Args:
            filename: Path to game board file
        
        Returns:
            A new board with the size and cards from the file
        
        Raises:
            ValueError: If the file cannot be read or is not a valid game board
        
        Preconditions:
            - filename is a valid file path
        
        Postconditions:
            - Returns a new Board matching the file specification
            - Board rep invariant holds
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = [line.rstrip('\r\n') for line in f]
            
            if not lines:
                raise ValueError("Empty file")
            
            # Parse dimensions
            dimensions = lines[0].split('x')
            if len(dimensions) != 2:
                raise ValueError("First line must be ROWxCOLUMN")
            
            rows = int(dimensions[0])
            cols = int(dimensions[1])
            
            # Parse cards
            cards = lines[1:]
            if len(cards) != rows * cols:
                raise ValueError(f"Expected {rows * cols} cards, got {len(cards)}")
            
            # Validate cards (non-empty, no whitespace)
            for i, card in enumerate(cards):
                if not card or card != card.strip() or ' ' in card or '\t' in card:
                    raise ValueError(f"Invalid card at line {i + 2}: '{card}'")
            
            return Board(rows, cols, cards)
        
        except FileNotFoundError:
            raise ValueError(f"File not found: {filename}")
        except (ValueError, IOError) as e:
            raise ValueError(f"Invalid board file: {e}")
    
    def get_state(self, player_id: str) -> str:
        """
        Get the current state of the board from a player's perspective.
        
        Args:
            player_id: ID of the player viewing the board
        
        Returns:
            String representation of the board state in the format:
            ROWxCOLUMN\n
            (none|down|up CARD|my CARD)\n
            ...
        
        Preconditions:
            - player_id is a non-empty string
        
        Postconditions:
            - Board state is unchanged
            - Returns a valid board state string
        """
        with self.lock:
            lines = [f"{self.rows}x{self.cols}"]
            
            for r in range(self.rows):
                for c in range(self.cols):
                    card = self.grid[r][c]
                    if card is None:
                        lines.append("none")
                    elif card.state == CardState.FACE_DOWN:
                        lines.append("down")
                    elif card.controller == player_id:
                        lines.append(f"my {card.value}")
                    else:
                        lines.append(f"up {card.value}")
            
            self._check_rep()
            return '\n'.join(lines) + '\n'
    
    async def flip(self, player_id: str, row: int, col: int) -> str:
        """
        Attempt to flip a card at the specified position.
        
        This implements the complete game rules for flipping cards, including:
        - First card: take control or wait for availability
        - Second card: match checking and control management
        - Cleanup: remove matched pairs or turn down unmatched cards
        
        Args:
            player_id: ID of the player making the flip
            row: Row number of the card 
            col: Column number of the card 
        
        Returns:
            The board state after the flip from the player's perspective
        
        Raises:
            ValueError: If the flip fails according to game rules
        
        Preconditions:
            - player_id is a non-empty string
            - 0 <= row < rows and 0 <= col < cols
        
        Postconditions:
            - If successful, card is flipped and game state updated per rules
            - If failed, raises ValueError and relinquishes control
            - Rep invariant holds
        """
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            raise ValueError(f"Invalid position ({row},{col})")
        
        # Ensure player state exists
        with self.lock:
            if player_id not in self.player_states:
                self.player_states[player_id] = PlayerState()
            player_state = self.player_states[player_id]
        
        # Determine if this is a first or second card flip
        # If player has already flipped two cards, this is a new first card
        # If player has flipped one card, this is a second card
        # If player has flipped no cards, this is a first card
        with self.lock:
            has_both_cards = player_state.first_card is not None and player_state.second_card is not None
            has_first_only = player_state.first_card is not None and player_state.second_card is None
            
            if has_both_cards or not has_first_only:
                # Either completed a previous turn (has both), or starting fresh (has neither)
                is_first_card = True
            else:
                # Has first card only, so this must be the second card
                is_first_card = False
        
        if is_first_card:
            return await self._flip_first_card(player_id, row, col)
        else:
            return await self._flip_second_card(player_id, row, col)
    
    async def _flip_first_card(self, player_id: str, row: int, col: int) -> str:
        """
        Handle flipping the first card of a pair
        
        Before flipping, cleanup previous turn if needed 
        Then attempt to flip and control the first card
        
        Preconditions:
            - Valid position (row, col)
            - player_id exists in player_states
        
        Postconditions:
            - Previous turn cleaned up (matched removed or unmatched turned down)
            - First card is flipped and controlled by player
            - player_state.first_card is set
        """
        # First, cleanup from previous turn
        with self.lock:
            player_state = self.player_states[player_id]
            
            # Rule 3-A: Remove matched pairs
            if player_state.matched and player_state.first_card and player_state.second_card:
                r1, c1 = player_state.first_card
                r2, c2 = player_state.second_card
                
                card1 = self.grid[r1][c1]
                card2 = self.grid[r2][c2]
                
                if card1 and card1.controller == player_id:
                    self.grid[r1][c1] = None
                if card2 and card2.controller == player_id:
                    self.grid[r2][c2] = None
                
                self.change_event.set()
                self.change_event.clear()
            
            # Rule 3-B: Turn down unmatched cards
            elif not player_state.matched:
                cards_turned_down = False
                
                if player_state.first_card:
                    r1, c1 = player_state.first_card
                    card1 = self.grid[r1][c1]
                    if card1 and card1.state == CardState.FACE_UP and card1.controller is None:
                        card1.state = CardState.FACE_DOWN
                        cards_turned_down = True
                
                if player_state.second_card:
                    r2, c2 = player_state.second_card
                    card2 = self.grid[r2][c2]
                    if card2 and card2.state == CardState.FACE_UP and card2.controller is None:
                        card2.state = CardState.FACE_DOWN
                        cards_turned_down = True
                
                if cards_turned_down:
                    self.change_event.set()
                    self.change_event.clear()
            
            # Reset player state
            player_state.first_card = None
            player_state.second_card = None
            player_state.matched = False
        
        # Now flip the first card
        while True:
            with self.lock:
                card = self.grid[row][col]
                
                # Rule 1-A: No card there
                if card is None:
                    self._check_rep()
                    raise ValueError(f"No card at position ({row},{col})")
                
                # Rule 1-B: Face down card - flip it up and take control
                if card.state == CardState.FACE_DOWN:
                    card.state = CardState.FACE_UP
                    card.controller = player_id
                    player_state.first_card = (row, col)
                    self.change_event.set()
                    self.change_event.clear()
                    self._check_rep()
                    return self.get_state(player_id)
                
                # Rule 1-C: Face up, no controller - take control
                if card.state == CardState.FACE_UP and card.controller is None:
                    card.controller = player_id
                    player_state.first_card = (row, col)
                    self._check_rep()
                    return self.get_state(player_id)
                
                # Rule 1-D: Face up, controlled by another player - wait
                if card.state == CardState.FACE_UP and card.controller is not None and card.controller != player_id:
                    event = self.change_event
            
            # Wait for the card to become available
            await event.wait()
    
    async def _flip_second_card(self, player_id: str, row: int, col: int) -> str:
        """
        Handle flipping the second card of a pair.
        Implements rules 2-A through 2-E.
        
        Preconditions:
            - player_state.first_card is set
            - Valid position (row, col)
        
        Postconditions:
            - Second card is flipped
            - If match: both cards controlled by player, matched=True
            - If no match: neither card controlled, matched=False
            - player_state.second_card is set
        """
        with self.lock:
            player_state = self.player_states[player_id]
            card = self.grid[row][col]
            
            # Rule 2-A: No card there - fail and relinquish first card
            if card is None:
                if player_state.first_card:
                    r1, c1 = player_state.first_card
                    card1 = self.grid[r1][c1]
                    if card1 and card1.controller == player_id:
                        card1.controller = None
                        self.change_event.set()
                        self.change_event.clear()
                
                player_state.first_card = None
                self._check_rep()
                raise ValueError(f"No card at position ({row},{col})")
            
            # Rule 2-B: Face up and controlled by another player - fail without waiting
            if card.state == CardState.FACE_UP and card.controller is not None and card.controller != player_id:
                if player_state.first_card:
                    r1, c1 = player_state.first_card
                    card1 = self.grid[r1][c1]
                    if card1 and card1.controller == player_id:
                        card1.controller = None
                        self.change_event.set()
                        self.change_event.clear()
                
                player_state.first_card = None
                self._check_rep()
                raise ValueError(f"Card at ({row},{col}) is controlled")
            
            # Rule 2-C: Face down - flip it up
            if card.state == CardState.FACE_DOWN:
                card.state = CardState.FACE_UP
                self.change_event.set()
                self.change_event.clear()
            
            # Now check for match
            r1, c1 = player_state.first_card
            card1 = self.grid[r1][c1]
            
            # Rule 2-D and 2-E: Check if cards match
            # flipping the same card twice is treated as no match
            is_same_position = (r1 == row and c1 == col)
            if card1 and card.value == card1.value and not is_same_position:
                # Match! Keep control of both
                card.controller = player_id
                player_state.second_card = (row, col)
                player_state.matched = True
            else:
                # No match - relinquish control of both
                if card1:
                    card1.controller = None
                card.controller = None
                player_state.second_card = (row, col)
                player_state.matched = False
                self.change_event.set()
                self.change_event.clear()
            
            self._check_rep()
            return self.get_state(player_id)
    
    async def map_cards(self, player_id: str, f: Callable[[str], str]) -> str:
        """
        Replace every card with f(card), maintaining pairwise consistency.
        
        Args:
            player_id: ID of the player applying the map
            f: Function that transforms card values
        
        Returns:
            The board state after the transformation from the player's perspective
        
        Preconditions:
            - f is a valid function from strings to strings
        
        Postconditions:
            - All cards replaced with f(card)
            - Cards that matched before still match after (same transformation)
            - Watchers are notified of the change
        """
        # Build a mapping of old values to new values
        value_map = {}
        
        with self.lock:
            # Find all unique card values
            for r in range(self.rows):
                for c in range(self.cols):
                    card = self.grid[r][c]
                    if card and card.value not in value_map:
                        value_map[card.value] = f(card.value)
            
            # Apply the transformation
            for r in range(self.rows):
                for c in range(self.cols):
                    card = self.grid[r][c]
                    if card:
                        card.value = value_map[card.value]
            
            self.change_event.set()
            self.change_event.clear()
            self._check_rep()
            return self.get_state(player_id)
    
    async def watch(self, player_id: str) -> str:
        """
        Wait for any change to the board, then return the updated state.
        
        Args:
            player_id: ID of the player watching the board
        
        Returns:
            The updated board state from the player's perspective
        
        Preconditions:
            - player_id is a non-empty string
        
        Postconditions:
            - Blocks until board changes
            - Returns updated board state
            - Board state is unchanged
        """
        event = self.change_event
        await event.wait()
        
        with self.lock:
            return self.get_state(player_id)
