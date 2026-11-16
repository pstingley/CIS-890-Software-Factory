# Tic-Tac-Toe Game Specification

## Overview

This specification describes the implemented behavior of a terminal-based Tic-Tac-Toe game written in Python. The implementation is a complete, playable two-player game with move validation, win detection, draw detection, and multi-game session support.

**Source File Examined:** [`tictactoe.py`](./tictactoe.py)

---

## 1. Board Representation and Initial State

### 1.1 Board Data Structure
- **Type:** Dictionary with integer keys (1–9) mapping to values {None, 'X', 'O'}
- **Positions:** Numbered 1–9, representing a 3×3 grid:
  ```
  1 | 2 | 3
  --+---+--
  4 | 5 | 6
  --+---+--
  7 | 8 | 9
  ```
- **Function:** `initialize_board()` (lines 8–9)
- **Return Value:** Dictionary with all positions set to None

### 1.2 Initial State
- All 9 squares are empty (None values)
- Board is created once per game session
- **Function:** Called at the start of each game in `play_game()` (line 109)

### 1.3 Board Display
- **Function:** `display_board(board)` (lines 12–26)
- Shows current board with player marks ('X', 'O') or empty square numbers
- Format: 3×3 grid with pipe (|) and dash (--) separators
- Prints to stdout with trailing newlines

### 1.4 Board Reset (Multi-game Feature)
- **Function:** `reset_board(board)` (lines 29–32)
- Clears the board between games by setting all positions to None
- Called implicitly when `initialize_board()` is called in new game sessions

---

## 2. Players and Turn Management

### 2.1 Players
- **Player 1:** 'X' (always plays first)
- **Player 2:** 'O' (always plays second)
- Both are human-controlled via terminal input

### 2.2 Starting Player
- Game always begins with player 'X'
- **Function:** `play_game()` (line 111) initializes `current_player = 'X'`

### 2.3 Turn Alternation
- After each valid move and board update, players alternate
- **Function:** `play_game()` (line 138) swaps players:
  ```python
  current_player, other_player = other_player, current_player
  ```
- Turn alternation occurs only after:
  1. Move is validated and placed
  2. Board is displayed
  3. No win is detected
  4. No draw is detected

### 2.4 Turn Sequence Example
1. X makes move → board displayed → check win/draw → if no end, switch to O
2. O makes move → board displayed → check win/draw → if no end, switch to X
3. ... continues until win or draw

---

## 3. Input Format, Validation, and Invalid Move Handling

### 3.1 Input Format
- **Source:** Terminal input via `input()` function
- **Expected:** Single string containing either:
  - A digit 1–9 (the square number for the move)
  - The character 'q' or 'Q' (quit command)
- **Function:** `get_player_move(board, player)` (lines 35–62)

### 3.2 Move Validation
- **Function:** `validate_move(board, move)` (lines 65–74)
- **Validation Checks:**
  - R1: `move` must be an integer
  - R2: `move` must be in range [1, 9]
  - R3: Square at position `move` must be unoccupied (board[move] == None)
- **Return:** True if all checks pass; False otherwise
- **Note:** Function does not validate the input parsing step; it assumes an integer input

### 3.3 Input Parsing and Error Handling
- **Function:** `get_player_move()` (lines 35–62) wraps validation
- **Parsing Errors:**
  - **Quit Command:** If user enters 'q' (case-insensitive), raise `QuitGame()` exception (lines 51–52)
  - **Non-numeric Input:** Caught by `int()` conversion (line 54); prints error message, prompts again (lines 60–61)
  - **Out-of-Range:** Caught by `validate_move()` check; prints error message (line 58)
  - **Occupied Square:** Caught by occupancy check in `validate_move()`; prints error message (line 57)

### 3.4 Input Validation Loop
- Continues indefinitely until:
  - A valid move is returned
  - 'q' is entered (raises `QuitGame`)
- Player sees error message and is re-prompted

### 3.5 Examples of Accepted Moves
- Input "5" when square 5 is empty → accepted, returns 5
- Input "1" on first turn (square 1 empty) → accepted, returns 1
- Input "q" at any time → raises `QuitGame` exception

