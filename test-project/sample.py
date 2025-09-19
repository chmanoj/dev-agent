"""Sample Python file for testing dev-agent."""

class UserManager:
    """Manages user operations."""
    
    def __init__(self):
        self.users = {}
    
    def create_user(self, username: str, email: str) -> bool:
        """Create a new user."""
        if username in self.users:
            return False
        
        self.users[username] = {
            'email': email,
            'active': True
        }
        return True
    
    def get_user(self, username: str) -> dict:
        """Get user information."""
        return self.users.get(username)
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate a user."""
        # Simple authentication logic
        user = self.users.get(username)
        return user is not None and user.get('active', False)


def main():
    """Main application entry point."""
    manager = UserManager()
    manager.create_user("admin", "admin@example.com")
    print("User management system initialized")


if __name__ == "__main__":
    main()