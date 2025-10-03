"""Example: Azure OpenAI Code Generation

This example demonstrates how to use Azure OpenAI to generate Python code
that matches existing codebase patterns and style.

Requirements:
- Azure OpenAI endpoint and API key configured
- Environment variables set (see below)
- dev-agent installed with Azure OpenAI dependencies
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.llm.token_counter import TokenCounter
from dev_agent.llm.cost_tracker import CostTracker
from dev_agent.llm.prompt_templates import PromptTemplate
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr


def setup_azure_config() -> AzureOpenAIConfig:
    """Set up Azure OpenAI configuration from environment variables.
    
    Returns:
        AzureOpenAIConfig: Validated configuration object
    """
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-resource.openai.azure.com/")
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "your-api-key-here")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    
    return AzureOpenAIConfig(
        endpoint=endpoint,
        api_key=SecretStr(api_key),
        api_version="2024-02-15-preview",
        deployment_name=deployment_name,
        embedding_deployment="text-embedding-ada-002",
        max_tokens=2000,  # Shorter for code generation
        temperature=0.3,  # Lower temperature for more deterministic code
        max_retries=3,
        timeout=60,
    )


def create_code_generation_prompt() -> PromptTemplate:
    """Create a prompt template for code generation.
    
    Returns:
        PromptTemplate: Structured prompt for code generation
    """
    system_prompt = """You are an expert Python developer generating production-quality code.

Guidelines:
1. Follow PEP 8 style guidelines strictly
2. Use type hints on all functions and methods
3. Write comprehensive docstrings in Google style
4. Include error handling with specific exceptions
5. Use modern Python 3.10+ syntax (e.g., list[str] not List[str])
6. Add logging where appropriate
7. Make code testable and maintainable
8. Match the existing codebase patterns exactly

Output ONLY the Python code, no explanations or markdown formatting.
"""

    user_prompt_template = """## Task
{task_description}

## Existing Code Patterns
{code_patterns}

## Similar Implementations
{similar_code}

## Requirements
{requirements}

