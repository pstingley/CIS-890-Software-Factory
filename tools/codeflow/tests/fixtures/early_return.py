"""Test fixture: early return from loop."""

def early_return(items):
    """A function with an early return inside a loop."""
    for item in items:
        if item == "target":
            return item
    return None

# Expected edges:
# Entry -> for item in items -> loop body -> if item=="target" (decision)
#   -> true: return item -> Exit
#   -> false: loop back -> exit loop -> return None -> Exit
