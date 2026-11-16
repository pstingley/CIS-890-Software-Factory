"""Test fixture: simple path with sequential statements."""

def simple_path():
    """A function with just sequential statements."""
    x = 1
    y = 2
    z = x + y
    print(z)
    return z


# Expected edges:
# Entry -> x=1 -> y=2 -> z=x+y -> print(z) -> return z -> Exit
