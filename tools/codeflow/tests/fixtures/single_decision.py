"""Test fixture: single if/else decision."""

def single_decision(x):
    """A function with a single if/else decision."""
    if x > 0:
        result = "positive"
    else:
        result = "non-positive"
    return result


# Expected edges:
# Entry -> if x>0 (decision) -> true: result="positive" -> merge -> return result -> Exit
#                            -> false: result="non-positive" -> merge
