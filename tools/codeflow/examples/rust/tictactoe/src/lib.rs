use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Player {
    X,
    O,
}

impl Player {
    pub fn symbol(&self) -> char {
        match self {
            Player::X => 'X',
            Player::O => 'O',
        }
    }

    pub fn other(&self) -> Player {
        match self {
            Player::X => Player::O,
            Player::O => Player::X,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Square {
    Empty,
    X,
    O,
}

pub struct Board {
    squares: HashMap<usize, Square>,
}

impl Board {
    pub fn new() -> Self {
        let mut squares = HashMap::new();
        for i in 1..=9 {
            squares.insert(i, Square::Empty);
        }
        Board { squares }
    }

    pub fn display(&self) -> String {
        let mut result = String::new();
        for row in 0..3 {
            for col in 0..3 {
                let pos = row * 3 + col + 1;
                let symbol = match self.squares.get(&pos) {
                    Some(Square::Empty) => pos.to_string(),
                    Some(Square::X) => "X".to_string(),
                    Some(Square::O) => "O".to_string(),
                    None => "?".to_string(),
                };
                result.push_str(&symbol);
                if col < 2 {
                    result.push_str(" | ");
                }
            }
            result.push('\n');
            if row < 2 {
                result.push_str("--+---+--\n");
            }
        }
        result
    }

    pub fn reset(&mut self) {
        for i in 1..=9 {
            self.squares.insert(i, Square::Empty);
        }
    }

    pub fn place_move(&mut self, position: usize, player: Player) {
        let square = match player {
            Player::X => Square::X,
            Player::O => Square::O,
        };
        self.squares.insert(position, square);
    }

    pub fn validate_move(&self, position: usize) -> bool {
        if !(1..=9).contains(&position) {
            return false;
        }
        self.squares.get(&position) == Some(&Square::Empty)
    }

    pub fn check_win(&self, player: Player) -> bool {
        let square = match player {
            Player::X => Square::X,
            Player::O => Square::O,
        };

        let winning_combinations = [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
            [1, 4, 7],
            [2, 5, 8],
            [3, 6, 9],
            [1, 5, 9],
            [3, 5, 7],
        ];

        winning_combinations.iter().any(|combo| {
            combo
                .iter()
                .all(|&pos| self.squares.get(&pos) == Some(&square))
        })
    }

    pub fn check_draw(&self) -> bool {
        (1..=9).all(|pos| self.squares.get(&pos) != Some(&Square::Empty))
    }

    pub fn is_empty(&self, position: usize) -> bool {
        self.squares.get(&position) == Some(&Square::Empty)
    }
}

impl Default for Board {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone)]
pub struct QuitGame;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_board_initialization() {
        let board = Board::new();
        for i in 1..=9 {
            assert_eq!(board.squares.get(&i), Some(&Square::Empty));
        }
    }

    #[test]
    fn test_board_reset() {
        let mut board = Board::new();
        board.place_move(1, Player::X);
        board.place_move(2, Player::O);
        board.reset();
        for i in 1..=9 {
            assert_eq!(board.squares.get(&i), Some(&Square::Empty));
        }
    }

    #[test]
    fn test_place_move() {
        let mut board = Board::new();
        board.place_move(5, Player::X);
        assert_eq!(board.squares.get(&5), Some(&Square::X));
        board.place_move(1, Player::O);
        assert_eq!(board.squares.get(&1), Some(&Square::O));
    }

    #[test]
    fn test_validate_move_valid() {
        let board = Board::new();
        for i in 1..=9 {
            assert!(board.validate_move(i));
        }
    }

    #[test]
    fn test_validate_move_out_of_range() {
        let board = Board::new();
        assert!(!board.validate_move(0));
        assert!(!board.validate_move(10));
        assert!(!board.validate_move(100));
    }

    #[test]
    fn test_validate_move_occupied() {
        let mut board = Board::new();
        board.place_move(5, Player::X);
        assert!(!board.validate_move(5));
    }

    #[test]
    fn test_win_row_1() {
        let mut board = Board::new();
        board.place_move(1, Player::X);
        board.place_move(2, Player::X);
        board.place_move(3, Player::X);
        assert!(board.check_win(Player::X));
        assert!(!board.check_win(Player::O));
    }

    #[test]
    fn test_win_row_2() {
        let mut board = Board::new();
        board.place_move(4, Player::O);
        board.place_move(5, Player::O);
        board.place_move(6, Player::O);
        assert!(board.check_win(Player::O));
        assert!(!board.check_win(Player::X));
    }

    #[test]
    fn test_win_row_3() {
        let mut board = Board::new();
        board.place_move(7, Player::X);
        board.place_move(8, Player::X);
        board.place_move(9, Player::X);
        assert!(board.check_win(Player::X));
    }

    #[test]
    fn test_win_column_1() {
        let mut board = Board::new();
        board.place_move(1, Player::X);
        board.place_move(4, Player::X);
        board.place_move(7, Player::X);
        assert!(board.check_win(Player::X));
    }

    #[test]
    fn test_win_column_2() {
        let mut board = Board::new();
        board.place_move(2, Player::O);
        board.place_move(5, Player::O);
        board.place_move(8, Player::O);
        assert!(board.check_win(Player::O));
    }

    #[test]
    fn test_win_column_3() {
        let mut board = Board::new();
        board.place_move(3, Player::X);
        board.place_move(6, Player::X);
        board.place_move(9, Player::X);
        assert!(board.check_win(Player::X));
    }

    #[test]
    fn test_win_diagonal_main() {
        let mut board = Board::new();
        board.place_move(1, Player::X);
        board.place_move(5, Player::X);
        board.place_move(9, Player::X);
        assert!(board.check_win(Player::X));
    }

    #[test]
    fn test_win_diagonal_anti() {
        let mut board = Board::new();
        board.place_move(3, Player::O);
        board.place_move(5, Player::O);
        board.place_move(7, Player::O);
        assert!(board.check_win(Player::O));
    }

    #[test]
    fn test_no_win_incomplete_row() {
        let mut board = Board::new();
        board.place_move(1, Player::X);
        board.place_move(2, Player::X);
        assert!(!board.check_win(Player::X));
    }

    #[test]
    fn test_no_win_mixed_players() {
        let mut board = Board::new();
        board.place_move(1, Player::X);
        board.place_move(2, Player::O);
        board.place_move(3, Player::X);
        assert!(!board.check_win(Player::X));
        assert!(!board.check_win(Player::O));
    }

    #[test]
    fn test_draw_full_board() {
        let mut board = Board::new();
        board.place_move(1, Player::X);
        board.place_move(2, Player::O);
        board.place_move(3, Player::X);
        board.place_move(4, Player::X);
        board.place_move(5, Player::O);
        board.place_move(6, Player::O);
        board.place_move(7, Player::O);
        board.place_move(8, Player::X);
        board.place_move(9, Player::X);
        assert!(board.check_draw());
    }

    #[test]
    fn test_no_draw_empty_board() {
        let board = Board::new();
        assert!(!board.check_draw());
    }

    #[test]
    fn test_no_draw_partial_board() {
        let mut board = Board::new();
        board.place_move(1, Player::X);
        board.place_move(2, Player::O);
        board.place_move(3, Player::X);
        assert!(!board.check_draw());
    }

    #[test]
    fn test_player_alternation() {
        assert_eq!(Player::X.other(), Player::O);
        assert_eq!(Player::O.other(), Player::X);
    }

    #[test]
    fn test_player_symbols() {
        assert_eq!(Player::X.symbol(), 'X');
        assert_eq!(Player::O.symbol(), 'O');
    }

    #[test]
    fn test_board_display() {
        let mut board = Board::new();
        board.place_move(5, Player::X);
        let display = board.display();
        assert!(display.contains("X"));
        assert!(display.contains("1"));
        assert!(display.contains("|"));
    }
}
