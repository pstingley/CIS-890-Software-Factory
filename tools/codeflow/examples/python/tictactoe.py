"""
Tic-Tac-Toe Game - A terminal-based two-player game.
"""


def initialize_board():
    """Initialize an empty board as a dictionary mapping positions 1-9 to None."""
    return {i: None for i in range(1, 10)}


def reset_board(board):
    """Reset/clear the board by setting all squares to None."""
    for i in range(1, 10):
        board[i] = None
    return board


def display_board(board):
    """Display the current board state in a 3x3 grid format."""
    print("\n")
    for row in range(3):
        row_squares = []
        for col in range(3):
            square_num = row * 3 + col + 1
            square_value = board[square_num]
            if square_value:
                row_squares.append(f"{square_value}")
            else:
                row_squares.append(f"{square_num}")
        print(" | ".join(row_squares))
        if row < 2:
            print("--+---+--")
    print("\n")


def validate_move(board, move):
    """
    Validate if a move is legal.
    
    Args:
        board: The current board state
        move: The square number (1-9) the player wants to move to
        
    Returns:
        True if the move is valid (square number 1-9 and not occupied), False otherwise
    """
    if not isinstance(move, int) or move < 1 or move > 9:
        return False
    if board[move] is not None:
        return False
    return True


def get_player_move(board, player):
    """
    Prompt the current player for input and return a validated move.
    
    Args:
        board: The current board state
        player: The current player ('X' or 'O')
        
    Returns:
        The square number (1-9) if valid move, or 'quit' to exit the game
        
    Raises:
        QuitGame: If the player enters 'q'
    """
    while True:
        try:
            user_input = input(f"Player {player}'s turn. Enter move (1-9) or 'q' to quit: ").strip()
            
            # Check for quit command
            if user_input.lower() == 'q':
                raise QuitGame()
            
            # Try to convert to integer
            move = int(user_input)
            
            # Validate the move
            if validate_move(board, move):
                return move
            elif board[move] is not None:
                print(f"Error: Square {move} is already occupied. Try again.")
            else:
                print(f"Error: Invalid move. Please enter a number between 1 and 9.")
                
        except ValueError:
            print("Error: Invalid input. Please enter a number between 1 and 9, or 'q' to quit.")
        except QuitGame:
            raise


def place_move(board, move, player):
    """
    Update the board with a player's mark.
    
    Args:
        board: The current board state
        move: The square number (1-9) where the player is moving
        player: The player ('X' or 'O') making the move
    """
    board[move] = player


def check_win(board, player):
    """
    Check if the current player has won.
    
    Checks all eight winning combinations (three rows, three columns, two diagonals).
    
    Args:
        board: The current board state
        player: The player ('X' or 'O') to check for a win
        
    Returns:
        True if the player has won, False otherwise
    """
    # Define all winning combinations
    winning_combinations = [
        # Rows
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
        # Columns
        [1, 4, 7],
        [2, 5, 8],
        [3, 6, 9],
        # Diagonals
        [1, 5, 9],
        [3, 5, 7],
    ]
    
    # Check each combination
    for combination in winning_combinations:
        if all(board[square] == player for square in combination):
            return True
    
    return False


def check_draw(board):
    """
    Check if the game is a draw.
    
    A draw occurs when the board is full and no player has won.
    
    Args:
        board: The current board state
        
    Returns:
        True if the board is full, False otherwise
    """
    return all(board[i] is not None for i in range(1, 10))


def play_again_prompt():
    """
    Ask players if they want to play another game.
    
    Returns:
        True if they want to play again, False otherwise
    """
    while True:
        response = input("\nDo you want to play again? (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Please enter 'yes' or 'no'.")


def play_game():
    """
    Manage a single game session with turn alternation.
    
    Handles the game loop, turn management, win/draw detection, and player feedback.
    Raises QuitGame if a player enters 'q' to quit.
    """
    board = initialize_board()
    current_player = 'X'
    other_player = 'O'
    
    print("\n" + "="*40)
    print("Welcome to Tic-Tac-Toe!")
    print("="*40)
    
    display_board(board)
    
    while True:
        try:
            # Get and validate player move
            move = get_player_move(board, current_player)
            
            # Place the move
            place_move(board, move, current_player)
            
            # Display the updated board
            display_board(board)
            
            # Check for win
            if check_win(board, current_player):
                print(f"🎉 Player {current_player} wins! Congratulations!")
                break
            
            # Check for draw
            if check_draw(board):
                print("It's a draw! Well played both!")
                break
            
            # Switch players
            current_player, other_player = other_player, current_player
            
        except QuitGame:
            print("Game quit by player. Goodbye!")
            raise


def main():
    """
    Orchestrate the overall game flow.
    
    Handles multiple games, play-again prompts, and quit commands.
    """
    print("\n" + "="*40)
    print("  TERMINAL TIC-TAC-TOE GAME")
    print("="*40)
    print("Rules:")
    print("- Two players (X and O)")
    print("- X always goes first")
    print("- Squares are numbered 1-9")
    print("- First to get three in a row wins!")
    print("- Enter 'q' at any time to quit")
    print("="*40 + "\n")
    
    while True:
        try:
            play_game()
        except QuitGame:
            print("\nThanks for playing! Goodbye!")
            break
        
        # Ask if players want to play again
        if not play_again_prompt():
            print("\nThanks for playing! Goodbye!")
            break


class QuitGame(Exception):
    """Exception raised when a player chooses to quit."""
    pass


if __name__ == "__main__":
    main()
