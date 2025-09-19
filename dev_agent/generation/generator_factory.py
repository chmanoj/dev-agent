"""Factory for creating generation components with Azure OpenAI support."""

from __future__ import annotations

import logging
from typing import Optional

from dev_agent.config.config_manager import DevAgentConfig
from dev_agent.interfaces.cli_interface import ICLIInterface
from dev_agent.interfaces.generation_interface import (
    IDesignGenerator,
    ISpecificationGenerator,
    ITaskGenerator,
)

# Traditional generators
from dev_agent.generation.specification_generator import SpecificationGenerator
from dev_agent.generation.design_generator import DesignGenerator
from dev_agent.generation.task_generator import TaskGenerator

# AI-powered generators
from dev_agent.generation.ai_specification_generator import AISpecificationGenerator
from dev_agent.generation.ai_design_generator import AIDesignGenerator
from dev_agent.generation.ai_task_generator import AITaskGenerator

logger = logging.getLogger(__name__)


class GeneratorFactory:
    """Factory for creating generation components."""
    
    def __init__(self, config: DevAgentConfig, cli_interface: Optional[ICLIInterface] = None):
        """Initialize generator factory.
        
        Args:
            config: Dev agent configuration
            cli_interface: Optional CLI interface for user interaction
        """
        self.config = config
        self.cli_interface = cli_interface
        self._use_ai = self._should_use_ai_generators()
    
    def _should_use_ai_generators(self) -> bool:
        """Determine if AI generators should be used.
        
        Returns:
            True if AI generators should be used
        """
        # Check if Azure OpenAI is configured
        if not self.config.azure_openai.api_key or not self.config.azure_openai.endpoint:
            logger.info("Azure OpenAI not configured, using traditional generators")
            return False
        
        # Test connection (optional - could be skipped for performance)
        try:
            from dev_agent.services.azure_openai_service import AzureOpenAIService
            service = AzureOpenAIService(self.config.azure_openai)
            # Quick connection test with minimal token usage
            if service.test_connection():
                logger.info("Azure OpenAI available, using AI-powered generators")
                return True
            else:
                logger.warning("Azure OpenAI connection failed, falling back to traditional generators")
                return False
        except Exception as e:
            logger.warning(f"Failed to test Azure OpenAI connection: {e}")
            logger.info("Falling back to traditional generators")
            return False
    
    def create_specification_generator(self) -> ISpecificationGenerator:
        """Create a specification generator.
        
        Returns:
            Specification generator instance
        """
        if self._use_ai:
            logger.info("Creating AI-powered specification generator")
            return AISpecificationGenerator(self.config, self.cli_interface)
        else:
            logger.info("Creating traditional specification generator")
            return SpecificationGenerator(self.cli_interface)
    
    def create_design_generator(self) -> IDesignGenerator:
        """Create a design generator.
        
        Returns:
            Design generator instance
        """
        if self._use_ai:
            logger.info("Creating AI-powered design generator")
            return AIDesignGenerator(self.config)
        else:
            logger.info("Creating traditional design generator")
            return DesignGenerator()
    
    def create_task_generator(self) -> ITaskGenerator:
        """Create a task generator.
        
        Returns:
            Task generator instance
        """
        if self._use_ai:
            logger.info("Creating AI-powered task generator")
            return AITaskGenerator(self.config)
        else:
            logger.info("Creating traditional task generator")
            return TaskGenerator()
    
    def is_using_ai(self) -> bool:
        """Check if AI generators are being used.
        
        Returns:
            True if AI generators are being used
        """
        return self._use_ai
    
    def get_generator_info(self) -> dict[str, str]:
        """Get information about the generators being used.
        
        Returns:
            Dictionary with generator information
        """
        if self._use_ai:
            return {
                "type": "AI-powered",
                "service": "Azure OpenAI",
                "chat_model": self.config.azure_openai.chat_model,
                "embedding_model": self.config.azure_openai.embedding_model,
                "api_version": self.config.azure_openai.api_version,
            }
        else:
            return {
                "type": "Traditional",
                "service": "Rule-based",
                "description": "Template-based generation without AI",
            }


def create_generators(
    config: DevAgentConfig, cli_interface: Optional[ICLIInterface] = None
) -> tuple[ISpecificationGenerator, IDesignGenerator, ITaskGenerator]:
    """Create all generators using the factory.
    
    Args:
        config: Dev agent configuration
        cli_interface: Optional CLI interface
        
    Returns:
        Tuple of (specification_generator, design_generator, task_generator)
    """
    factory = GeneratorFactory(config, cli_interface)
    
    spec_generator = factory.create_specification_generator()
    design_generator = factory.create_design_generator()
    task_generator = factory.create_task_generator()
    
    logger.info(f"Created generators: {factory.get_generator_info()}")
    
    return spec_generator, design_generator, task_generator