Generate the Python code following the patterns shown above.
"""

    return PromptTemplate(
        system_prompt=system_prompt,
        user_prompt_template=user_prompt_template,
        required_context=["task_description", "code_patterns", "similar_code", "requirements"],
        max_context_tokens=4000,
        temperature=0.3,
        max_tokens=2000,
    )


async def generate_code_example():
    """Example: Generate Python code using Azure OpenAI.
    
    This example shows:
    1. Setting up Azure OpenAI for code generation
    2. Providing code patterns and examples
    3. Generating code that matches existing style
    4. Validating and saving generated code
    """
    print("=" * 70)
    print("Azure OpenAI Code Generation Example")
    print("=" * 70)
    
    # Step 1: Set up configuration
    print("\n[1/5] Setting up Azure OpenAI configuration...")
    try:
        config = setup_azure_config()
        print(f"✅ Configuration loaded")
        print(f"   Temperature: {config.temperature} (lower = more deterministic)")
        print(f"   Max tokens: {config.max_tokens}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Step 2: Initialize clients
    print("\n[2/5] Initializing clients...")
    llm_client = AzureOpenAIClient(config)
    token_counter = TokenCounter()
    cost_tracker = CostTracker()
    print("✅ Clients initialized")
    
    # Step 3: Prepare code generation context
    print("\n[3/5] Preparing code generation context...")
    
    # Task description
    task_description = """
    Create a UserRepository class that handles CRUD operations for user data.
    The class should use async/await patterns and follow the repository pattern.
    """
    
    # Example code patterns from the codebase
    code_patterns = """
    # Example 1: Existing repository pattern
    class BaseRepository:
        def __init__(self, db_session: AsyncSession):
            self.db_session = db_session
        
        async def get_by_id(self, id: int) -> Model | None:
            result = await self.db_session.execute(
                select(Model).where(Model.id == id)
            )
            return result.scalar_one_or_none()
    
    # Example 2: Error handling pattern
    try:
        result = await operation()
    except DatabaseError as e:
        logger.error(f"Database operation failed: {e}")
        raise RepositoryError("Failed to fetch data") from e
    
    # Example 3: Type hints and docstrings
    async def create_item(self, data: dict[str, Any]) -> Item:
        \"\"\"Create a new item in the database.
        
        Args:
            data: Dictionary containing item data
            
        Returns:
            Item: Created item instance
            
        Raises:
            ValidationError: If data is invalid
            RepositoryError: If database operation fails
        \"\"\"
    """
    
    # Similar implementations
    similar_code = """
    # Similar implementation: ProductRepository
    class ProductRepository(BaseRepository):
        async def create(self, product_data: dict[str, Any]) -> Product:
            product = Product(**product_data)
            self.db_session.add(product)
            await self.db_session.commit()
            await self.db_session.refresh(product)
            return product
        
        async def update(self, id: int, updates: dict[str, Any]) -> Product:
            product = await self.get_by_id(id)
            if not product:
                raise NotFoundError(f"Product {id} not found")
            
            for key, value in updates.items():
                setattr(product, key, value)
            
            await self.db_session.commit()
            await self.db_session.refresh(product)
            return product
    """
    
    # Requirements
    requirements = """
    - Inherit from BaseRepository
    - Implement create, read, update, delete methods
    - Use async/await for all database operations
    - Include comprehensive error handling
    - Add type hints to all methods
    - Write Google-style docstrings
    - Use logging for errors
    - Follow existing naming conventions
    """
    
    print("✅ Context prepared")
    
    # Step 4: Build prompt and generate code
    print("\n[4/5] Building prompt and generating code...")
    
    template = create_code_generation_prompt()
    prompt = template.user_prompt_template.format(
        task_description=task_description,
        code_patterns=code_patterns,
        similar_code=similar_code,
        requirements=requirements,
    )
    
    # Count tokens
    total_tokens = token_counter.count_tokens(
        template.system_prompt + prompt,
        model="gpt-4"
    )
    print(f"   Input tokens: {total_tokens}")
    
    # Estimate cost
    estimated_cost = token_counter.estimate_cost(
        prompt_tokens=total_tokens,
        completion_tokens=template.max_tokens,
        model="gpt-4",
    )
    print(f"   Estimated cost: ${estimated_cost:.4f}")
    
    print("   Generating code... (this may take 10-20 seconds)")
    
    try:
        # Generate code
        generated_code = await llm_client.generate_completion(
            prompt=prompt,
            system_prompt=template.system_prompt,
            temperature=template.temperature,
            max_tokens=template.max_tokens,
        )
        
        print("✅ Code generated successfully!")
        
        # Count completion tokens
        completion_tokens = token_counter.count_tokens(generated_code, model="gpt-4")
        print(f"   Completion tokens: {completion_tokens}")
        
        # Track costs
        cost_tracker.record_completion(
            prompt_tokens=total_tokens,
            completion_tokens=completion_tokens,
            model="gpt-4",
        )
        
        # Step 5: Display and save generated code
        print("\n[5/5] Displaying generated code...")
        print("=" * 70)
        print("Generated Code:")
        print("=" * 70)
        print(generated_code)
        print("=" * 70)
        
        # Save to file
        output_file = Path("user_repository_generated.py")
        output_file.write_text(generated_code)
        print(f"\n💾 Code saved to: {output_file}")
        
        # Display cost report
        report = cost_tracker.get_report()
        print(f"\n💰 Cost Report:")
        print(f"   Total tokens: {report['total_tokens']}")
        print(f"   Actual cost: ${report['total_cost']:.4f}")
        
    except Exception as e:
        print(f"❌ Error generating code: {e}")
        return
    
    print("\n✅ Example completed successfully!")


async def generate_code_with_context_injection():
    """Example: Generate code with context from vector search.
    
    This shows how to inject relevant code examples from a vector database
    to improve code generation quality.
    """
    print("\n" + "=" * 70)
    print("Code Generation with Context Injection Example")
    print("=" * 70)
    
    print("\n[1/4] Setting up...")
    try:
        config = setup_azure_config()
        llm_client = AzureOpenAIClient(config)
        print("✅ Setup complete")
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return
    
    print("\n[2/4] Simulating vector search for relevant code...")
    # In a real scenario, this would come from vector database search
    relevant_code_chunks = [
        {
            "file": "repositories/base.py",
            "code": "class BaseRepository:\n    async def get_by_id(self, id: int) -> Model | None: ...",
            "similarity": 0.92,
        },
        {
            "file": "repositories/product.py",
            "code": "async def create(self, data: dict) -> Product: ...",
            "similarity": 0.88,
        },
        {
            "file": "models/user.py",
            "code": "class User(Base):\n    id: int\n    email: str\n    ...",
            "similarity": 0.85,
        },
    ]
    
    print(f"✅ Found {len(relevant_code_chunks)} relevant code chunks")
    for chunk in relevant_code_chunks:
        print(f"   - {chunk['file']} (similarity: {chunk['similarity']:.2f})")
    
    print("\n[3/4] Building context-aware prompt...")
    context = "\n\n".join([
        f"# From {chunk['file']} (similarity: {chunk['similarity']:.2f})\n{chunk['code']}"
        for chunk in relevant_code_chunks
    ])
    
    template = create_code_generation_prompt()
    prompt = template.user_prompt_template.format(
        task_description="Create a simple User model with validation",
        code_patterns=context,
        similar_code="See above examples",
        requirements="Match the style of existing models",
    )
    
    print("\n[4/4] Generating code with injected context...")
    try:
        code = await llm_client.generate_completion(
            prompt=prompt,
            system_prompt=template.system_prompt,
            temperature=0.3,
            max_tokens=1000,
        )
        
        print("✅ Code generated with context!")
        print("\n" + "-" * 70)
        print(code)
        print("-" * 70)
        
    except Exception as e:
        print(f"❌ Generation error: {e}")


async def generate_test_code_example():
    """Example: Generate test code for existing functions.
    
    This shows how to generate pytest tests that match existing test patterns.
    """
    print("\n" + "=" * 70)
    print("Test Code Generation Example")
    print("=" * 70)
    
    print("\n[1/3] Setting up...")
    try:
        config = setup_azure_config()
        llm_client = AzureOpenAIClient(config)
        print("✅ Setup complete")
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return
    
    print("\n[2/3] Preparing test generation context...")
    
    # Function to test
    function_to_test = """
    async def create_user(
        email: str,
        password: str,
        db: AsyncSession,
    ) -> User:
        \"\"\"Create a new user with hashed password.
        
        Args:
            email: User email address
            password: Plain text password
            db: Database session
            
        Returns:
            User: Created user instance
            
        Raises:
            ValidationError: If email is invalid
            DuplicateError: If email already exists
        \"\"\"
        # Validate email
        if not is_valid_email(email):
            raise ValidationError("Invalid email format")
        
        # Check for duplicates
        existing = await get_user_by_email(email, db)
        if existing:
            raise DuplicateError(f"User with email {email} already exists")
        
        # Hash password and create user
        hashed_password = hash_password(password)
        user = User(email=email, password_hash=hashed_password)
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user
    """
    
    # Existing test patterns
    test_patterns = """
    # Example test pattern
    @pytest.mark.asyncio
    async def test_create_item_success(mock_db_session):
        \"\"\"Test successful item creation.\"\"\"
        # Arrange
        item_data = {"name": "Test Item", "price": 10.99}
        
        # Act
        result = await create_item(item_data, mock_db_session)
        
        # Assert
        assert result.name == "Test Item"
        assert result.price == 10.99
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_item_validation_error(mock_db_session):
        \"\"\"Test item creation with invalid data.\"\"\"
        # Arrange
        invalid_data = {"name": "", "price": -1}
        
        # Act & Assert
        with pytest.raises(ValidationError):
            await create_item(invalid_data, mock_db_session)
    """
    
    prompt = f"""Generate pytest tests for the following function:

