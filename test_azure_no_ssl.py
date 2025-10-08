#!/usr/bin/env python3
"""
Test Azure OpenAI connection WITHOUT SSL verification.
⚠️  WARNING: This is INSECURE and only for diagnostic purposes!

This script helps confirm that SSL certificate verification is the only issue.
If this works, you know the problem is SSL certs, not auth/network/config.
"""

import asyncio
import os
import sys
import warnings

# Suppress SSL warnings since we're intentionally disabling verification
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

try:
    import httpx
    from openai import AsyncAzureOpenAI
except ImportError:
    print("❌ Missing dependencies. Install with:")
    print("   uv pip install httpx openai")
    sys.exit(1)


async def test_without_ssl_verification():
    """Test connection without SSL verification - DIAGNOSTIC ONLY!"""
    
    print("="*70)
    print("⚠️  SSL VERIFICATION DISABLED - DIAGNOSTIC TEST ONLY")
    print("="*70)
    print()
    print("This test will attempt to connect to Azure OpenAI WITHOUT verifying")
    print("SSL certificates. This is INSECURE and should NEVER be used in")
    print("production. It's only to confirm that SSL certificates are the issue.")
    print()
    
    # Get configuration from environment
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    bearer_token = os.getenv("AZURE_OPENAI_TOKEN")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    if not endpoint:
        print("❌ AZURE_OPENAI_ENDPOINT not set")
        return False
    
    if not (api_key or bearer_token):
        print("❌ AZURE_OPENAI_API_KEY or AZURE_OPENAI_TOKEN not set")
        return False
    
    if not deployment:
        print("❌ AZURE_OPENAI_DEPLOYMENT_NAME not set")
        return False
    
    print("Configuration:")
    print(f"  Endpoint: {endpoint}")
    print(f"  Deployment: {deployment}")
    print(f"  API Version: {api_version}")
    print(f"  Auth Method: {'Bearer Token' if bearer_token else 'API Key'}")
    print()
    
    # Create HTTP client that doesn't verify SSL
    print("Creating HTTP client with SSL verification DISABLED...")
    http_client = httpx.AsyncClient(verify=False)
    
    # Prepare authentication
    auth_value = bearer_token if bearer_token else api_key
    
    # Create Azure OpenAI client with custom HTTP client
    print("Creating Azure OpenAI client...")
    client = AsyncAzureOpenAI(
        api_key=auth_value,
        api_version=api_version,
        azure_endpoint=endpoint,
        http_client=http_client,
    )
    
    try:
        print("Sending test request to Azure OpenAI...")
        print()
        
        response = await client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Connection successful!' if you can read this."}
            ],
            max_tokens=20,
        )
        
        result = response.choices[0].message.content
        
        print("="*70)
        print("✅ SUCCESS - Connection Works Without SSL Verification!")
        print("="*70)
        print()
        print(f"Response: {result}")
        print()
        print("="*70)
        print("DIAGNOSIS: SSL Certificate Verification is the Problem")
        print("="*70)
        print()
        print("Your Azure OpenAI configuration is correct:")
        print("  ✅ Endpoint is reachable")
        print("  ✅ API key/token is valid")
        print("  ✅ Deployment name is correct")
        print("  ✅ Network connectivity works")
        print()
        print("The ONLY issue is SSL certificate verification.")
        print()
        print("NEXT STEPS:")
        print("  1. Read: FIX_SSL_CERTIFICATE_ERROR.md")
        print("  2. Try: /Applications/Python 3.*/Install Certificates.command (macOS)")
        print("  3. Or: uv pip install --upgrade certifi")
        print("  4. Or: export SSL_CERT_FILE=$(python3 -c 'import certifi; print(certifi.where())')")
        print()
        print("DO NOT use this script in production - fix SSL certificates properly!")
        print("="*70)
        
        return True
        
    except Exception as e:
        print("="*70)
        print("❌ FAILED - Even Without SSL Verification")
        print("="*70)
        print()
        print(f"Error: {type(e).__name__}: {e}")
        print()
        print("This means the problem is NOT just SSL certificates.")
        print("Possible issues:")
        print("  • Wrong API key or bearer token")
        print("  • Wrong endpoint URL")
        print("  • Wrong deployment name")
        print("  • Network/firewall blocking connection")
        print("  • Azure OpenAI service issue")
        print()
        
        import traceback
        print("Full error details:")
        print("-"*70)
        traceback.print_exc()
        print("-"*70)
        
        return False
        
    finally:
        await http_client.aclose()


async def test_embedding_without_ssl():
    """Test embedding endpoint without SSL verification."""
    
    print("\n" + "="*70)
    print("Testing Embedding Endpoint (SSL Disabled)")
    print("="*70)
    print()
    
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    bearer_token = os.getenv("AZURE_OPENAI_TOKEN")
    embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    if not embedding_deployment:
        print("⚠️  AZURE_OPENAI_EMBEDDING_DEPLOYMENT not set, skipping embedding test")
        return False
    
    http_client = httpx.AsyncClient(verify=False)
    auth_value = bearer_token if bearer_token else api_key
    
    client = AsyncAzureOpenAI(
        api_key=auth_value,
        api_version=api_version,
        azure_endpoint=endpoint,
        http_client=http_client,
    )
    
    try:
        print("Sending test embedding request...")
        
        response = await client.embeddings.create(
            model=embedding_deployment,
            input=["test embedding"],
        )
        
        embedding = response.data[0].embedding
        dimension = len(embedding)
        
        print(f"✅ Embedding test successful!")
        print(f"   Dimension: {dimension}")
        print(f"   Expected: 1536 (for text-embedding-ada-002)")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding test failed: {e}")
        return False
        
    finally:
        await http_client.aclose()


async def main():
    """Main test function."""
    
    # Test completion
    completion_success = await test_without_ssl_verification()
    
    # Test embedding if completion worked
    embedding_success = False
    if completion_success:
        embedding_success = await test_embedding_without_ssl()
    
    print()
    
    if completion_success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
