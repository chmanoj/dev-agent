"""Authentication and authorization system for dev-agent API."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pydantic import BaseModel, Field

from dev_agent.errors.exceptions import AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)


class UserRole(BaseModel):
    """User role definition."""
    
    name: str
    permissions: list[str]
    description: str = ""


class User(BaseModel):
    """User model."""
    
    id: str
    username: str
    email: str
    roles: list[str] = Field(default_factory=list)
    team_id: str | None = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: datetime | None = None


class TokenData(BaseModel):
    """JWT token data."""
    
    user_id: str
    username: str
    roles: list[str]
    team_id: str | None = None
    exp: datetime
    iat: datetime


class LoginRequest(BaseModel):
    """Login request model."""
    
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response model."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User


class AuthenticationManager:
    """Authentication and authorization manager."""
    
    # Default roles and permissions
    DEFAULT_ROLES = {
        "admin": UserRole(
            name="admin",
            permissions=[
                "project:read", "project:write", "project:delete",
                "workflow:read", "workflow:write", "workflow:execute",
                "analysis:read", "analysis:write",
                "generation:read", "generation:write",
                "collaboration:read", "collaboration:write",
                "user:read", "user:write", "user:delete",
                "team:read", "team:write", "team:delete",
            ],
            description="Full system access",
        ),
        "developer": UserRole(
            name="developer",
            permissions=[
                "project:read", "project:write",
                "workflow:read", "workflow:write", "workflow:execute",
                "analysis:read", "analysis:write",
                "generation:read", "generation:write",
                "collaboration:read", "collaboration:write",
            ],
            description="Standard developer access",
        ),
        "viewer": UserRole(
            name="viewer",
            permissions=[
                "project:read",
                "workflow:read",
                "analysis:read",
                "generation:read",
                "collaboration:read",
            ],
            description="Read-only access",
        ),
    }
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        expiration_hours: int = 24,
    ) -> None:
        """Initialize the authentication manager.
        
        Args:
            secret_key: JWT secret key
            algorithm: JWT algorithm
            expiration_hours: Token expiration time in hours
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiration_hours = expiration_hours
        
        # In-memory user store (replace with database in production)
        self.users: dict[str, User] = {}
        self.user_passwords: dict[str, str] = {}  # username -> hashed_password
        self.roles = self.DEFAULT_ROLES.copy()
        
        # Create default admin user
        self._create_default_users()
    
    def _create_default_users(self) -> None:
        """Create default users for development."""
        admin_user = User(
            id="admin-001",
            username="admin",
            email="admin@dev-agent.dev",
            roles=["admin"],
        )
        
        dev_user = User(
            id="dev-001",
            username="developer",
            email="dev@dev-agent.dev",
            roles=["developer"],
        )
        
        viewer_user = User(
            id="viewer-001",
            username="viewer",
            email="viewer@dev-agent.dev",
            roles=["viewer"],
        )
        
        # Store users (in production, use proper password hashing)
        self.users["admin"] = admin_user
        self.users["developer"] = dev_user
        self.users["viewer"] = viewer_user
        
        # Store passwords (in production, use proper password hashing like bcrypt)
        self.user_passwords["admin"] = "admin123"  # noqa: S105
        self.user_passwords["developer"] = "dev123"  # noqa: S105
        self.user_passwords["viewer"] = "view123"  # noqa: S105
    
    async def authenticate_user(self, username: str, password: str) -> User:
        """Authenticate a user with username and password.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Authenticated user
            
        Raises:
            AuthenticationError: If authentication fails
        """
        if username not in self.users:
            raise AuthenticationError("Invalid username or password")
        
        # In production, use proper password hashing verification
        if self.user_passwords.get(username) != password:
            raise AuthenticationError("Invalid username or password")
        
        user = self.users[username]
        if not user.is_active:
            raise AuthenticationError("User account is disabled")
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        
        logger.info(f"User {username} authenticated successfully")
        return user
    
    def create_access_token(self, user: User) -> str:
        """Create a JWT access token for a user.
        
        Args:
            user: User to create token for
            
        Returns:
            JWT access token
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(hours=self.expiration_hours)
        
        token_data = {
            "user_id": user.id,
            "username": user.username,
            "roles": user.roles,
            "team_id": user.team_id,
            "exp": expire,
            "iat": now,
        }
        
        token = jwt.encode(token_data, self.secret_key, algorithm=self.algorithm)
        logger.info(f"Created access token for user {user.username}")
        return token
    
    async def verify_token(self, token: str) -> dict[str, Any]:
        """Verify and decode a JWT token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token data
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Validate token data
            username = payload.get("username")
            if not username or username not in self.users:
                raise AuthenticationError("Invalid token: user not found")
            
            user = self.users[username]
            if not user.is_active:
                raise AuthenticationError("User account is disabled")
            
            return payload
        
        except jwt.ExpiredSignatureError as e:
            raise AuthenticationError("Token has expired") from e
        except jwt.InvalidTokenError as e:
            raise AuthenticationError("Invalid token") from e
    
    def check_permission(self, user_roles: list[str], required_permission: str) -> bool:
        """Check if user roles have the required permission.
        
        Args:
            user_roles: List of user role names
            required_permission: Required permission string
            
        Returns:
            True if user has permission, False otherwise
        """
        for role_name in user_roles:
            role = self.roles.get(role_name)
            if role and required_permission in role.permissions:
                return True
        return False
    
    def require_permission(self, user_roles: list[str], required_permission: str) -> None:
        """Require a specific permission, raise exception if not authorized.
        
        Args:
            user_roles: List of user role names
            required_permission: Required permission string
            
        Raises:
            AuthorizationError: If user doesn't have required permission
        """
        if not self.check_permission(user_roles, required_permission):
            raise AuthorizationError(
                f"Insufficient permissions. Required: {required_permission}"
            )
    
    async def login(self, login_request: LoginRequest) -> TokenResponse:
        """Login a user and return access token.
        
        Args:
            login_request: Login request with username and password
            
        Returns:
            Token response with access token and user info
            
        Raises:
            AuthenticationError: If login fails
        """
        user = await self.authenticate_user(
            login_request.username, 
            login_request.password
        )
        
        access_token = self.create_access_token(user)
        
        return TokenResponse(
            access_token=access_token,
            expires_in=self.expiration_hours * 3600,  # Convert to seconds
            user=user,
        )
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        roles: list[str] | None = None,
        team_id: str | None = None,
    ) -> User:
        """Create a new user.
        
        Args:
            username: Username
            email: Email address
            password: Password
            roles: List of role names
            team_id: Team ID
            
        Returns:
            Created user
            
        Raises:
            AuthenticationError: If user already exists
        """
        if username in self.users:
            raise AuthenticationError(f"User {username} already exists")
        
        user = User(
            id=f"user-{len(self.users) + 1:03d}",
            username=username,
            email=email,
            roles=roles or ["developer"],
            team_id=team_id,
        )
        
        self.users[username] = user
        self.user_passwords[username] = password  # In production, hash this
        
        logger.info(f"Created user {username}")
        return user
    
    def get_user_permissions(self, user_roles: list[str]) -> list[str]:
        """Get all permissions for a list of user roles.
        
        Args:
            user_roles: List of user role names
            
        Returns:
            List of all permissions
        """
        permissions = set()
        for role_name in user_roles:
            role = self.roles.get(role_name)
            if role:
                permissions.update(role.permissions)
        return list(permissions)