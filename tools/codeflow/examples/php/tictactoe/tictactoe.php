<?php
/**
 * Fixed PHP example for CodeFlow reverse-engineering validation.
 * This is a source-language fixture, NOT PHP-generation functionality.
 */
declare(strict_types=1);

final class QuitGame extends RuntimeException {}

/** @return array<int, null|string> */
function initialize_board(): array
{
    return array_fill_keys(range(1, 9), null);
}

/** @param array<int, null|string> $board */
function reset_board(array &$board): void
{
    foreach (range(1, 9) as $square) {
        $board[$square] = null;
    }
}

/** @param array<int, null|string> $board */
function display_board(array $board): void
{
    echo "\n";
    for ($row = 0; $row < 3; $row++) {
        $rowSquares = [];
        for ($col = 0; $col < 3; $col++) {
            $squareNum = $row * 3 + $col + 1;
            $squareValue = $board[$squareNum];
            if ($squareValue !== null) {
                $rowSquares[] = $squareValue;
            } else {
                $rowSquares[] = (string) $squareNum;
            }
        }
        echo ' ' . implode(' | ', $rowSquares) . "\n";
        if ($row < 2) {
            echo "---+---+---\n";
        }
    }
    echo "\n";
}

/** @param array<int, null|string> $board */
function validate_move(array $board, mixed $move): bool
{
    if (!is_int($move)) {
        return false;
    }
    if ($move < 1 || $move > 9) {
        return false;
    }
    if ($board[$move] !== null) {
        return false;
    }
    return true;
}

/** @param array<int, null|string> $board */
function get_player_move(array $board, string $player): int
{
    while (true) {
        echo "Player {$player}'s turn: Enter move (1-9) or 'q' to quit: ";
        $line = fgets(STDIN);
        if ($line === false) {
            throw new QuitGame('Input stream closed');
        }
        $userInput = trim($line);
        if (strtolower($userInput) === 'q') {
            throw new QuitGame('Player requested quit');
        }

        // FILTER_VALIDATE_INT avoids silently accepting a partial numeric string.
        $move = filter_var($userInput, FILTER_VALIDATE_INT);
        if ($move === false) {
            echo "Error: Invalid input. Please enter a number between 1 and 9, or 'q' to quit.\n";
            continue;
        }
        if (!validate_move($board, $move)) {
            if ($move < 1 || $move > 9) {
                echo "Error: Invalid move. Please enter a number between 1 and 9.\n";
            } else {
                echo "Error: Square {$move} is already occupied. Try again.\n";
            }
            continue;
        }
        return $move;
    }
}

/** @param array<int, null|string> $board */
function place_move(array &$board, int $move, string $player): void
{
    // Caller is responsible for calling validate_move first.
    $board[$move] = $player;
}

/** @param array<int, null|string> $board */
function check_win(array $board, string $player): bool
{
    $winningCombinations = [
        [1, 2, 3], [4, 5, 6], [7, 8, 9],
        [1, 4, 7], [2, 5, 8], [3, 6, 9],
        [1, 5, 9], [3, 5, 7],
    ];
    foreach ($winningCombinations as $combination) {
        $allMatch = true;
        foreach ($combination as $square) {
            if ($board[$square] !== $player) {
                $allMatch = false;
                break;
            }
        }
        if ($allMatch) {
            return true;
        }
    }
    return false;
}

/** @param array<int, null|string> $board */
function check_draw(array $board): bool
{
    foreach (range(1, 9) as $square) {
        if ($board[$square] === null) {
            return false;
        }
    }
    return true;
}

function play_again_prompt(): bool
{
    while (true) {
        echo 'Do you want to play again? (yes/no): ';
        $line = fgets(STDIN);
        if ($line === false) {
            return false;
        }
        $answer = strtolower(trim($line));
        if ($answer === 'yes' || $answer === 'y') {
            return true;
        }
        if ($answer === 'no' || $answer === 'n') {
            return false;
        }
        echo "Please enter 'yes' or 'no'.\n";
    }
}

function play_game(): void
{
    $board = initialize_board();
    $currentPlayer = 'X';
    $otherPlayer = 'O';
    display_board($board);

    try {
        while (true) {
            $move = get_player_move($board, $currentPlayer);
            place_move($board, $move, $currentPlayer);
            display_board($board);
            if (check_win($board, $currentPlayer)) {
                echo "Player {$currentPlayer} wins! Congratulations!\n";
                break;
            }
            if (check_draw($board)) {
                echo "It's a draw! Well played both!\n";
                break;
            }
            [$currentPlayer, $otherPlayer] = [$otherPlayer, $currentPlayer];
        }
    } catch (QuitGame $exception) {
        echo "Game quit by player. Goodbye!\n";
        throw $exception;
    }
}

function main(): void
{
    echo "Welcome to Tic-Tac-Toe!\nTwo human players: X goes first; enter 1-9 to move or q to quit.\n";
    while (true) {
        try {
            play_game();
        } catch (QuitGame $exception) {
            echo "Thanks for playing! Goodbye!\n";
            break;
        }
        if (!play_again_prompt()) {
            echo "Thanks for playing! Goodbye!\n";
            break;
        }
    }
}
    if (isset($_SERVER['SCRIPT_FILENAME']) &&
    realpath($_SERVER['SCRIPT_FILENAME']) === __FILE__) {
    main();
}
