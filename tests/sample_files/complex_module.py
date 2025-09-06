"""A complex Python module with various language features."""

import os
import sys
from typing import List, Dict, Optional, Union, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import wraps, lru_cache
import json

# Module-level constants
DEFAULT_CONFIG = {
    'debug': False,
    'max_retries': 3,
    'timeout': 30
}

@dataclass
class Config:
    """Configuration data class."""
    debug: bool = False
    max_retries: int = 3
    timeout: int = 30
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create config from dictionary."""
        return cls(**data)

def retry(max_attempts: int = 3):
    """Decorator for retrying failed operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise e
                    continue
            return None
        return wrapper
    return decorator

class ProcessorError(Exception):
    """Custom exception for processor errors."""
    
    def __init__(self, message: str, error_code: int = 500):
        super().__init__(message)
        self.error_code = error_code

class BaseProcessor(ABC):
    """Abstract base class for processors."""
    
    def __init__(self, name: str, config: Optional[Config] = None):
        self.name = name
        self.config = config or Config()
        self._processed_count = 0
    
    @property
    def processed_count(self) -> int:
        """Get number of processed items."""
        return self._processed_count
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """Process data - must be implemented by subclasses."""
        pass
    
    def _increment_counter(self) -> None:
        """Internal method to increment counter."""
        self._processed_count += 1
    
    @staticmethod
    def validate_input(data: Any) -> bool:
        """Validate input data."""
        return data is not None

class TextProcessor(BaseProcessor):
    """Processor for text data."""
    
    def __init__(self, name: str, encoding: str = 'utf-8', config: Optional[Config] = None):
        super().__init__(name, config)
        self.encoding = encoding
        self._cache = {}
    
    @retry(max_attempts=3)
    def process(self, data: str) -> str:
        """Process text data."""
        if not self.validate_input(data):
            raise ProcessorError("Invalid input data", 400)
        
        # Check cache first
        if data in self._cache:
            return self._cache[data]
        
        # Process the data
        result = self._transform_text(data)
        
        # Cache the result
        self._cache[data] = result
        self._increment_counter()
        
        return result
    
    def _transform_text(self, text: str) -> str:
        """Transform text according to processor rules."""
        # Simple transformation for demo
        return text.upper().strip()
    
    @lru_cache(maxsize=128)
    def get_word_count(self, text: str) -> int:
        """Get word count with caching."""
        return len(text.split())
    
    def clear_cache(self) -> None:
        """Clear internal cache."""
        self._cache.clear()

class JSONProcessor(BaseProcessor):
    """Processor for JSON data."""
    
    def process(self, data: Union[str, Dict]) -> Dict:
        """Process JSON data."""
        if isinstance(data, str):
            try:
                parsed_data = json.loads(data)
            except json.JSONDecodeError as e:
                raise ProcessorError(f"Invalid JSON: {e}", 400)
        else:
            parsed_data = data
        
        self._increment_counter()
        return self._normalize_json(parsed_data)
    
    def _normalize_json(self, data: Dict) -> Dict:
        """Normalize JSON data structure."""
        # Simple normalization for demo
        normalized = {}
        for key, value in data.items():
            normalized[key.lower()] = value
        return normalized

class ProcessorFactory:
    """Factory for creating processors."""
    
    _processors = {
        'text': TextProcessor,
        'json': JSONProcessor
    }
    
    @classmethod
    def create_processor(cls, processor_type: str, name: str, **kwargs) -> BaseProcessor:
        """Create a processor of the specified type."""
        if processor_type not in cls._processors:
            raise ValueError(f"Unknown processor type: {processor_type}")
        
        processor_class = cls._processors[processor_type]
        return processor_class(name, **kwargs)
    
    @classmethod
    def register_processor(cls, processor_type: str, processor_class: type) -> None:
        """Register a new processor type."""
        cls._processors[processor_type] = processor_class
    
    @classmethod
    def list_processors(cls) -> List[str]:
        """List available processor types."""
        return list(cls._processors.keys())

def process_file(file_path: str, processor_type: str = 'text') -> Optional[Any]:
    """Process a file using the specified processor."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        processor = ProcessorFactory.create_processor(
            processor_type, 
            f"file_processor_{os.path.basename(file_path)}"
        )
        
        return processor.process(content)
    
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None

def main():
    """Main function demonstrating the processors."""
    # Create processors
    text_proc = ProcessorFactory.create_processor('text', 'demo_text')
    json_proc = ProcessorFactory.create_processor('json', 'demo_json')
    
    # Process some data
    text_result = text_proc.process("  Hello, World!  ")
    print(f"Text result: {text_result}")
    
    json_data = '{"Name": "John", "Age": 30}'
    json_result = json_proc.process(json_data)
    print(f"JSON result: {json_result}")
    
    # Show processor stats
    print(f"Text processor processed: {text_proc.processed_count} items")
    print(f"JSON processor processed: {json_proc.processed_count} items")

if __name__ == "__main__":
    main()