"""AI-powered task generator using Azure OpenAI."""

from __future__ import annotations

import logging
from typing import List, Optional

from dev_agent.config.config_manager import DevAgentConfig
from dev_agent.interfaces.generation_interface import ITaskGenerator
from dev_agent.models.documents import DesignDocument, Task, TaskList
from dev_agent.models.enums import Priority, TaskStatus
from dev_agent.services.azure_openai_service import AzureOpenAIService, ChatMessage
from dev_agent.errors.exceptions import GenerationError

logger = logging.getLogger(__name__)


class AITaskGenerator(ITaskGenerator):
    """AI-powered task generator using Azure OpenAI."""
    
    def __init__(self, config: DevAgentConfig):
        """Initialize AI task generator.
        
        Args:
            config: Dev agent configuration
        """
        self.config = config
        self.ai_service = AzureOpenAIService(config.azure_openai)
        self.version = "1.0"
    
    def generate_from_design(self, design: DesignDocument) -> TaskList:
        """Generate implementation tasks from design document using AI.
        
        Args:
            design: Design document
            
        Returns:
            Generated task list
            
        Raises:
            GenerationError: If task generation fails
        """
        try:
            logger.info("Generating implementation tasks from design using Azure OpenAI")
            
            # Create system prompt for task generation
            system_prompt = self._create_system_prompt_for_tasks()
            
            # Create user prompt with design document
            user_prompt = self._create_task_generation_prompt(design)
            
            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt),
            ]
            
            # Generate tasks using AI
            response = self.ai_service.chat_completion(
                messages=messages,
                temperature=0.2,  # Balanced temperature for structured output
                max_tokens=4000,
            )
            
            # Parse AI response into task list
            task_list = self._parse_ai_response_to_tasks(response.content, design)
            
            logger.info(f"Successfully generated {len(task_list.tasks)} implementation tasks")
            return task_list
            
        except Exception as e:
            logger.error(f"Failed to generate tasks from design: {e}")
            raise GenerationError(f"Task generation failed: {e}") from e
    
    def refine_tasks(self, tasks: TaskList, feedback: str) -> TaskList:
        """Refine task list based on user feedback using AI.
        
        Args:
            tasks: Current task list
            feedback: User feedback for refinement
            
        Returns:
            Refined task list
            
        Raises:
            GenerationError: If task refinement fails
        """
        try:
            logger.info("Refining task list based on user feedback using Azure OpenAI")
            
            # Create system prompt for refinement
            system_prompt = self._create_system_prompt_for_refinement()
            
            # Create user prompt with current tasks and feedback
            user_prompt = self._create_refinement_prompt(tasks, feedback)
            
            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt),
            ]
            
            # Refine tasks using AI
            response = self.ai_service.chat_completion(
                messages=messages,
                temperature=0.1,  # Low temperature for consistent refinement
                max_tokens=4000,
            )
            
            # Parse AI response into refined task list
            refined_tasks = self._parse_ai_response_to_tasks(
                response.content, base_tasks=tasks
            )
            
            logger.info(f"Successfully refined task list to {len(refined_tasks.tasks)} tasks")
            return refined_tasks
            
        except Exception as e:
            logger.error(f"Failed to refine tasks: {e}")
            raise GenerationError(f"Task refinement failed: {e}") from e
    
    def _create_system_prompt_for_tasks(self) -> str:
        """Create system prompt for task generation."""
        return """You are an expert software project manager and technical lead. Your task is to generate a comprehensive list of implementation tasks based on a technical design document.

Key requirements:
1. Break down the design into specific, actionable implementation tasks
2. Create tasks that are appropriately sized (not too large or too small)
3. Consider dependencies between tasks and logical implementation order
4. Include tasks for code implementation, testing, documentation, and deployment
5. Assign appropriate priorities based on dependencies and criticality
6. Provide clear descriptions and acceptance criteria for each task
7. Consider both functional and non-functional requirements

Task categories to include:
- Core implementation tasks
- Database/data model tasks
- API/interface implementation
- Testing tasks (unit, integration, end-to-end)
- Documentation tasks
- Configuration and deployment tasks
- Security implementation tasks
- Performance optimization tasks

For each task, provide:
- Clear, specific title
- Detailed description
- Acceptance criteria
- Estimated effort/complexity
- Priority level
- Dependencies (if any)

Output should be structured and actionable for a development team."""
    
    def _create_system_prompt_for_refinement(self) -> str:
        """Create system prompt for task refinement."""
        return """You are an expert software project manager and technical lead. Your task is to refine an existing task list based on user feedback.

Key requirements:
1. Carefully analyze the provided feedback
2. Update tasks to address all feedback points
3. Maintain logical task structure and dependencies
4. Preserve existing tasks that don't conflict with feedback
5. Ensure all changes are well-integrated
6. Update priorities and dependencies as needed
7. Maintain clear, actionable task descriptions

Focus on:
- Addressing specific feedback about task scope, priority, or dependencies
- Improving task clarity and completeness
- Ensuring proper task breakdown and sizing
- Maintaining project coherence and flow

Provide the complete refined task list."""
    
    def _create_task_generation_prompt(self, design: DesignDocument) -> str:
        """Create user prompt with design document data."""
        prompt_parts = [
            "Please generate a comprehensive list of implementation tasks based on the following technical design:",
            "",
            f"## Design: {design.title}",
            "",
            "### Overview",
            design.overview,
            "",
        ]
        
        if design.system_architecture:
            prompt_parts.extend([
                "### System Architecture",
                design.system_architecture[:1000],  # Limit to avoid token overflow
                "",
            ])
        
        if design.component_design:
            prompt_parts.extend([
                "### Component Design",
                design.component_design[:1000],
                "",
            ])
        
        if design.data_models:
            prompt_parts.extend([
                "### Data Models",
                design.data_models[:800],
                "",
            ])
        
        if design.api_design:
            prompt_parts.extend([
                "### API Design",
                design.api_design[:800],
                "",
            ])
        
        if design.implementation_guidelines:
            prompt_parts.extend([
                "### Implementation Guidelines",
                design.implementation_guidelines[:600],
                "",
            ])
        
        prompt_parts.extend([
            "Generate a complete task list that covers:",
            "1. All components and features described in the design",
            "2. Database/data model implementation",
            "3. API and interface development",
            "4. Testing at all levels",
            "5. Documentation and deployment",
            "6. Security and performance considerations",
            "",
            "Organize tasks logically with proper priorities and dependencies.",
        ])
        
        return "\n".join(prompt_parts)
    
    def _create_refinement_prompt(self, tasks: TaskList, feedback: str) -> str:
        """Create user prompt for task refinement."""
        current_tasks = self._format_tasks_for_prompt(tasks)
        
        prompt_parts = [
            "Please refine the following task list based on the provided feedback:",
            "",
            "**Current Task List:**",
            current_tasks,
            "",
            "**User Feedback:**",
            feedback,
            "",
            "Please provide the complete refined task list that addresses all feedback points.",
        ]
        
        return "\n".join(prompt_parts)
    
    def _format_tasks_for_prompt(self, tasks: TaskList) -> str:
        """Format task list for use in prompts."""
        parts = [
            f"# {tasks.title}",
            "",
            f"**Total Tasks:** {len(tasks.tasks)}",
            "",
        ]
        
        for task in tasks.tasks[:20]:  # Limit to avoid token overflow
            parts.extend([
                f"## {task.id}: {task.title}",
                f"**Priority:** {task.priority.value}",
                f"**Status:** {task.status.value}",
                f"**Description:** {task.description}",
                "",
                "**Acceptance Criteria:**",
                *[f"- {criteria}" for criteria in task.acceptance_criteria],
                "",
                f"**Estimated Hours:** {task.estimated_hours}",
                "",
                "---",
                "",
            ])
        
        if len(tasks.tasks) > 20:
            parts.append(f"... and {len(tasks.tasks) - 20} more tasks")
        
        return "\n".join(parts)
    
    def _parse_ai_response_to_tasks(
        self,
        ai_response: str,
        design: Optional[DesignDocument] = None,
        base_tasks: Optional[TaskList] = None,
    ) -> TaskList:
        """Parse AI response into a task list.
        
        This is a simplified parser. In a production system, you might want
        to use more sophisticated parsing or ask the AI to return structured JSON.
        """
        from datetime import datetime
        
        # Extract title
        lines = ai_response.split('\n')
        title = design.title + " - Implementation Tasks" if design else "Implementation Tasks"
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        
        # Parse tasks from the response
        tasks = []
        current_task = None
        task_counter = 1
        
        for line in lines:
            line = line.strip()
            
            # Look for task headers (## or numbered items)
            if (line.startswith('## ') or 
                (line and line[0].isdigit() and (':' in line or '.' in line))):
                
                # Save previous task if exists
                if current_task:
                    tasks.append(current_task)
                
                # Extract task title
                if line.startswith('## '):
                    task_title = line[3:].strip()
                else:
                    # Handle numbered format like "1. Task Title" or "1: Task Title"
                    parts = line.split(':', 1) if ':' in line else line.split('.', 1)
                    if len(parts) > 1:
                        task_title = parts[1].strip()
                    else:
                        task_title = line
                
                # Create new task
                current_task = {
                    'id': f"TASK-{task_counter:03d}",
                    'title': task_title,
                    'description': '',
                    'acceptance_criteria': [],
                    'priority': Priority.MEDIUM,
                    'estimated_hours': 8,
                    'dependencies': [],
                }
                task_counter += 1
            
            elif current_task:
                # Parse task details
                if line.startswith('**Description:**') or line.startswith('Description:'):
                    current_task['description'] = line.split(':', 1)[1].strip()
                elif line.startswith('**Priority:**') or line.startswith('Priority:'):
                    priority_text = line.split(':', 1)[1].strip().upper()
                    try:
                        current_task['priority'] = Priority(priority_text)
                    except ValueError:
                        current_task['priority'] = Priority.MEDIUM
                elif line.startswith('**Estimated Hours:**') or line.startswith('Estimated:'):
                    try:
                        hours_text = line.split(':', 1)[1].strip()
                        current_task['estimated_hours'] = int(''.join(filter(str.isdigit, hours_text))) or 8
                    except (ValueError, IndexError):
                        current_task['estimated_hours'] = 8
                elif line.startswith('- ') and 'acceptance' in ai_response.lower():
                    # Look for acceptance criteria
                    current_task['acceptance_criteria'].append(line[2:].strip())
                elif line and not line.startswith('**') and not line.startswith('#'):
                    # Add to description if not empty and not a header
                    if current_task['description']:
                        current_task['description'] += ' ' + line
                    else:
                        current_task['description'] = line
        
        # Add the last task
        if current_task:
            tasks.append(current_task)
        
        # Create Task objects
        task_objects = []
        for task_data in tasks:
            task = Task(
                id=task_data['id'],
                title=task_data['title'],
                description=task_data['description'] or f"Implement {task_data['title'].lower()}",
                acceptance_criteria=task_data['acceptance_criteria'] or [
                    f"GIVEN the implementation requirements WHEN {task_data['title'].lower()} is implemented THEN it SHALL meet all specified criteria",
                    "WHEN the task is completed THEN all tests SHALL pass",
                    "WHEN the implementation is reviewed THEN it SHALL meet code quality standards",
                ],
                priority=task_data['priority'],
                status=TaskStatus.NOT_STARTED,
                estimated_hours=task_data['estimated_hours'],
                dependencies=task_data['dependencies'],
                assigned_to="",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            task_objects.append(task)
        
        # If no tasks were parsed, create some default ones
        if not task_objects:
            task_objects = [
                Task(
                    id="TASK-001",
                    title="Set up project structure",
                    description="Initialize project structure and basic configuration",
                    acceptance_criteria=[
                        "GIVEN project requirements WHEN structure is created THEN all necessary directories exist",
                        "WHEN configuration is set up THEN project can be built successfully",
                    ],
                    priority=Priority.HIGH,
                    status=TaskStatus.NOT_STARTED,
                    estimated_hours=4,
                    dependencies=[],
                    assigned_to="",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                ),
                Task(
                    id="TASK-002",
                    title="Implement core functionality",
                    description="Develop the main features as specified in the design",
                    acceptance_criteria=[
                        "GIVEN design specifications WHEN core features are implemented THEN they meet requirements",
                        "WHEN functionality is tested THEN all tests pass",
                    ],
                    priority=Priority.HIGH,
                    status=TaskStatus.NOT_STARTED,
                    estimated_hours=16,
                    dependencies=["TASK-001"],
                    assigned_to="",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                ),
            ]
        
        return TaskList(
            title=title,
            version=base_tasks.version if base_tasks else "1.0",
            created_at=base_tasks.created_at if base_tasks else datetime.now(),
            design_reference=design.title if design else "",
            tasks=task_objects,
            total_estimated_hours=sum(task.estimated_hours for task in task_objects),
        )