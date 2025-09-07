"""A simple Python module for testing."""

def add(a, b):
    """Add two numbers."""
    return a + b

def subtract(a, b):
    """Subtract b from a."""
    return a - b

class Calculator:
    """A simple calculator."""

    def __init__(self):
        self.history = []

    def calculate(self, operation, a, b):
        """Perform calculation."""
        if operation == "add":
            result = add(a, b)
        elif operation == "subtract":
            result = subtract(a, b)
        else:
            result = None

        if result is not None:
            self.history.append(f"{a} {operation} {b} = {result}")

        return result
