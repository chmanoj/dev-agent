"""Memory-efficient streaming for large file processing and code generation."""

from __future__ import annotations

import asyncio
import gc
import logging
import mmap
import os
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Dict, Generator, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class StreamingConfig:
    """Configuration for memory streaming."""
    
    chunk_size: int = 8192  # 8KB chunks
    buffer_size: int = 1024 * 1024  # 1MB buffer
    max_memory_usage_mb: int = 512  # 512MB max memory
    enable_compression: bool = True
    enable_memory_mapping: bool = True
    memory_map_threshold: int = 10 * 1024 * 1024  # 10MB threshold
    temp_dir: Optional[str] = None
    enable_gc_optimization: bool = True
    gc_threshold: int = 100  # Trigger GC every N chunks


@dataclass
class StreamingMetrics:
    """Metrics for streaming operations."""
    
    bytes_processed: int = 0
    chunks_processed: int = 0
    memory_peak_mb: float = 0.0
    processing_time: float = 0.0
    compression_ratio: float = 1.0
    cache_hits: int = 0
    cache_misses: int = 0


class MemoryStreamer:
    """Memory-efficient streaming system for large file processing."""

    def __init__(self, config: Optional[StreamingConfig] = None):
        """Initialize the memory streamer.
        
        Args:
            config: Streaming configuration
        """
        self.config = config or StreamingConfig()
        self.metrics = StreamingMetrics()
        
        # Setup temporary directory
        self.temp_dir = Path(self.config.temp_dir) if self.config.temp_dir else Path(tempfile.gettempdir())
        self.temp_dir.mkdir(exist_ok=True)
        
        # Memory management
        self._memory_usage = 0
        self._active_streams = {}
        self._chunk_cache = {}
        
        logger.info(f"MemoryStreamer initialized with {self.config.chunk_size} byte chunks")

    @contextmanager
    def stream_file(self, file_path: Union[str, Path], mode: str = 'rb'):
        """Context manager for streaming file access.
        
        Args:
            file_path: Path to the file
            mode: File open mode
            
        Yields:
            File stream or memory-mapped file
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = file_path.stat().st_size
        
        # Use memory mapping for large files
        if (self.config.enable_memory_mapping and 
            file_size > self.config.memory_map_threshold and
            'b' in mode):
            
            with open(file_path, mode) as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    yield mm
        else:
            # Regular file streaming
            with open(file_path, mode, buffering=self.config.buffer_size) as f:
                yield f

    def stream_file_chunks(
        self,
        file_path: Union[str, Path],
        chunk_size: Optional[int] = None,
    ) -> Generator[bytes, None, None]:
        """Stream file in chunks.
        
        Args:
            file_path: Path to the file
            chunk_size: Size of each chunk (uses config default if None)
            
        Yields:
            File chunks as bytes
        """
        chunk_size = chunk_size or self.config.chunk_size
        
        with self.stream_file(file_path, 'rb') as f:
            chunk_count = 0
            
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                yield chunk
                
                # Update metrics
                self.metrics.bytes_processed += len(chunk)
                self.metrics.chunks_processed += 1
                chunk_count += 1
                
                # Trigger garbage collection periodically
                if (self.config.enable_gc_optimization and 
                    chunk_count % self.config.gc_threshold == 0):
                    gc.collect()

    async def stream_file_chunks_async(
        self,
        file_path: Union[str, Path],
        chunk_size: Optional[int] = None,
    ) -> AsyncGenerator[bytes, None]:
        """Asynchronously stream file in chunks.
        
        Args:
            file_path: Path to the file
            chunk_size: Size of each chunk
            
        Yields:
            File chunks as bytes
        """
        chunk_size = chunk_size or self.config.chunk_size
        
        def read_chunk(f, size):
            return f.read(size)
        
        with self.stream_file(file_path, 'rb') as f:
            chunk_count = 0
            
            while True:
                # Read chunk in executor to avoid blocking
                loop = asyncio.get_event_loop()
                chunk = await loop.run_in_executor(None, read_chunk, f, chunk_size)
                
                if not chunk:
                    break
                
                yield chunk
                
                # Update metrics
                self.metrics.bytes_processed += len(chunk)
                self.metrics.chunks_processed += 1
                chunk_count += 1
                
                # Yield control to event loop
                await asyncio.sleep(0)
                
                # Trigger garbage collection periodically
                if (self.config.enable_gc_optimization and 
                    chunk_count % self.config.gc_threshold == 0):
                    gc.collect()

    def process_large_file(
        self,
        file_path: Union[str, Path],
        processor: Callable[[bytes], Any],
        output_path: Optional[Union[str, Path]] = None,
    ) -> Any:
        """Process a large file in memory-efficient chunks.
        
        Args:
            file_path: Path to input file
            processor: Function to process each chunk
            output_path: Optional output file path
            
        Returns:
            Processing result
        """
        start_time = time.time()
        results = []
        
        # Setup output file if specified
        output_file = None
        if output_path:
            output_file = open(output_path, 'wb')
        
        try:
            for chunk in self.stream_file_chunks(file_path):
                # Process chunk
                result = processor(chunk)
                
                if result is not None:
                    results.append(result)
                    
                    # Write to output file if specified
                    if output_file and isinstance(result, bytes):
                        output_file.write(result)
                
                # Check memory usage
                self._check_memory_usage()
            
            # Update metrics
            self.metrics.processing_time = time.time() - start_time
            
            return results
            
        finally:
            if output_file:
                output_file.close()

    async def process_large_file_async(
        self,
        file_path: Union[str, Path],
        processor: Callable[[bytes], Any],
        output_path: Optional[Union[str, Path]] = None,
        max_concurrent_chunks: int = 10,
    ) -> Any:
        """Asynchronously process a large file in chunks.
        
        Args:
            file_path: Path to input file
            processor: Function to process each chunk
            output_path: Optional output file path
            max_concurrent_chunks: Maximum concurrent chunk processing
            
        Returns:
            Processing result
        """
        start_time = time.time()
        results = []
        
        # Semaphore to limit concurrent processing
        semaphore = asyncio.Semaphore(max_concurrent_chunks)
        
        async def process_chunk(chunk_data):
            async with semaphore:
                # Run processor in executor if it's not async
                if asyncio.iscoroutinefunction(processor):
                    return await processor(chunk_data)
                else:
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(None, processor, chunk_data)
        
        # Process chunks concurrently
        tasks = []
        async for chunk in self.stream_file_chunks_async(file_path):
            task = asyncio.create_task(process_chunk(chunk))
            tasks.append(task)
            
            # Limit number of concurrent tasks
            if len(tasks) >= max_concurrent_chunks:
                # Wait for some tasks to complete
                done, pending = await asyncio.wait(
                    tasks, 
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Collect results
                for task in done:
                    result = await task
                    if result is not None:
                        results.append(result)
                
                tasks = list(pending)
        
        # Wait for remaining tasks
        if tasks:
            remaining_results = await asyncio.gather(*tasks)
            results.extend([r for r in remaining_results if r is not None])
        
        # Update metrics
        self.metrics.processing_time = time.time() - start_time
        
        return results

    def stream_code_generation(
        self,
        generator_func: Callable[..., Generator[str, None, None]],
        output_path: Union[str, Path],
        *args,
        **kwargs,
    ) -> None:
        """Stream code generation output to file.
        
        Args:
            generator_func: Function that yields code strings
            output_path: Path to output file
            *args: Arguments for generator function
            **kwargs: Keyword arguments for generator function
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8', buffering=self.config.buffer_size) as f:
            for code_chunk in generator_func(*args, **kwargs):
                f.write(code_chunk)
                
                # Update metrics
                self.metrics.bytes_processed += len(code_chunk.encode('utf-8'))
                
                # Check memory usage
                self._check_memory_usage()

    async def stream_code_generation_async(
        self,
        generator_func: Callable[..., AsyncGenerator[str, None]],
        output_path: Union[str, Path],
        *args,
        **kwargs,
    ) -> None:
        """Asynchronously stream code generation output to file.
        
        Args:
            generator_func: Async function that yields code strings
            output_path: Path to output file
            *args: Arguments for generator function
            **kwargs: Keyword arguments for generator function
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8', buffering=self.config.buffer_size) as f:
            async for code_chunk in generator_func(*args, **kwargs):
                f.write(code_chunk)
                
                # Update metrics
                self.metrics.bytes_processed += len(code_chunk.encode('utf-8'))
                
                # Yield control to event loop
                await asyncio.sleep(0)
                
                # Check memory usage
                self._check_memory_usage()

    def create_temporary_stream(self, prefix: str = "stream_") -> Path:
        """Create a temporary file for streaming operations.
        
        Args:
            prefix: Prefix for temporary file name
            
        Returns:
            Path to temporary file
        """
        temp_file = tempfile.NamedTemporaryFile(
            prefix=prefix,
            dir=self.temp_dir,
            delete=False,
        )
        temp_file.close()
        
        temp_path = Path(temp_file.name)
        self._active_streams[str(temp_path)] = temp_path
        
        return temp_path

    def cleanup_temporary_streams(self) -> None:
        """Clean up all temporary streams."""
        for stream_path in list(self._active_streams.values()):
            try:
                if stream_path.exists():
                    stream_path.unlink()
                self._active_streams.pop(str(stream_path), None)
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary stream {stream_path}: {e}")

    def batch_process_files(
        self,
        file_paths: List[Union[str, Path]],
        processor: Callable[[bytes], Any],
        batch_size: int = 10,
    ) -> List[Any]:
        """Process multiple files in memory-efficient batches.
        
        Args:
            file_paths: List of file paths to process
            processor: Function to process file content
            batch_size: Number of files to process in each batch
            
        Returns:
            List of processing results
        """
        results = []
        
        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i:i + batch_size]
            batch_results = []
            
            for file_path in batch:
                try:
                    file_result = self.process_large_file(file_path, processor)
                    batch_results.append(file_result)
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    batch_results.append(None)
            
            results.extend(batch_results)
            
            # Force garbage collection between batches
            if self.config.enable_gc_optimization:
                gc.collect()
        
        return results

    def get_streaming_metrics(self) -> StreamingMetrics:
        """Get current streaming metrics.
        
        Returns:
            Current streaming metrics
        """
        # Update memory peak
        current_memory = self._get_memory_usage_mb()
        if current_memory > self.metrics.memory_peak_mb:
            self.metrics.memory_peak_mb = current_memory
        
        return self.metrics

    def reset_metrics(self) -> None:
        """Reset streaming metrics."""
        self.metrics = StreamingMetrics()

    def _check_memory_usage(self) -> None:
        """Check current memory usage and trigger cleanup if needed."""
        current_memory = self._get_memory_usage_mb()
        
        if current_memory > self.config.max_memory_usage_mb:
            logger.warning(f"Memory usage ({current_memory:.1f}MB) exceeds limit ({self.config.max_memory_usage_mb}MB)")
            
            # Force garbage collection
            gc.collect()
            
            # Clear chunk cache if it exists
            if hasattr(self, '_chunk_cache'):
                self._chunk_cache.clear()
            
            # Update memory usage
            current_memory = self._get_memory_usage_mb()
            logger.info(f"Memory usage after cleanup: {current_memory:.1f}MB")

    def _get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            # Fallback to basic estimation
            return 0.0

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup_temporary_streams()


class StreamingCodeGenerator:
    """Streaming code generator for large code generation tasks."""

    def __init__(self, memory_streamer: MemoryStreamer):
        """Initialize streaming code generator.
        
        Args:
            memory_streamer: Memory streamer instance
        """
        self.memory_streamer = memory_streamer
        self.generation_buffer = []
        self.buffer_size_limit = 1024 * 1024  # 1MB buffer limit

    def generate_code_stream(
        self,
        template: str,
        data_source: Union[List[Dict], Callable[[], Generator[Dict, None, None]]],
        output_path: Union[str, Path],
    ) -> None:
        """Generate code using streaming approach.
        
        Args:
            template: Code template string
            data_source: Data source (list or generator function)
            output_path: Output file path
        """
        def code_generator():
            if isinstance(data_source, list):
                # Process list in chunks
                for item in data_source:
                    yield self._render_template(template, item)
            else:
                # Process generator
                for item in data_source():
                    yield self._render_template(template, item)
        
        self.memory_streamer.stream_code_generation(
            code_generator,
            output_path,
        )

    async def generate_code_stream_async(
        self,
        template: str,
        data_source: Union[List[Dict], Callable[[], AsyncGenerator[Dict, None]]],
        output_path: Union[str, Path],
    ) -> None:
        """Asynchronously generate code using streaming approach.
        
        Args:
            template: Code template string
            data_source: Async data source
            output_path: Output file path
        """
        async def async_code_generator():
            if isinstance(data_source, list):
                # Process list in chunks
                for item in data_source:
                    yield self._render_template(template, item)
                    await asyncio.sleep(0)  # Yield control
            else:
                # Process async generator
                async for item in data_source():
                    yield self._render_template(template, item)
        
        await self.memory_streamer.stream_code_generation_async(
            async_code_generator,
            output_path,
        )

    def _render_template(self, template: str, data: Dict[str, Any]) -> str:
        """Render template with data.
        
        Args:
            template: Template string
            data: Data dictionary
            
        Returns:
            Rendered code string
        """
        # Simple template rendering (in practice, use Jinja2 or similar)
        try:
            return template.format(**data)
        except KeyError as e:
            logger.warning(f"Template rendering error: missing key {e}")
            return f"# Template rendering error: missing key {e}\n"


class StreamingFileProcessor:
    """Streaming processor for large file operations."""

    def __init__(self, memory_streamer: MemoryStreamer):
        """Initialize streaming file processor.
        
        Args:
            memory_streamer: Memory streamer instance
        """
        self.memory_streamer = memory_streamer

    def merge_files_streaming(
        self,
        input_paths: List[Union[str, Path]],
        output_path: Union[str, Path],
        separator: str = "\n",
    ) -> None:
        """Merge multiple files using streaming approach.
        
        Args:
            input_paths: List of input file paths
            output_path: Output file path
            separator: Separator between files
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as output_file:
            for i, input_path in enumerate(input_paths):
                # Add separator between files (except first)
                if i > 0:
                    output_file.write(separator.encode('utf-8'))
                
                # Stream file content
                for chunk in self.memory_streamer.stream_file_chunks(input_path):
                    output_file.write(chunk)

    def split_file_streaming(
        self,
        input_path: Union[str, Path],
        output_dir: Union[str, Path],
        max_size_mb: int = 100,
    ) -> List[Path]:
        """Split large file into smaller chunks using streaming.
        
        Args:
            input_path: Input file path
            output_dir: Output directory
            max_size_mb: Maximum size per chunk in MB
            
        Returns:
            List of output file paths
        """
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        max_size_bytes = max_size_mb * 1024 * 1024
        output_files = []
        
        current_size = 0
        current_file_index = 0
        current_output_file = None
        
        try:
            for chunk in self.memory_streamer.stream_file_chunks(input_path):
                # Check if we need a new output file
                if current_output_file is None or current_size >= max_size_bytes:
                    # Close current file
                    if current_output_file:
                        current_output_file.close()
                    
                    # Create new output file
                    output_path = output_dir / f"{input_path.stem}_part_{current_file_index:03d}{input_path.suffix}"
                    current_output_file = open(output_path, 'wb')
                    output_files.append(output_path)
                    current_file_index += 1
                    current_size = 0
                
                # Write chunk to current file
                current_output_file.write(chunk)
                current_size += len(chunk)
        
        finally:
            if current_output_file:
                current_output_file.close()
        
        return output_files