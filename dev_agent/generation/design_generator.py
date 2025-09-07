"""Design generator for creating DESIGN.md documents."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..interfaces.generation_interface import IDesignGenerator
from ..interfaces.cli_interface import ICLIInterface
from ..interfaces.analysis_interface import ICodebaseAnalyzer
from ..models.documents import (
    DesignDocument, SpecificationDocument, ComponentSpec, DataModel,
    InterfaceSpec, ErrorHandlingStrategy, TestingStrategy, ArchitectureDescription
)
from ..models.analysis import DesignAnalysis, ComponentAnalysis


class DesignGenerator(IDesignGenerator):
    """Generates design documents from specifications and codebase analysis."""
    
    def __init__(self, codebase_analyzer: ICodebaseAnalyzer, cli_interface: Optional[ICLIInterface] = None):
        """Initialize the design generator.
        
        Args:
            codebase_analyzer: Codebase analyzer for architecture analysis
            cli_interface: Optional CLI interface for user interaction
        """
        self.codebase_analyzer = codebase_analyzer
        self.cli_interface = cli_interface
        self.version = "1.0"
    
    def generate_from_specification(self, spec: SpecificationDocument, analysis: DesignAnalysis) -> DesignDocument:
        """Generate design document from specification and codebase analysis.
        
        Args:
            spec: Specification document
            analysis: Design analysis from codebase
            
        Returns:
            Generated design document
        """
        # Generate overview from specification and analysis
        overview = self._generate_overview(spec, analysis)
        
        # Create architecture description
        architecture = self._create_architecture_description(spec, analysis)
        
        # Generate components from analysis and requirements
        components = self._generate_components(spec, analysis)
        
        # Extract data models from analysis
        data_models = self._generate_data_models(spec, analysis)
        
        # Generate interfaces from analysis
        interfaces = self._generate_interfaces(spec, analysis)
        
        # Create error handling strategy
        error_handling = self._create_error_handling_strategy(spec, analysis)
        
        # Create testing strategy
        testing_strategy = self._create_testing_strategy(spec, analysis)
        
        return DesignDocument(
            overview=overview,
            architecture=architecture,
            components=components,
            data_models=data_models,
            interfaces=interfaces,
            error_handling=error_handling,
            testing_strategy=testing_strategy,
            version=self.version,
            approved=False
        )
    
    def refine_design(self, design: DesignDocument, feedback: str) -> DesignDocument:
        """Refine design based on user feedback.
        
        Args:
            design: Original design document
            feedback: User feedback for refinement
            
        Returns:
            Refined design document
        """
        # Parse feedback to understand what needs to be changed
        refinements = self._parse_feedback(feedback)
        
        # Apply refinements to the design
        refined_design = self._apply_refinements(design, refinements)
        
        # Update version and reset approval status
        refined_design.version = self._increment_version(design.version)
        refined_design.approved = False
        
        return refined_design
    
    def format_design_document(self, design: DesignDocument) -> str:
        """Format design document as markdown.
        
        Args:
            design: Design document to format
            
        Returns:
            Formatted markdown string
        """
        lines = []
        
        # Header
        lines.append("# Design Document")
        lines.append("")
        
        # Overview
        lines.append("## Overview")
        lines.append("")
        lines.append(design.overview)
        lines.append("")
        
        # Architecture
        lines.append("## Architecture")
        lines.append("")
        lines.append(design.architecture.overview)
        lines.append("")
        
        if design.architecture.patterns:
            lines.append("### Architectural Patterns")
            lines.append("")
            for pattern in design.architecture.patterns:
                lines.append(f"- {pattern}")
            lines.append("")
        
        if design.architecture.components:
            lines.append("### High-Level Components")
            lines.append("")
            for component in design.architecture.components:
                lines.append(f"- {component}")
            lines.append("")
        
        # Components and Interfaces
        if design.components:
            lines.append("## Components and Interfaces")
            lines.append("")
            
            for component in design.components:
                lines.append(f"### {component.name}")
                lines.append("")
                lines.append(component.description)
                lines.append("")
                
                if component.interfaces:
                    lines.append("**Interfaces:**")
                    for interface in component.interfaces:
                        lines.append(f"- {interface}")
                    lines.append("")
                
                if component.dependencies:
                    lines.append("**Dependencies:**")
                    for dependency in component.dependencies:
                        lines.append(f"- {dependency}")
                    lines.append("")
        
        # Data Models
        if design.data_models:
            lines.append("## Data Models")
            lines.append("")
            
            for model in design.data_models:
                lines.append(f"### {model.name}")
                lines.append("")
                
                if model.fields:
                    lines.append("**Fields:**")
                    for field_name, field_type in model.fields.items():
                        lines.append(f"- `{field_name}`: {field_type}")
                    lines.append("")
                
                if model.relationships:
                    lines.append("**Relationships:**")
                    for relationship in model.relationships:
                        lines.append(f"- {relationship}")
                    lines.append("")
        
        # Interfaces
        if design.interfaces:
            lines.append("## Interface Specifications")
            lines.append("")
            
            for interface in design.interfaces:
                lines.append(f"### {interface.name}")
                lines.append("")
                lines.append(interface.description)
                lines.append("")
                
                if interface.methods:
                    lines.append("**Methods:**")
                    for method in interface.methods:
                        lines.append(f"- {method}")
                    lines.append("")
        
        # Error Handling
        lines.append("## Error Handling")
        lines.append("")
        lines.append(f"**Logging Strategy:** {design.error_handling.logging_strategy}")
        lines.append("")
        
        if design.error_handling.error_categories:
            lines.append("**Error Categories:**")
            for category in design.error_handling.error_categories:
                lines.append(f"- {category}")
            lines.append("")
        
        if design.error_handling.recovery_mechanisms:
            lines.append("**Recovery Mechanisms:**")
            for mechanism in design.error_handling.recovery_mechanisms:
                lines.append(f"- {mechanism}")
            lines.append("")
        
        # Testing Strategy
        lines.append("## Testing Strategy")
        lines.append("")
        lines.append(f"**Unit Testing:** {design.testing_strategy.unit_testing}")
        lines.append("")
        lines.append(f"**Integration Testing:** {design.testing_strategy.integration_testing}")
        lines.append("")
        lines.append(f"**Performance Testing:** {design.testing_strategy.performance_testing}")
        lines.append("")
        lines.append(f"**Test Coverage Target:** {design.testing_strategy.test_coverage_target:.0%}")
        lines.append("")
        
        # Metadata
        lines.append("---")
        lines.append("")
        lines.append("## Document Metadata")
        lines.append("")
        lines.append(f"- **Version:** {design.version}")
        lines.append(f"- **Status:** {'Approved' if design.approved else 'Draft'}")
        
        return "\n".join(lines)
    
    def request_user_approval(self, design: DesignDocument) -> bool:
        """Request user approval for the design.
        
        Args:
            design: Design document to approve
            
        Returns:
            True if approved, False otherwise
        """
        if not self.cli_interface:
            # Auto-approve if no CLI interface
            design.approved = True
            return True
        
        formatted_design = self.format_design_document(design)
        approved = self.cli_interface.request_approval(formatted_design, "design")
        
        if approved:
            design.approved = True
        
        return approved
    
    # Private helper methods
    
    def _generate_overview(self, spec: SpecificationDocument, analysis: DesignAnalysis) -> str:
        """Generate design overview from specification and analysis."""
        overview_parts = []
        
        # Start with specification introduction context
        overview_parts.append(f"This design document outlines the technical architecture for the system described in the specification.")
        
        # Add architecture insights from analysis
        if analysis.architecture_overview:
            overview_parts.append(analysis.architecture_overview)
        
        # Add component count information
        if analysis.components:
            overview_parts.append(f"The system is organized into {len(analysis.components)} main components.")
        
        # Add design patterns information
        if analysis.design_patterns:
            patterns_text = ", ".join(analysis.design_patterns[:3])
            overview_parts.append(f"The design incorporates {patterns_text} patterns.")
        
        # Add quality metrics if available
        if analysis.quality_metrics:
            if 'documentation_coverage' in analysis.quality_metrics:
                coverage = analysis.quality_metrics['documentation_coverage']
                if coverage > 0.7:
                    overview_parts.append("The codebase demonstrates good documentation practices.")
                elif coverage < 0.3:
                    overview_parts.append("The design emphasizes improved documentation standards.")
        
        return " ".join(overview_parts)
    
    def _create_architecture_description(self, spec: SpecificationDocument, analysis: DesignAnalysis) -> ArchitectureDescription:
        """Create architecture description from analysis."""
        # Generate architecture overview
        if analysis.architecture_overview:
            overview = analysis.architecture_overview
        else:
            overview = "The system follows a modular architecture with clear separation of concerns."
        
        # Extract patterns from analysis
        patterns = analysis.design_patterns.copy() if analysis.design_patterns else []
        
        # Add patterns inferred from components
        if analysis.components:
            component_names = [comp.name.lower() for comp in analysis.components]
            if any('service' in name for name in component_names):
                patterns.append("Service Layer Pattern")
            if any('repository' in name or 'dao' in name for name in component_names):
                patterns.append("Repository Pattern")
            if any('controller' in name for name in component_names):
                patterns.append("MVC Pattern")
        
        # Generate component list
        components = []
        if analysis.components:
            components = [comp.name for comp in analysis.components]
        else:
            # Infer components from specification requirements
            for req in spec.functional_requirements:
                if 'data' in req.user_story.lower():
                    components.append("Data Management Component")
                if 'user' in req.user_story.lower():
                    components.append("User Interface Component")
                if 'api' in req.user_story.lower():
                    components.append("API Component")
        
        # Remove duplicates and limit
        components = list(dict.fromkeys(components))[:8]
        
        return ArchitectureDescription(
            overview=overview,
            patterns=patterns,
            components=components
        )
    
    def _generate_components(self, spec: SpecificationDocument, analysis: DesignAnalysis) -> List[ComponentSpec]:
        """Generate component specifications."""
        components = []
        
        # Use existing components from analysis if available
        if analysis.components:
            for comp_analysis in analysis.components:
                component = ComponentSpec(
                    name=comp_analysis.name,
                    description=comp_analysis.purpose,
                    interfaces=comp_analysis.interfaces,
                    dependencies=comp_analysis.dependencies
                )
                components.append(component)
        else:
            # Generate components based on specification requirements
            component_map = {}
            
            for req in spec.functional_requirements:
                req_text = req.user_story.lower()
                
                # Identify component types from requirements
                if any(keyword in req_text for keyword in ['data', 'store', 'save', 'retrieve']):
                    if 'Data Management' not in component_map:
                        component_map['Data Management'] = {
                            'description': 'Handles data storage, retrieval, and management operations',
                            'interfaces': ['IDataRepository', 'IDataValidator'],
                            'dependencies': ['Database', 'Validation Framework']
                        }
                
                if any(keyword in req_text for keyword in ['user', 'interface', 'display', 'view']):
                    if 'User Interface' not in component_map:
                        component_map['User Interface'] = {
                            'description': 'Provides user interaction and presentation layer',
                            'interfaces': ['IUserInterface', 'IViewController'],
                            'dependencies': ['UI Framework', 'Event System']
                        }
                
                if any(keyword in req_text for keyword in ['api', 'service', 'endpoint', 'request']):
                    if 'API Service' not in component_map:
                        component_map['API Service'] = {
                            'description': 'Handles external API requests and responses',
                            'interfaces': ['IAPIHandler', 'IRequestProcessor'],
                            'dependencies': ['HTTP Framework', 'Authentication Service']
                        }
                
                if any(keyword in req_text for keyword in ['auth', 'login', 'security', 'permission']):
                    if 'Authentication' not in component_map:
                        component_map['Authentication'] = {
                            'description': 'Manages user authentication and authorization',
                            'interfaces': ['IAuthenticator', 'IAuthorizer'],
                            'dependencies': ['Security Framework', 'User Management']
                        }
            
            # Convert to ComponentSpec objects
            for name, details in component_map.items():
                component = ComponentSpec(
                    name=name,
                    description=details['description'],
                    interfaces=details['interfaces'],
                    dependencies=details['dependencies']
                )
                components.append(component)
        
        return components
    
    def _generate_data_models(self, spec: SpecificationDocument, analysis: DesignAnalysis) -> List[DataModel]:
        """Generate data models from analysis."""
        models = []
        
        # Use existing data models from analysis if available
        if analysis.data_models:
            for model_data in analysis.data_models:
                model = DataModel(
                    name=model_data.get('name', 'UnknownModel'),
                    fields=self._convert_attributes_to_fields(model_data.get('attributes', [])),
                    relationships=model_data.get('relationships', [])
                )
                models.append(model)
        else:
            # Generate models based on specification requirements
            model_candidates = set()
            
            for req in spec.functional_requirements:
                req_text = req.user_story.lower()
                
                # Extract potential model names from requirements
                if 'user' in req_text:
                    model_candidates.add('User')
                if any(keyword in req_text for keyword in ['data', 'record', 'item', 'entity']):
                    model_candidates.add('DataRecord')
                if 'session' in req_text:
                    model_candidates.add('Session')
                if 'config' in req_text:
                    model_candidates.add('Configuration')
            
            # Create basic models
            for model_name in list(model_candidates)[:5]:
                fields = self._generate_basic_fields_for_model(model_name)
                relationships = self._generate_basic_relationships_for_model(model_name, model_candidates)
                
                model = DataModel(
                    name=model_name,
                    fields=fields,
                    relationships=relationships
                )
                models.append(model)
        
        return models
    
    def _generate_interfaces(self, spec: SpecificationDocument, analysis: DesignAnalysis) -> List[InterfaceSpec]:
        """Generate interface specifications."""
        interfaces = []
        
        # Use existing interfaces from analysis if available
        if analysis.api_interfaces:
            for api_data in analysis.api_interfaces:
                interface = InterfaceSpec(
                    name=api_data.get('name', 'UnknownInterface'),
                    methods=self._extract_methods_from_api_data(api_data),
                    description=api_data.get('docstring', 'API interface')
                )
                interfaces.append(interface)
        else:
            # Generate interfaces based on specification requirements
            interface_map = {}
            
            for req in spec.functional_requirements:
                req_text = req.user_story.lower()
                
                if any(keyword in req_text for keyword in ['data', 'store', 'retrieve']):
                    if 'IDataService' not in interface_map:
                        interface_map['IDataService'] = {
                            'description': 'Interface for data management operations',
                            'methods': ['create(data)', 'read(id)', 'update(id, data)', 'delete(id)', 'list()']
                        }
                
                if any(keyword in req_text for keyword in ['user', 'auth', 'login']):
                    if 'IUserService' not in interface_map:
                        interface_map['IUserService'] = {
                            'description': 'Interface for user management operations',
                            'methods': ['authenticate(credentials)', 'authorize(user, action)', 'get_user(id)', 'update_user(id, data)']
                        }
                
                if any(keyword in req_text for keyword in ['api', 'service', 'request']):
                    if 'IAPIHandler' not in interface_map:
                        interface_map['IAPIHandler'] = {
                            'description': 'Interface for API request handling',
                            'methods': ['handle_request(request)', 'validate_input(data)', 'format_response(data)']
                        }
            
            # Convert to InterfaceSpec objects
            for name, details in interface_map.items():
                interface = InterfaceSpec(
                    name=name,
                    methods=details['methods'],
                    description=details['description']
                )
                interfaces.append(interface)
        
        return interfaces
    
    def _create_error_handling_strategy(self, spec: SpecificationDocument, analysis: DesignAnalysis) -> ErrorHandlingStrategy:
        """Create error handling strategy."""
        # Determine error categories based on requirements
        error_categories = []
        
        for req in spec.functional_requirements:
            req_text = req.user_story.lower()
            
            if any(keyword in req_text for keyword in ['data', 'store', 'save']):
                error_categories.append("Data Validation Errors")
                error_categories.append("Storage Errors")
            
            if any(keyword in req_text for keyword in ['user', 'auth', 'login']):
                error_categories.append("Authentication Errors")
                error_categories.append("Authorization Errors")
            
            if any(keyword in req_text for keyword in ['api', 'request', 'service']):
                error_categories.append("Network Errors")
                error_categories.append("API Errors")
        
        # Remove duplicates
        error_categories = list(dict.fromkeys(error_categories))
        
        # Add common error categories
        if not error_categories:
            error_categories = ["Input Validation Errors", "System Errors", "Business Logic Errors"]
        
        # Define recovery mechanisms
        recovery_mechanisms = [
            "Graceful degradation for non-critical failures",
            "Retry mechanisms for transient errors",
            "User-friendly error messages",
            "Logging and monitoring for debugging"
        ]
        
        # Determine logging strategy
        if analysis.technical_debt and any('log' in debt.lower() for debt in analysis.technical_debt):
            logging_strategy = "Structured logging with appropriate levels (DEBUG, INFO, WARN, ERROR)"
        else:
            logging_strategy = "Comprehensive logging with structured format and appropriate levels"
        
        return ErrorHandlingStrategy(
            error_categories=error_categories,
            recovery_mechanisms=recovery_mechanisms,
            logging_strategy=logging_strategy
        )
    
    def _create_testing_strategy(self, spec: SpecificationDocument, analysis: DesignAnalysis) -> TestingStrategy:
        """Create testing strategy."""
        # Determine testing approach based on analysis
        if analysis.quality_metrics and 'documentation_coverage' in analysis.quality_metrics:
            coverage = analysis.quality_metrics['documentation_coverage']
            if coverage > 0.7:
                unit_testing = "Comprehensive unit testing with high coverage (>90%)"
                target_coverage = 0.9
            elif coverage > 0.4:
                unit_testing = "Good unit testing coverage with focus on critical paths"
                target_coverage = 0.8
            else:
                unit_testing = "Basic unit testing with emphasis on core functionality"
                target_coverage = 0.7
        else:
            unit_testing = "Comprehensive unit testing using pytest framework"
            target_coverage = 0.85
        
        # Integration testing strategy
        integration_testing = "Integration tests for component interactions and external dependencies"
        
        # Performance testing strategy
        performance_testing = "Performance testing for critical paths and scalability requirements"
        
        return TestingStrategy(
            unit_testing=unit_testing,
            integration_testing=integration_testing,
            performance_testing=performance_testing,
            test_coverage_target=target_coverage
        )
    
    def _convert_attributes_to_fields(self, attributes: List[str]) -> Dict[str, str]:
        """Convert attribute list to field dictionary."""
        fields = {}
        
        for attr in attributes:
            # Simple type inference based on attribute name
            attr_lower = attr.lower()
            if any(keyword in attr_lower for keyword in ['id', 'key']):
                fields[attr] = "int"
            elif any(keyword in attr_lower for keyword in ['name', 'title', 'description']):
                fields[attr] = "str"
            elif any(keyword in attr_lower for keyword in ['date', 'time', 'created', 'updated']):
                fields[attr] = "datetime"
            elif any(keyword in attr_lower for keyword in ['count', 'number', 'size']):
                fields[attr] = "int"
            elif any(keyword in attr_lower for keyword in ['active', 'enabled', 'valid']):
                fields[attr] = "bool"
            else:
                fields[attr] = "str"
        
        return fields
    
    def _generate_basic_fields_for_model(self, model_name: str) -> Dict[str, str]:
        """Generate basic fields for a model based on its name."""
        fields = {"id": "int"}
        
        model_lower = model_name.lower()
        
        if model_lower == 'user':
            fields.update({
                "username": "str",
                "email": "str",
                "created_at": "datetime",
                "is_active": "bool"
            })
        elif model_lower == 'datarecord':
            fields.update({
                "name": "str",
                "data": "dict",
                "created_at": "datetime",
                "updated_at": "datetime"
            })
        elif model_lower == 'session':
            fields.update({
                "user_id": "int",
                "token": "str",
                "expires_at": "datetime",
                "is_active": "bool"
            })
        elif model_lower == 'configuration':
            fields.update({
                "key": "str",
                "value": "str",
                "description": "str",
                "updated_at": "datetime"
            })
        else:
            fields.update({
                "name": "str",
                "description": "str",
                "created_at": "datetime"
            })
        
        return fields
    
    def _generate_basic_relationships_for_model(self, model_name: str, all_models: set) -> List[str]:
        """Generate basic relationships for a model."""
        relationships = []
        
        model_lower = model_name.lower()
        
        if model_lower == 'user' and 'Session' in all_models:
            relationships.append("One-to-many relationship with Session")
        
        if model_lower == 'session' and 'User' in all_models:
            relationships.append("Many-to-one relationship with User")
        
        if model_lower == 'datarecord' and 'User' in all_models:
            relationships.append("Many-to-one relationship with User (owner)")
        
        return relationships
    
    def _extract_methods_from_api_data(self, api_data: Dict[str, Any]) -> List[str]:
        """Extract methods from API data."""
        methods = []
        
        if 'parameters' in api_data:
            params = ", ".join(api_data['parameters'])
            method_name = api_data.get('name', 'unknown_method')
            return_type = api_data.get('return_type', 'Any')
            methods.append(f"{method_name}({params}) -> {return_type}")
        else:
            methods.append(f"{api_data.get('name', 'unknown_method')}()")
        
        return methods
    
    def _parse_feedback(self, feedback: str) -> Dict[str, Any]:
        """Parse user feedback to understand requested changes."""
        feedback_lower = feedback.lower()
        refinements = {
            'modify_overview': None,
            'add_components': [],
            'modify_components': [],
            'add_interfaces': [],
            'modify_error_handling': None,
            'modify_testing': None
        }
        
        # Simple keyword-based parsing
        if 'overview' in feedback_lower:
            refinements['modify_overview'] = feedback
        
        if 'component' in feedback_lower:
            if 'add' in feedback_lower or 'more' in feedback_lower:
                refinements['add_components'] = ['Additional component based on feedback']
            else:
                refinements['modify_components'] = [feedback]
        
        if 'interface' in feedback_lower and 'add' in feedback_lower:
            refinements['add_interfaces'] = ['Additional interface based on feedback']
        
        if 'error' in feedback_lower or 'exception' in feedback_lower:
            refinements['modify_error_handling'] = feedback
        
        if 'test' in feedback_lower:
            refinements['modify_testing'] = feedback
        
        # If no specific category matched, treat as general overview feedback
        if not any(refinements.values()):
            refinements['modify_overview'] = feedback
        
        return refinements
    
    def _apply_refinements(self, design: DesignDocument, refinements: Dict[str, Any]) -> DesignDocument:
        """Apply refinements to design document."""
        # Create a copy of the design
        refined_design = DesignDocument(
            overview=design.overview,
            architecture=design.architecture,
            components=design.components.copy(),
            data_models=design.data_models.copy(),
            interfaces=design.interfaces.copy(),
            error_handling=design.error_handling,
            testing_strategy=design.testing_strategy,
            version=design.version,
            approved=False
        )
        
        # Apply overview changes
        if refinements['modify_overview']:
            refined_design.overview = f"{design.overview} {refinements['modify_overview']}"
        
        # Add new components
        for new_comp_text in refinements['add_components']:
            new_component = ComponentSpec(
                name="Additional Component",
                description=new_comp_text,
                interfaces=[],
                dependencies=[]
            )
            refined_design.components.append(new_component)
        
        # Add new interfaces
        for new_interface_text in refinements['add_interfaces']:
            new_interface = InterfaceSpec(
                name="IAdditionalInterface",
                methods=["additional_method()"],
                description=new_interface_text
            )
            refined_design.interfaces.append(new_interface)
        
        # Modify error handling
        if refinements['modify_error_handling']:
            refined_design.error_handling.logging_strategy = f"{design.error_handling.logging_strategy} {refinements['modify_error_handling']}"
        
        # Modify testing strategy
        if refinements['modify_testing']:
            refined_design.testing_strategy.unit_testing = f"{design.testing_strategy.unit_testing} {refinements['modify_testing']}"
        
        return refined_design
    
    def _increment_version(self, version: str) -> str:
        """Increment version number."""
        try:
            parts = version.split('.')
            if len(parts) >= 2:
                minor = int(parts[1]) + 1
                return f"{parts[0]}.{minor}"
            else:
                major = int(parts[0])
                return f"{major}.1"
        except (ValueError, IndexError):
            return "1.1"