### 3.6 Examples of Rejected Moves
- Input "10" → error message: "Invalid move. Please enter a number between 1 and 9."
- Input "0" → error message: "Invalid move. Please enter a number between 1 and 9."
- Input "-1" → error message: "Invalid move. Please enter a number between 1 and 9."
- Input "5" when square 5 is occupied → error message: "Square 5 is already occupied. Try again."
- Input "abc" → error message: "Invalid input. Please enter a number between 1 and 9, or 'q' to quit."
- Input "1.5" → error message: "Invalid input. Please enter a number between 1 and 9, or 'q' to quit."

---

## 4. Move Placement

### 4.1 Place Move Function
- **Function:** `place_move(board, move, player)` (lines 77–86)
- **Action:** Sets `board[move] = player` (line 85)
- **Precondition:** Move must be validated before calling (caller responsibility)
- **Side Effect:** Modifies the board dictionary in-place
- **Return:** None

### 4.2 Move Placement Sequence
In `play_game()` (lines 121–122):
```
1. Get valid move from player
2. Call place_move(board, move, current_player)
3. Update board[move] to current player's mark
4. Display updated board
```

---

## 5. Win Conditions and Win Detection

### 5.1 Winning Combinations
- **Function:** `check_win(board, player)` (lines 89–120)
- **Winning Combinations (8 total):**
  - Rows: [1,2,3], [4,5,6], [7,8,9]
  - Columns: [1,4,7], [2,5,8], [3,6,9]
  - Diagonals: [1,5,9], [3,5,7]

### 5.2 Win Detection Logic
- After each move, `check_win(board, current_player)` is called (line 127)
- Returns True if current player occupies all three squares in any winning combination
- Specifically: `all(board[square] == player for square in combination)` for any combination

### 5.3 Win Termination
- When a win is detected:
  - Print message: "🎉 Player {player} wins! Congratulations!" (line 128)
  - Break from game loop
  - Game session ends
  - Return to play-again prompt

### 5.4 Win Examples
- **Example 1:** X plays positions 1, 5, 9 (diagonal) → X wins
- **Example 2:** O plays positions 1, 4, 7 (column) → O wins
- **Example 3:** X plays positions 2, 5, 8 (column) → X wins

---

## 6. Draw Conditions and Game Termination

### 6.1 Draw Detection
- **Function:** `check_draw(board)` (lines 123–130)
- **Condition:** All 9 squares are occupied (filled with 'X' or 'O')
- **Implementation:** `all(board[i] is not None for i in range(1, 10))`
- **Check Timing:** After move placement and win check (line 131)

### 6.2 Draw Termination
- When draw is detected:
  - Print message: "It's a draw! Well played both!" (line 132)
  - Break from game loop
  - Game session ends
  - Return to play-again prompt

### 6.3 Draw Example
- Board fills completely with no three-in-a-row for either player → draw

---

## 7. Game Flow and Termination

### 7.1 Single Game Session (`play_game()`)
1. Initialize empty board
2. Set `current_player = 'X'`
3. Display board
4. **Game Loop:**
   - Get valid move from current player
   - Place move on board
   - Display updated board
   - Check for current player's win → if yes, print win message and break
   - Check for draw → if yes, print draw message and break
   - Alternate to other player
5. Game loop ends on win, draw, or `QuitGame` exception
6. If `QuitGame` raised, print "Game quit by player. Goodbye!" and re-raise

### 7.2 Multi-Game Session (`main()`)
1. Print welcome message and rules
2. **Session Loop:**
   - Call `play_game()`
   - If `QuitGame` exception caught, print goodbye and break session
   - If game ended normally (win/draw):
     - Call `play_again_prompt()`
     - If yes, loop back to step 2
     - If no, print goodbye and break

### 7.3 Quit Behavior
- **Trigger:** Player enters 'q' during move input
- **Handler:** `QuitGame` exception raised in `get_player_move()` (line 52)
- **Propagation:**
  - Caught in `play_game()` (lines 119–120)
  - Prints "Game quit by player. Goodbye!"
  - Re-raised to caller
  - Caught in `main()` (lines 156–157)
  - Prints "Thanks for playing! Goodbye!"
  - Breaks session loop

### 7.4 Exit Behavior
- After `main()` completes, Python script terminates
- Script execution ends after all games and quit operations

---

## 8. Play Again Prompt

