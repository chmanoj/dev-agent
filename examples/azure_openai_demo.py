"""Demo script showing Azure OpenAI integration with dev-agent."""

import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import dev_agent
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_agent.config.config_manager import DevAgentConfig, AzureOpenAIConfig
from dev_agent.services.azure_openai_service import AzureOpenAIService, ChatMessage
from dev_agent.generation.generator_factory import GeneratorFactory
from dev_agent.indexing.enhanced_indexing_engine import create_indexing_engine


def setup_demo_config() -> DevAgentConfig:
    """Set up demo configuration with Azure OpenAI."""
    # Create Azure OpenAI configuration
    azure_config = AzureOpenAIConfig(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        chat_model=os.getenv("AZURE_OPENAI_CHAT_MODEL", "gpt-4"),
        embedding_model=os.getenv("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"),
        max_tokens=4000,
        temperature=0.1,
        timeout=60,
        max_retries=3,
    )
    
    # Create main configuration
    config = DevAgentConfig.default()
    config.azure_openai = azure_config
    config.indexing.use_azure_embeddings = True
    
    return config


def demo_azure_service():
    """Demonstrate Azure OpenAI service functionality."""
    print("🔧 Azure OpenAI Service Demo")
    print("=" * 50)
    
    config = setup_demo_config()
    
    if not config.azure_openai.api_key or not config.azure_openai.endpoint:
        print("❌ Azure OpenAI not configured!")
        print("Please set the following environment variables:")
        print("- AZURE_OPENAI_API_KEY")
        print("- AZURE_OPENAI_ENDPOINT")
        print("- AZURE_OPENAI_CHAT_MODEL (optional)")
        print("- AZURE_OPENAI_EMBEDDING_MODEL (optional)")
        return
    
    try:
        # Initialize service
        service = AzureOpenAIService(config.azure_openai)
        print(f"✅ Azure OpenAI service initialized")
        print(f"   Endpoint: {config.azure_openai.endpoint}")
        print(f"   Chat Model: {config.azure_openai.chat_model}")
        print(f"   Embedding Model: {config.azure_openai.embedding_model}")
        
        # Test connection
        print("\n🔍 Testing connection...")
        if service.test_connection():
            print("✅ Connection test successful!")
        else:
            print("❌ Connection test failed!")
            return
        
        # Demo chat completion
        print("\n💬 Testing chat completion...")
        messages = [
            ChatMessage(role="system", content="You are a helpful coding assistant."),
            ChatMessage(role="user", content="Explain what a Python decorator is in one sentence."),
        ]
        
        response = service.chat_completion(messages, max_tokens=100)
        print(f"✅ Chat response: {response.content}")
        print(f"   Model: {response.model}")
        print(f"   Usage: {response.usage}")
        
        # Demo embeddings
        print("\n🔢 Testing embeddings...")
        texts = [
            "def hello_world(): print('Hello, World!')",
            "class MyClass: pass",
            "import numpy as np",
        ]
        
        embedding_response = service.generate_embeddings(texts)
        print(f"✅ Generated {len(embedding_response.embeddings)} embeddings")
        print(f"   Dimension: {len(embedding_response.embeddings[0])}")
        print(f"   Model: {embedding_response.model}")
        print(f"   Usage: {embedding_response.usage}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def demo_ai_generators():
    """Demonstrate AI-powered generators."""
    print("\n🤖 AI-Powered Generators Demo")
    print("=" * 50)
    
    config = setup_demo_config()
    
    if not config.azure_openai.api_key or not config.azure_openai.endpoint:
        print("❌ Azure OpenAI not configured! Skipping AI generators demo.")
        return
    
    try:
        # Create generator factory
        factory = GeneratorFactory(config)
        print(f"✅ Generator factory created")
        print(f"   Using AI: {factory.is_using_ai()}")
        print(f"   Info: {factory.get_generator_info()}")
        
        # Create specification generator
        spec_generator = factory.create_specification_generator()
        print(f"✅ Specification generator: {type(spec_generator).__name__}")
        
        # Create design generator
        design_generator = factory.create_design_generator()
        print(f"✅ Design generator: {type(design_generator).__name__}")
        
        # Create task generator
        task_generator = factory.create_task_generator()
        print(f"✅ Task generator: {type(task_generator).__name__}")
        
        # Demo specification generation from user input
        print("\n📝 Testing specification generation...")
        user_requirements = [
            "Create a REST API for user management",
            "Support user authentication and authorization",
            "Provide CRUD operations for user profiles",
            "Include data validation and error handling",
        ]
        
        if hasattr(spec_generator, 'generate_from_user_input'):
            try:
                spec_doc = spec_generator.generate_from_user_input(user_requirements)
                print(f"✅ Generated specification: {spec_doc.title}")
                print(f"   Features: {len(spec_doc.key_features)}")
                print(f"   Requirements: {len(spec_doc.functional_requirements)}")
                
                # Show first few features
                if spec_doc.key_features:
                    print("   Key features:")
                    for feature in spec_doc.key_features[:3]:
                        print(f"   - {feature}")
                
            except Exception as e:
                print(f"❌ Specification generation failed: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def demo_enhanced_indexing():
    """Demonstrate enhanced indexing with Azure embeddings."""
    print("\n🔍 Enhanced Indexing Demo")
    print("=" * 50)
    
    config = setup_demo_config()
    
    # Use current directory as demo project
    project_path = str(Path(__file__).parent.parent)
    
    try:
        # Create enhanced indexing engine
        indexing_engine = create_indexing_engine(project_path, config)
        print(f"✅ Enhanced indexing engine created")
        print(f"   Project path: {project_path}")
        print(f"   Using Azure embeddings: {config.indexing.use_azure_embeddings}")
        
        # Test Azure connection if enabled
        if config.indexing.use_azure_embeddings:
            print("\n🔗 Testing Azure connection for embeddings...")
            if indexing_engine.test_azure_connection():
                print("✅ Azure embeddings connection successful!")
            else:
                print("❌ Azure embeddings connection failed, will use local embeddings")
        
        # Get vector database stats
        print("\n📊 Vector database stats:")
        stats = indexing_engine.get_vector_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Demo similarity search (if index exists)
        print("\n🔍 Testing similarity search...")
        try:
            matches = indexing_engine.query_similar_code(
                "function that processes user input", 
                limit=3,
                threshold=0.5
            )
            
            if matches:
                print(f"✅ Found {len(matches)} similar code matches:")
                for i, match in enumerate(matches[:2], 1):
                    print(f"   {i}. {match.file_path}:{match.start_line}-{match.end_line}")
                    print(f"      Similarity: {match.similarity_score:.3f}")
                    print(f"      Type: {match.chunk_type}")
            else:
                print("ℹ️  No similar code matches found (index may be empty)")
                
        except Exception as e:
            print(f"⚠️  Similarity search failed: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def demo_async_operations():
    """Demonstrate async Azure OpenAI operations."""
    print("\n⚡ Async Operations Demo")
    print("=" * 50)
    
    config = setup_demo_config()
    
    if not config.azure_openai.api_key or not config.azure_openai.endpoint:
        print("❌ Azure OpenAI not configured! Skipping async demo.")
        return
    
    try:
        service = AzureOpenAIService(config.azure_openai)
        
        # Test async connection
        print("🔍 Testing async connection...")
        if await service.async_test_connection():
            print("✅ Async connection test successful!")
        else:
            print("❌ Async connection test failed!")
            return
        
        # Demo async chat completion
        print("\n💬 Testing async chat completion...")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is async programming?"},
        ]
        
        response = await service.async_chat_completion(messages, max_tokens=50)
        print(f"✅ Async chat response: {response.content}")
        
        # Demo async embeddings
        print("\n🔢 Testing async embeddings...")
        texts = ["async def example(): pass", "await some_function()"]
        
        embedding_response = await service.async_generate_embeddings(texts)
        print(f"✅ Generated {len(embedding_response.embeddings)} async embeddings")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all demos."""
    print("🚀 Dev-Agent Azure OpenAI Integration Demo")
    print("=" * 60)
    
    # Check environment variables
    required_vars = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("⚠️  Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables and run the demo again.")
        print("\nExample:")
        print("export AZURE_OPENAI_API_KEY='your-api-key'")
        print("export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'")
        print("export AZURE_OPENAI_CHAT_MODEL='gpt-4'  # optional")
        print("export AZURE_OPENAI_EMBEDDING_MODEL='text-embedding-ada-002'  # optional")
        return
    
    # Run demos
    demo_azure_service()
    demo_ai_generators()
    demo_enhanced_indexing()
    
    # Run async demo
    print("\n" + "=" * 60)
    asyncio.run(demo_async_operations())
    
    print("\n🎉 Demo completed!")
    print("\nTo use Azure OpenAI in dev-agent:")
    print("1. Configure: dev-agent azure configure")
    print("2. Test: dev-agent azure test")
    print("3. Check status: dev-agent azure status")


if __name__ == "__main__":
    main()