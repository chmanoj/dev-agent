"""Audit system for verifying dev-agent core functionality.

This module provides comprehensive auditing capabilities to verify that all
core features of dev-agent are functioning correctly, including:
- Indexing phase (Tree-sitter, FAISS, Azure OpenAI embeddings)
- Specification phase (GPT-4 generation)
- Design phase (design document generation)
- Implementation phase (task generation)
- State management (persistence and recovery)
- Azure OpenAI integration (API connectivity, token counting, cost tracking)
- Error handling (graceful degradation)
"""

from dev_agent.audit.audit_engine import AuditEngine
from dev_agent.audit.models import AuditReport, AuditResult

__all__ = ["AuditEngine", "AuditReport", "AuditResult"]
