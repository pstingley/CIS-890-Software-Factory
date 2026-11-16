use std::io::{self, Write};
use tictactoe::{Board, Player, QuitGame};

fn main() {
    println!("Welcome to Tic-Tac-Toe!");
    println!("This is a two-player game where X and O take turns.");
    println!("Board positions are numbered 1-9 (left to right, top to bottom).");
    println!("Enter 'q' to quit at any time.\n");

    loop {
        match play_game() {
            Ok(true) => {
                if !play_again_prompt() {
                    println!("Thanks for playing! Goodbye!");
                    break;
                }
            }
            Ok(false) => {
                println!("Thanks for playing! Goodbye!");
                break;
            }
            Err(_) => {
                println!("Thanks for playing! Goodbye!");
                break;
            }
        }
    }
}

fn play_game() -> Result<bool, QuitGame> {
    let mut board = Board::new();
    let mut current_player = Player::X;

    println!("{}", board.display());

    loop {
        let player_move = get_player_move(&board, current_player)?;
        board.place_move(player_move, current_player);
        println!("{}", board.display());

        if board.check_win(current_player) {
            println!(
                "🎉 Player {} wins! Congratulations!",
                current_player.symbol()
            );
            return Ok(true);
        }

        if board.check_draw() {
            println!("It's a draw! Well played both!");
            return Ok(true);
        }

        current_player = current_player.other();
    }
}

fn get_player_move(board: &Board, player: Player) -> Result<usize, QuitGame> {
    loop {
        print!(
            "Player {}'s turn: Enter move (1-9) or 'q' to quit: ",
            player.symbol()
        );
        io::stdout().flush().unwrap();

        let mut input = String::new();
        io::stdin()
            .read_line(&mut input)
            .expect("Failed to read input");

        let input = input.trim();

        if input.to_lowercase() == "q" {
            println!("Game quit by player. Goodbye!");
            return Err(QuitGame);
        }

        match input.parse::<usize>() {
            Ok(move_num) => {
                if !board.validate_move(move_num) {
                    if !(1..=9).contains(&move_num) {
                        println!("Invalid move. Please enter a number between 1 and 9.");
                    } else {
                        println!("Square {} is already occupied. Try again.", move_num);
                    }
                } else {
                    return Ok(move_num);
                }
            }
            Err(_) => {
                println!("Invalid input. Please enter a number between 1 and 9, or 'q' to quit.");
            }
        }
    }
}

fn play_again_prompt() -> bool {
    loop {
        print!("Do you want to play again? (yes/no): ");
        io::stdout().flush().unwrap();

        let mut input = String::new();
        io::stdin()
            .read_line(&mut input)
            .expect("Failed to read input");

        let input = input.trim().to_lowercase();

        if input == "yes" || input == "y" {
            return true;
        } else if input == "no" || input == "n" {
            return false;
        } else {
            println!("Please enter 'yes' or 'no'.");
        }
    }
}
