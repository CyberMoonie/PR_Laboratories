# Memory Scramble Game

Start the game server with:

```bash
python src/server.py <PORT> <BOARD_FILE>
```

### Examples

```bash
# Run with the ab.txt board on port 8080
python src/server.py 8080 boards/ab.txt

# Run with the perfect.txt board (emoji cards)
python src/server.py 8080 boards/perfect.txt

# Run with the zoom.txt board (vehicle emoji)
python src/server.py 8080 boards/zoom.txt
```

After starting the server, open your browser and navigate to:

```
http://localhost:8080/index.html
```

## Running Tests

Run all tests:

```bash
pytest tests/
```

Run specific test files:

```bash
# Test individual game rules
pytest tests/rule1b.py
pytest tests/rule2d.py
pytest tests/rule3a.py

# Test concurrent access
pytest tests/test_concurrent.py

# Run with verbose output
pytest tests/ -v
```

## Game Rules

The Memory Scramble game implements the following rules for flipping cards:

### First Card Rules (Rules 1-A through 1-D)

When a player flips their **first card** in a turn:

- **Rule 1-A: No card present**

  - If there's no card at the position (already matched and removed), the operation **fails** with an error.

- **Rule 1-B: Face-down card**

  - The card is **flipped face-up** and the player takes **control** of it.
  - The card shows as `my [CARD]` to that player.

- **Rule 1-C: Face-up, uncontrolled card**

  - The card is already face-up but no one controls it (from a previous non-matching pair).
  - The player takes **control** of it without needing to flip it.

- **Rule 1-D: Face-up, controlled card**
  - Another player currently controls this card.
  - The operation **waits** until the card becomes available (the other player releases it).
  - Once released, the waiting player takes control.

### Second Card Rules (Rules 2-A through 2-E)

When a player flips their **second card** in a turn:

- **Rule 2-A: No card present**

  - If there's no card at the position, the operation **fails**.
  - The player **releases control** of their first card.

- **Rule 2-B: Controlled card**

  - If another player controls the card, the operation **fails immediately** (no waiting).
  - The player **releases control** of their first card.

- **Rule 2-C: Face-down card**

  - The card is **flipped face-up**.
  - Then the game checks if it matches the first card.

- **Rule 2-D: Cards match**

  - If the two cards have the same value, the player **keeps control** of both cards.
  - Both cards remain face-up and controlled.
  - They will be **removed** when the player starts their next turn (Rule 3-A).

- **Rule 2-E: Cards don't match**
  - If the two cards have different values, the player **loses control** of both cards.
  - Both cards **remain face-up** (so players can memorize them).
  - They will be **turned face-down** when any player starts a new turn (Rule 3-B).

### Cleanup Rules (Rules 3-A and 3-B)

When a player starts a **new turn** (flips a first card):

- **Rule 3-A: Remove matched pairs**

  - If the player's previous turn resulted in a match (two controlled cards with the same value):
  - Both matched cards are **removed from the board** (show as `none`).

- **Rule 3-B: Turn down unmatched cards**
  - If the player's previous turn resulted in a non-match (two face-up cards without controllers):
  - Both unmatched cards are **turned face-down**.
  - This gives all players a chance to see and memorize the cards before they're hidden again.

### Concurrent Play

Multiple players can play simultaneously! The game ensures thread-safety and proper synchronization:

- Players can flip cards concurrently without conflicts
- If two players try to control the same card, one will wait (Rule 1-D)
- All game rules are enforced atomically to prevent race conditions
