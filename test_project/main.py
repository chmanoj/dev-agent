#!/usr/bin/env python3
"""
Simple test application for dev-agent testing.
"""

def hello_world():
    """Print hello world message."""
    print("Hello, World!")

def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

class Calculator:
    """Simple calculator class."""
    
    def __init__(self):
        self.history = []
    
    def calculate(self, operation: str, a: int, b: int) -> int:
        """Perform calculation and store in history."""
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        self.history.append(f"{a} {operation} {b} = {result}")
        return result

if __name__ == "__main__":
    hello_world()
    calc = Calculator()
    print(calc.calculate("add", 5, 3))