### 8.1 Function and Behavior
- **Function:** `play_again_prompt()` (lines 133–142)
- Called after each game ends (win or draw, not quit)
- Prompts: "Do you want to play again? (yes/no):"

### 8.2 Valid Responses
- **Accept play again:** 'yes', 'y', 'YES', 'Y', etc. (case-insensitive) → returns True
- **Decline and exit:** 'no', 'n', 'NO', 'N', etc. (case-insensitive) → returns False
- **Invalid input:** Any other input → prints "Please enter 'yes' or 'no'." and re-prompts

### 8.3 Input Loop
- Continues indefinitely until valid response received

---

## 9. Exception Handling

### 9.1 QuitGame Exception
- **Definition:** Custom exception class (lines 161–163)
- **Purpose:** Signal player quit during input
- **Raised by:** `get_player_move()` when 'q' is entered
- **Caught by:** `play_game()` and `main()`
- **Effect:** Terminates current game and optionally exits session

---

## 10. Numbered Requirements Mapping

| Req # | Description | Source File | Function | Lines |
|-------|-------------|-------------|----------|-------|
| R1 | Board is 3×3 grid with positions 1–9 | tictactoe.py | initialize_board, display_board | 8–26 |
| R2 | Initial state is all squares empty | tictactoe.py | initialize_board | 8–9 |
| R3 | Display shows current state with marks or numbers | tictactoe.py | display_board | 12–26 |
| R4 | Player X always starts first | tictactoe.py | play_game | 111 |
| R5 | Players alternate after each valid move | tictactoe.py | play_game | 138 |
| R6 | Input must be integer 1–9 or 'q' | tictactoe.py | get_player_move, validate_move | 35–74 |
| R7 | Occupied squares cannot be played | tictactoe.py | validate_move | 71 |
| R8 | Invalid moves trigger re-prompt with error message | tictactoe.py | get_player_move | 57–61 |
| R9 | 'q' command raises QuitGame exception | tictactoe.py | get_player_move | 51–52 |
| R10 | Eight winning combinations exist (3 rows, 3 cols, 2 diags) | tictactoe.py | check_win | 95–107 |
| R11 | Win is checked immediately after move placement | tictactoe.py | play_game | 127 |
| R12 | Winning player is announced; game ends | tictactoe.py | play_game | 127–128 |
| R13 | Draw occurs when board is full and no win | tictactoe.py | play_game | 131–132 |
| R14 | Draw results in game termination | tictactoe.py | play_game | 131–132 |
| R15 | Quit terminates current game with message | tictactoe.py | play_game, main | 119–120, 156–157 |
| R16 | Play-again prompt appears after each game | tictactoe.py | play_again_prompt | 133–142 |
| R17 | Valid responses are 'yes'/'y' or 'no'/'n' (case-insensitive) | tictactoe.py | play_again_prompt | 135 |
| R18 | Multiple games can be played in one session | tictactoe.py | main | 155–162 |

---

## 11. Concrete Examples

### 11.1 Accepted Move Sequence
```
Starting board:
  1 | 2 | 3
 --+---+--
  4 | 5 | 6
 --+---+--
  7 | 8 | 9

Player X's turn: Enter move (1-9) or 'q' to quit: 5
Move 5 accepted.

Board after X moves to 5:
  1 | 2 | 3
 --+---+--
  4 | X | 6
 --+---+--
  7 | 8 | 9

Player O's turn: Enter move (1-9) or 'q' to quit: 1
Move 1 accepted.

Board after O moves to 1:
  O | 2 | 3
 --+---+--
  4 | X | 6
 --+---+--
  7 | 8 | 9
```

### 11.2 Rejected Move Examples
```
Scenario 1: Out of range
Player X's turn: Enter move (1-9) or 'q' to quit: 10
Error: Invalid move. Please enter a number between 1 and 9.
Player X's turn: Enter move (1-9) or 'q' to quit: 5

Scenario 2: Occupied square
Player X's turn: Enter move (1-9) or 'q' to quit: 5
Error: Square 5 is already occupied. Try again.
Player X's turn: Enter move (1-9) or 'q' to quit: 3

Scenario 3: Non-numeric input
Player X's turn: Enter move (1-9) or 'q' to quit: abc
Error: Invalid input. Please enter a number between 1 and 9, or 'q' to quit.
Player X's turn: Enter move (1-9) or 'q' to quit: 7
```

