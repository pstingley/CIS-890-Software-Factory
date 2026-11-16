"""Test fixture: single for loop."""

def single_loop():
    """A function with a single for loop."""
    total = 0
    for i in range(10):
        total += i
    print(total)
    return total

# Expected edges:
# Entry -> total=0 -> for i in range(10) -> loop body: total+=i -> loop back -> exit loop -> print(total) -> return -> Exit