{function_to_test}

Follow these existing test patterns:
{test_patterns}

Requirements:
- Use pytest.mark.asyncio for async tests
- Test success case
- Test validation error case
- Test duplicate error case
- Use mocks for database session
- Follow Arrange-Act-Assert pattern
- Include descriptive docstrings

Generate ONLY the test code.
"""
    
    print("\n[3/3] Generating test code...")
    try:
        test_code = await llm_client.generate_completion(
            prompt=prompt,
            system_prompt="You are generating pytest tests for Python code.",
            temperature=0.3,
            max_tokens=1500,
        )
        
        print("✅ Test code generated!")
        print("\n" + "-" * 70)
        print(test_code)
        print("-" * 70)
        
        # Save test code
        output_file = Path("test_user_generated.py")
        output_file.write_text(test_code)
        print(f"\n💾 Test code saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Generation error: {e}")


def main():
    """Run code generation examples."""
    print("\n🚀 Azure OpenAI Code Generation Examples\n")
    
    # Check configuration
    if not os.getenv("AZURE_OPENAI_API_KEY") or not os.getenv("AZURE_OPENAI_ENDPOINT"):
        print("⚠️  Azure OpenAI not configured!")
        print("\nTo run this example, set the following environment variables:")
        print("  export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'")
        print("  export AZURE_OPENAI_API_KEY='your-api-key-here'")
        print("  export AZURE_OPENAI_DEPLOYMENT_NAME='gpt-4'")
        print("\n⚠️  Never commit API keys to version control!")
        return
    
    # Run main example
    asyncio.run(generate_code_example())
    
    # Optional: Run additional examples
    print("\n" + "=" * 70)
    response = input("\nRun context injection example? (y/n): ")
    if response.lower() == 'y':
        asyncio.run(generate_code_with_context_injection())
    
    print("\n" + "=" * 70)
    response = input("\nRun test generation example? (y/n): ")
    if response.lower() == 'y':
        asyncio.run(generate_test_code_example())
    
    print("\n🎉 All examples completed!")
    print("\nKey takeaways:")
    print("  1. Use lower temperature (0.2-0.4) for code generation")
    print("  2. Provide clear code patterns and examples")
    print("  3. Include similar implementations for better results")
    print("  4. Specify requirements explicitly")
    print("  5. Always validate and review generated code")


if __name__ == "__main__":
    main()