### 11.3 Quit Example
```
Player X's turn: Enter move (1-9) or 'q' to quit: q
Game quit by player. Goodbye!

Thanks for playing! Goodbye!
[Script terminates]
```

### 11.4 Win Example
```
Board state:
  X | X | 3
 --+---+--
  4 | O | 6
 --+---+--
  7 | 8 | O

Player X's turn: Enter move (1-9) or 'q' to quit: 3
Board after X moves to 3:
  X | X | X
 --+---+--
  4 | O | 6
 --+---+--
  7 | 8 | O

🎉 Player X wins! Congratulations!

Do you want to play again? (yes/no): yes
```

### 11.5 Draw Example
```
Board state:
  X | O | X
 --+---+--
  X | O | O
 --+---+--
  2 | X | 9

Player O's turn: Enter move (1-9) or 'q' to quit: 2
Board after O moves to 2:
  X | O | X
 --+---+--
  X | O | O
 --+---+--
  O | X | 9

Player X's turn: Enter move (1-9) or 'q' to quit: 9
Board after X moves to 9:
  X | O | X
 --+---+--
  X | O | O
 --+---+--
  O | X | X

It's a draw! Well played both!

Do you want to play again? (yes/no): no

Thanks for playing! Goodbye!
[Script terminates]
```

---

## 12. Ambiguities, Apparent Defects, and Differences

### 12.1 Ambiguity: Move String Parsing
- **Issue:** Function `validate_move()` expects an integer parameter (line 65: `if not isinstance(move, int)`), but input comes as a string from `input()`.
- **Actual Behavior:** `get_player_move()` converts the string to int using `int(user_input)` (line 54), or catches ValueError if not numeric. The int is then passed to `validate_move()`.
- **Documentation vs. Code:** Docstring for `get_player_move()` says "Returns: The square number (1-9) if valid move", which matches actual behavior. However, the intermediate parsing step is implicit.
- **Ambiguity:** It is slightly unclear from `validate_move()`'s docstring that it expects an already-parsed integer and will reject strings.

### 12.2 Defect: Integer Type Checking
- **Issue:** Line 66 uses `isinstance(move, int)` to validate type, but in Python, `bool` is a subclass of `int`.
- **Actual Risk:** If `True` or `False` is somehow passed (value 1 or 0), the type check passes.
  - `True == 1` (will be rejected by range check)
  - `False == 0` (will be rejected by range check)
- **Impact:** Low risk in practice since input conversion (`int(user_input)`) will not produce bool values from normal terminal input.

### 12.3 Ambiguity: Win Detection Timing
- **Issue:** Win is checked immediately after `place_move()` and only for the current player (line 127: `if check_win(board, current_player)`).
- **Behavior:** Because X always moves first and players strictly alternate, a win can only occur on the current player's move. The second player cannot have won on a move they haven't made yet.
- **Consequence:** Both players' boards after each move show the most recent player's status; there is no risk of missing an opponent's earlier win because the game strictly alternates.
- **Clarification Needed:** Docstring for `check_win()` does not explicitly state "checks only current player" but code implements it correctly.

### 12.4 Ambiguity: Draw Detection Without Prior Win Check
- **Issue:** Line 131 checks for draw immediately after win check. Draw is detected even if the current player just won.
- **Code Path:** If a player wins (line 127–128), the code breaks before reaching the draw check (line 131).
- **Actual Behavior:** Correct; a win always terminates the game, so draw detection never occurs when the board is full after a winning move.
- **Documentation:** Code comment in `check_draw()` says "A draw occurs when the board is full and no player has won," which is accurate to implementation (the check is only reached if no win was detected).

### 12.5 Defect: Input Stripping and Case Sensitivity
- **Issue:** Line 50 uses `.strip()` to remove whitespace but only checks for lowercase 'q': `if user_input.lower() == 'q'`.
- **Code:** `if user_input.lower() == 'q': raise QuitGame()` correctly handles uppercase 'Q'.
- **Impact:** No defect; the code correctly uses `.lower()` for case-insensitive comparison.

