"""Performance optimization utilities for dev-agent.

This module provides performance monitoring and optimization utilities
to ensure dev-agent meets performance targets:
- Indexing: 100+ files/second
- Embedding batch processing: 16 items per batch
- Embedding caching: Avoid re-computation
- FAISS vector search: O(log n) performance
- CLI responsiveness: <100ms command parsing
- State persistence: <100ms save operations
"""

from __future__ import annotations

__all__ = [
    "PerformanceMonitor",
    "measure_time",
    "optimize_batch_size",
]

from .monitor import PerformanceMonitor, measure_time, optimize_batch_size
