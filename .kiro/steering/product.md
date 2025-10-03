# Product Overview

dev-agent is an AI-powered development workflow assistant that implements a structured four-phase development process for Python projects, leveraging Azure OpenAI for intelligent code analysis and generation.

## Core Purpose
- Analyze existing large codebases through comprehensive local indexing with Azure OpenAI embeddings
- Generate specifications, designs, and implementation plans using GPT-4
- Provide context-aware code generation consistent with existing patterns
- Maintain persistent state across development sessions
- Ensure enterprise-grade security with Azure OpenAI integration

## Four-Phase Workflow

### 1. Indexing Phase
- **Tree-sitter Parsing**: Analyzes Python code structure (AST, functions, classes, imports)
- **Azure OpenAI Embeddings**: Generates semantic embeddings via text-embedding-ada-002
- **FAISS Vector Storage**: Stores embeddings for efficient similarity search
- **Pattern Detection**: Identifies coding patterns, conventions, and architecture

### 2. Specification Phase
- **Context Retrieval**: Uses vector similarity to find relevant code examples
- **GPT-4 Generation**: Creates detailed specifications based on codebase analysis
- **User Approval**: Requires explicit approval before proceeding
- **Document Storage**: Saves specifications in `.dev_agent/documents/`

### 3. Design Phase
- **Architecture Analysis**: Understands existing design patterns
- **GPT-4 Design**: Generates technical design documents consistent with codebase
- **Pattern Matching**: Ensures new designs align with existing architecture
- **User Approval**: Gate before implementation

### 4. Implementation Phase
- **Context-Aware Generation**: GPT-4 generates code matching existing patterns
- **Style Consistency**: Maintains coding style from analyzed codebase
- **Test Generation**: Creates tests following project conventions
- **Incremental Development**: Supports iterative implementation with feedback

## Key Features

### AI-Powered Intelligence
- **Azure OpenAI Integration**: Enterprise-grade GPT-4 for code generation
- **Semantic Code Search**: Vector embeddings for finding relevant code
- **Pattern Learning**: Understands and replicates codebase conventions
- **Context-Aware**: Generates code that "fits" your project

### Developer Experience
- **Interactive CLI**: Chat-based interface with Rich terminal output
- **Session Management**: Persistent state across CLI invocations
- **User Approval Workflows**: Human-in-the-loop for quality control
- **Streaming Responses**: Real-time feedback during generation

### Enterprise Ready
- **Secure by Default**: API keys via environment variables only
- **Azure Integration**: Leverages existing Azure infrastructure
- **Cost Tracking**: Monitor token usage and API costs
- **Audit Logging**: Track all AI operations

### Performance & Scalability
- **Efficient Indexing**: Handles large codebases (10K+ files)
- **FAISS Vector Search**: O(log n) similarity search
- **Async API Calls**: Non-blocking Azure OpenAI requests
- **Batch Processing**: Optimized embedding generation

## Target Users

### Primary Audience
- **Enterprise Python Developers**: Working with large, complex codebases
- **Development Teams**: Need consistent code generation across team members
- **Tech Leads**: Want AI assistance that respects existing architecture
- **Organizations**: Using Azure infrastructure and require secure AI integration

### Use Cases
- **Feature Development**: Generate new features matching existing patterns
- **Code Documentation**: Create specs and designs for existing code
- **Refactoring**: Understand codebase before making changes
- **Onboarding**: Help new developers understand large codebases
- **Technical Debt**: Document undocumented legacy code

## Differentiators

### vs. Generic Code Assistants
- **Codebase-Specific**: Learns YOUR patterns, not generic examples
- **Structured Workflow**: Four-phase process with approval gates
- **Persistent Context**: Maintains understanding across sessions
- **Enterprise Security**: Azure OpenAI with your credentials

### vs. Local AI Tools
- **No GPU Required**: All AI operations via Azure OpenAI API
- **Latest Models**: Access to GPT-4, GPT-4 Turbo, GPT-4o
- **Scalable**: No local resource constraints
- **Always Updated**: Benefit from OpenAI model improvements

## Technology Stack
- **AI Provider**: Azure OpenAI (GPT-4 + text-embedding-ada-002)
- **Language**: Python 3.10+ with modern async/await patterns
- **Vector DB**: FAISS for local embedding storage
- **CLI**: Typer + Rich for interactive terminal experience
- **Code Analysis**: Tree-sitter for AST parsing

## Future Roadmap
- **Multi-Language Support**: Extend beyond Python (JavaScript, TypeScript, Go)
- **AWS Bedrock Integration**: Support Claude 3 models as alternative
- **Team Collaboration**: Shared project state and knowledge base
- **IDE Integration**: VS Code extension for inline assistance
- **Cost Optimization**: Automatic model selection based on task complexity