### 12.6 Ambiguity: Exception Re-raising in play_game()
- **Issue:** Lines 119–120 catch `QuitGame`, print a message, and then re-raise it.
- **Code:**
  ```python
  except QuitGame:
      print("Game quit by player. Goodbye!")
      raise
  ```
- **Behavior:** The exception is re-raised, caught in `main()`, and results in session termination.
- **Clarity:** Code correctly propagates the exception but docstring for `play_game()` could better explain that `QuitGame` is re-raised.

### 12.7 Potential Defect: No Maximum Game Limit
- **Issue:** The session loop in `main()` (lines 155–162) has no limit on the number of games or playtime.
- **Behavior:** Players can play indefinitely as long as they respond "yes" to the play-again prompt.
- **Risk:** No risk of crash or error; this appears to be intentional design.

### 12.8 Behavior: play_again_prompt Accepts Substrings
- **Issue:** Line 135 checks `if response in ['yes', 'y']`, which does not accept other variations like 'yeah' or 'yep'.
- **Actual Behavior:** Only exact matches of 'yes', 'y', 'no', or 'n' (after `.lower()`) are accepted.
- **Clarity:** Behavior matches the prompt text "(yes/no)"; no defect.

### 12.9 Documentation Gap: Board Representation
- **Issue:** Main docstring says "terminal-based" game but does not specify that board is a Python dictionary internally.
- **Clarification:** Provided in `initialize_board()` docstring.

### 12.10 Apparent Defect: No Input Length Validation
- **Issue:** Lines 54 accept any string that parses as an integer, including very large numbers and negative numbers.
- **Example:** Input "-999999999" will fail the range check, but will be tried.
- **Actual Behavior:** Range check (line 67: `move < 1 or move > 9`) correctly rejects out-of-range integers.
- **Impact:** No defect; validation works correctly.

---

## 13. Recommendations and Design Notes

**Note:** This section is separate from the specification itself and describes recommended improvements or clarifications. These are not part of the implemented behavior.

### 13.1 Recommended Improvements
- **R13.1.1:** Add a move counter to prevent infinite draws (optional tournament rule).
- **R13.1.2:** Track game statistics across sessions (wins/losses/draws per player).
- **R13.1.3:** Add difficulty levels if AI opponent is desired.
- **R13.1.4:** Implement undo/replay functionality.
- **R13.1.5:** Add time limits for moves (optional tournament rule).

### 13.2 Clarifications for Implementation
- **C13.2.1:** The board is never explicitly reset between games in the current code; `initialize_board()` creates a new board object, so there is no risk of state carryover.
- **C13.2.2:** The distinction between `reset_board()` and `initialize_board()` is subtle; both clear the board, but `reset_board()` modifies an existing board in-place, while `initialize_board()` creates a new board. Only `initialize_board()` is used in `play_game()`.

---

## 14. Alloy Model Readiness

The specification above is precise enough to translate into an Alloy model. Key elements:

### 14.1 Alloy Signatures
- **Board:** Map from positions {1..9} to values {X, O, Empty}
- **Player:** X, O (enumeration)
- **GameState:** {Setup, Active, Win, Draw, Quit}
- **Move:** Integer in range 1..9

### 14.2 Alloy Predicates
- `validMove[b: Board, m: Move] → bool`: Checks board[m] == Empty and m in 1..9
- `checkWin[b: Board, p: Player] → bool`: Checks all 8 winning combinations
- `checkDraw[b: Board] → bool`: Checks all squares are filled
- `placeMove[b: Board, m: Move, p: Player] → Board`: Returns board with board'[m] = p

### 14.3 Alloy Constraints
- Players strictly alternate; exactly one move per turn
- Win is checked only for the current player
- Draw is checked only when no win has occurred
- Game state transitions: Setup → Active → {Win, Draw, Quit}

---

## 15. Summary

This Tic-Tac-Toe implementation is a complete, functional game with:
- Clear board representation (positions 1–9)
- Two human players (X and O)
- Strict alternating turns starting with X
- Comprehensive input validation with error messages
- Eight win conditions (3 rows, 3 columns, 2 diagonals)
- Draw detection when board is full
- Quit and replay functionality across multiple sessions
- Exception-based control flow for quit commands

All behaviors are implemented as specified in the code, with minimal ambiguities and no critical defects. The code is ready for formal specification and analysis.
