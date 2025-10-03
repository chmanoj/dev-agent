# Integration Tests

This directory contains integration tests that use real Azure OpenAI API calls to verify end-to-end functionality.

## Prerequisites

1. **Azure OpenAI Resource**: You need an active Azure OpenAI resource with:
   - GPT-4 deployment (or GPT-3.5-turbo)
   - text-embedding-ada-002 deployment

2. **Environment Variables**: Configure the following environment variables:

```bash
export AZURE_OPENAI_INTEGRATION_TESTS=true
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
export AZURE_OPENAI_API_KEY=your-api-key-here
export AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

## Running Integration Tests

### Run All Integration Tests

```bash
# Set environment variables first
export AZURE_OPENAI_INTEGRATION_TESTS=true
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
export AZURE_OPENAI_API_KEY=your-api-key-here
export AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Run tests
uv run pytest tests/integration/ -v
```

### Run Specific Test

```bash
uv run pytest tests/integration/test_azure_openai_integration.py::test_real_completion_generation -v
```

### Run with Coverage

```bash
uv run pytest tests/integration/ --cov=dev_agent.llm --cov-report=html -v
```

## Test Coverage

The integration test suite covers:

1. **Basic LLM Operations**
   - Completion generation
   - Streaming responses
   - Token counting
   - Cost estimation

2. **Embedding Operations**
   - Single text embedding
   - Batch embedding generation
   - Embedding cache functionality

3. **End-to-End Workflows**
   - Specification generation
   - Code generation
   - Vector search with real embeddings

4. **Cost Tracking**
   - Token usage tracking
   - Cost estimation across workflow phases
   - Budget monitoring

5. **Error Handling**
   - Authentication errors
   - Retry logic
   - Error recovery

6. **Performance Benchmarks**
   - Completion generation speed
   - Embedding generation speed
   - Vector search performance

## Cost Considerations

**WARNING**: These tests make real API calls to Azure OpenAI and will incur costs.

Estimated costs per full test run:
- Completion tests: ~$0.10 - $0.50
- Embedding tests: ~$0.01 - $0.05
- Total: ~$0.15 - $0.60 per run

To minimize costs:
- Run tests selectively using specific test names
- Use GPT-3.5-turbo instead of GPT-4 for testing (update AZURE_OPENAI_DEPLOYMENT_NAME)
- Set lower max_tokens values in test configuration

## Troubleshooting

### Tests are Skipped

If you see "Integration tests disabled", ensure:
1. `AZURE_OPENAI_INTEGRATION_TESTS=true` is set
2. All required environment variables are configured
3. Environment variables are exported in the current shell

### Authentication Errors

If you see authentication errors:
1. Verify your API key is correct
2. Check that your Azure OpenAI resource is active
3. Ensure your endpoint URL is correct (should end with `.openai.azure.com/`)

### Rate Limiting

If you hit rate limits:
1. Wait a few minutes before retrying
2. Reduce the number of concurrent tests
3. Check your Azure OpenAI quota limits

### Timeout Errors

If tests timeout:
1. Check your network connection
2. Verify Azure OpenAI service status
3. Increase timeout values in test configuration

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run Integration Tests
  env:
    AZURE_OPENAI_INTEGRATION_TESTS: true
    AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
    AZURE_OPENAI_API_KEY: ${{ secrets.AZURE_OPENAI_API_KEY }}
    AZURE_OPENAI_DEPLOYMENT_NAME: ${{ secrets.AZURE_OPENAI_DEPLOYMENT_NAME }}
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: ${{ secrets.AZURE_OPENAI_EMBEDDING_DEPLOYMENT }}
  run: |
    uv run pytest tests/integration/ -v
```

## Best Practices

1. **Run Locally First**: Test your configuration locally before adding to CI/CD
2. **Use Secrets**: Never commit API keys - use environment variables or secrets management
3. **Monitor Costs**: Track API usage and costs in Azure Portal
4. **Selective Testing**: Run only necessary tests to minimize costs
5. **Cache Results**: Use embedding cache to reduce duplicate API calls

## Support

For issues or questions:
- Check the main documentation: `docs/configuration/azure-openai.md`
- Review troubleshooting guide: `docs/configuration/troubleshooting.md`
- Open an issue on GitHub
