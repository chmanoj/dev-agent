#!/usr/bin/env python3
"""
Demonstration of the specification generation system.

This script shows how to use the SpecificationGenerator and SpecificationWorkflow
to generate specification documents from both existing code analysis and user input.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dev_agent.generation.specification_generator import SpecificationGenerator
from dev_agent.workflow.specification_workflow import SpecificationWorkflow
from dev_agent.models.analysis import SpecificationAnalysis, RequirementEvidence
from dev_agent.models.enums import SpecificationSource
from dev_agent.interfaces.cli_interface import ICLIInterface


class DemoCLI(ICLIInterface):
    """Simple CLI implementation for demonstration purposes."""
    
    def __init__(self):
        self.messages = []
        self.inputs = []
        self.input_index = 0
    
    def start_chat_session(self) -> None:
        print("Demo CLI session started")
    
    def handle_user_input(self, input_text: str) -> str:
        return f"Processed: {input_text}"
    
    def request_approval(self, document: str, document_type: str) -> bool:
        print(f"\n=== {document_type.upper()} DOCUMENT ===")
        print(document)
        print(f"=== END {document_type.upper()} ===\n")
        
        # Auto-approve for demo
        print("✓ Document automatically approved for demo")
        return True
    
    def display_progress(self, phase, progress: float) -> None:
        print(f"Progress: {phase.value} - {progress:.0%}")
    
    def init_command(self, project_path: str) -> None:
        print(f"Initializing project at: {project_path}")
    
    def display_message(self, message: str) -> None:
        print(f"📝 {message}")
        self.messages.append(message)
    
    def get_user_input(self, prompt: str) -> str:
        # Pre-defined inputs for demo
        demo_inputs = [
            "Users should be able to create accounts with email and password",
            "System should authenticate users securely with JWT tokens",
            "Users can update their profile information including name and avatar",
            "Admins can manage user accounts and view system statistics",
            "System should log all user activities for security auditing",
            ""  # Empty to stop
        ]
        
        if self.input_index < len(demo_inputs):
            response = demo_inputs[self.input_index]
            self.input_index += 1
            print(f"{prompt}{response}")
            return response
        
        return ""


def demo_existing_code_analysis():
    """Demonstrate specification generation from existing code analysis."""
    print("\n" + "="*60)
    print("DEMO 1: SPECIFICATION FROM EXISTING CODE ANALYSIS")
    print("="*60)
    
    # Create sample analysis data (simulating what CodebaseAnalyzer would return)
    evidence1 = RequirementEvidence(
        requirement_type="User Authentication",
        description="System provides secure user authentication with JWT tokens",
        supporting_files=["auth/models.py", "auth/views.py", "auth/serializers.py"],
        supporting_functions=["login_user", "logout_user", "refresh_token", "validate_token"],
        confidence=0.9,
        code_examples=[]
    )
    
    evidence2 = RequirementEvidence(
        requirement_type="User Profile Management",
        description="System allows users to manage their profile information",
        supporting_files=["users/models.py", "users/views.py", "users/serializers.py"],
        supporting_functions=["update_profile", "get_profile", "upload_avatar"],
        confidence=0.85,
        code_examples=[]
    )
    
    evidence3 = RequirementEvidence(
        requirement_type="Admin Dashboard",
        description="System provides administrative interface for user management",
        supporting_files=["admin/views.py", "admin/models.py", "admin/permissions.py"],
        supporting_functions=["list_users", "deactivate_user", "view_statistics"],
        confidence=0.8,
        code_examples=[]
    )
    
    analysis = SpecificationAnalysis(
        project_purpose="Django REST API for user management with authentication",
        main_features=[
            "User Registration and Authentication",
            "JWT Token Management", 
            "Profile Management",
            "Admin Dashboard",
            "Activity Logging"
        ],
        user_roles=["User", "Admin", "Super Admin"],
        functional_areas=[
            "Authentication",
            "User Management", 
            "Profile Management",
            "Administration",
            "Security"
        ],
        requirement_evidence=[evidence1, evidence2, evidence3],
        technology_constraints=[
            "Python 3.8+",
            "Django REST Framework",
            "JWT Authentication",
            "PostgreSQL Database"
        ],
        external_dependencies=[
            "django",
            "djangorestframework", 
            "djangorestframework-simplejwt",
            "psycopg2-binary"
        ],
        confidence_score=0.85
    )
    
    # Generate specification
    cli = DemoCLI()
    generator = SpecificationGenerator(cli_interface=cli)
    
    print("🔍 Analyzing existing codebase...")
    spec = generator.generate_from_existing_code(analysis)
    
    print(f"✅ Generated specification with {len(spec.functional_requirements)} requirements")
    print(f"📊 Source: {spec.source.value}")
    print(f"🎯 Key Features: {', '.join(spec.key_features[:3])}...")
    
    # Request approval
    approved = generator.request_user_approval(spec)
    print(f"✓ Specification approved: {approved}")
    
    return spec


def demo_user_input_specification():
    """Demonstrate specification generation from user input."""
    print("\n" + "="*60)
    print("DEMO 2: SPECIFICATION FROM USER INPUT")
    print("="*60)
    
    cli = DemoCLI()
    generator = SpecificationGenerator(cli_interface=cli)
    
    print("👤 Collecting user requirements...")
    spec = generator.generate_from_user_input([])
    
    print(f"✅ Generated specification with {len(spec.functional_requirements)} requirements")
    print(f"📊 Source: {spec.source.value}")
    print(f"🎯 Key Features: {', '.join(spec.key_features)}")
    
    # Request approval
    approved = generator.request_user_approval(spec)
    print(f"✓ Specification approved: {approved}")
    
    return spec


def demo_specification_refinement():
    """Demonstrate specification refinement based on feedback."""
    print("\n" + "="*60)
    print("DEMO 3: SPECIFICATION REFINEMENT")
    print("="*60)
    
    cli = DemoCLI()
    generator = SpecificationGenerator(cli_interface=cli)
    
    # Start with a basic specification
    user_requirements = [
        "Create a simple blog application",
        "Users can write and publish posts"
    ]
    
    print("📝 Creating initial specification...")
    original_spec = generator.generate_from_user_input(user_requirements)
    print(f"Original version: {original_spec.version}")
    print(f"Original requirements: {len(original_spec.functional_requirements)}")
    
    # Refine the specification
    feedback = "Add user authentication, comment system, and admin moderation features"
    print(f"\n💬 User feedback: {feedback}")
    
    refined_spec = generator.refine_specification(original_spec, feedback)
    print(f"✅ Refined specification")
    print(f"New version: {refined_spec.version}")
    print(f"New requirements: {len(refined_spec.functional_requirements)}")
    
    # Show the refined specification
    approved = generator.request_user_approval(refined_spec)
    print(f"✓ Refined specification approved: {approved}")
    
    return refined_spec


def demo_workflow_integration():
    """Demonstrate the complete workflow integration."""
    print("\n" + "="*60)
    print("DEMO 4: COMPLETE WORKFLOW INTEGRATION")
    print("="*60)
    
    cli = DemoCLI()
    workflow = SpecificationWorkflow(cli_interface=cli)
    
    print("🚀 Starting specification workflow...")
    
    # Simulate new project (no existing code)
    project_path = "/demo/project"
    
    # Mock the existing code check to return False
    original_method = workflow._has_existing_code
    workflow._has_existing_code = lambda path: False
    
    try:
        spec = workflow.execute_specification_phase(project_path)
        
        print(f"🎉 Workflow completed successfully!")
        print(f"📄 Final specification:")
        print(f"   - Version: {spec.version}")
        print(f"   - Source: {spec.source.value}")
        print(f"   - Requirements: {len(spec.functional_requirements)}")
        print(f"   - Approved: {spec.approved}")
        print(f"   - Features: {len(spec.key_features)}")
        
        return spec
        
    finally:
        # Restore original method
        workflow._has_existing_code = original_method


def main():
    """Run all specification generation demos."""
    print("🎯 SPECIFICATION GENERATION SYSTEM DEMO")
    print("This demo shows the complete specification generation capabilities")
    
    try:
        # Demo 1: Existing code analysis
        spec1 = demo_existing_code_analysis()
        
        # Demo 2: User input
        spec2 = demo_user_input_specification()
        
        # Demo 3: Refinement
        spec3 = demo_specification_refinement()
        
        # Demo 4: Workflow integration
        spec4 = demo_workflow_integration()
        
        print("\n" + "="*60)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"Generated {4} specification documents:")
        print(f"1. Existing Code Analysis: {len(spec1.functional_requirements)} requirements")
        print(f"2. User Input: {len(spec2.functional_requirements)} requirements")
        print(f"3. Refined Specification: {len(spec3.functional_requirements)} requirements")
        print(f"4. Workflow Integration: {len(spec4.functional_requirements)} requirements")
        
        print("\n🎯 Key Features Demonstrated:")
        print("✓ Specification generation from codebase analysis")
        print("✓ Specification generation from user input")
        print("✓ User approval workflow with CLI integration")
        print("✓ Specification refinement based on feedback")
        print("✓ Complete workflow orchestration")
        print("✓ Proper EARS format for acceptance criteria")
        print("✓ Markdown document formatting")
        print("✓ Version management and approval tracking")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)