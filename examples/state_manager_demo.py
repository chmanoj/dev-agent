#!/usr/bin/env python3
"""
Demonstration of StateManager functionality.

This script shows how to use the StateManager class for project state persistence.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dev_agent.state.state_manager import StateManager
from dev_agent.models.enums import PhaseType, TaskStatus, DocumentType


def main():
    """Demonstrate StateManager functionality."""
    print("🚀 StateManager Demo")
    print("=" * 50)
    
    # Create a demo project directory
    demo_dir = Path("demo_project")
    demo_dir.mkdir(exist_ok=True)
    
    # Initialize StateManager
    state_manager = StateManager(str(demo_dir))
    print(f"📁 Initialized StateManager for: {demo_dir.absolute()}")
    
    # Create initial project state
    session_id = f"demo-session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    initial_state = state_manager.create_initial_state(str(demo_dir), session_id)
    print(f"🆕 Created initial state with session ID: {session_id}")
    
    # Save initial state
    success = state_manager.save_project_state(initial_state)
    print(f"💾 Saved initial state: {'✅' if success else '❌'}")
    
    # Update phase to specification
    success = state_manager.update_phase_status(PhaseType.SPECIFICATION, "Moving to specification phase")
    print(f"📋 Updated phase to SPECIFICATION: {'✅' if success else '❌'}")
    
    # Save a specification document
    spec_content = """# Demo Project Specification

## Introduction
This is a demonstration project for the dev-agent state management system.

## Key Features
- State persistence with JSON serialization
- Document storage for SPECIFICATION.md, DESIGN.md, and TASKS.md
- Task progress tracking
- Session management

## Requirements

### REQ-1: State Management
**User Story:** As a developer, I want to save and restore project state so that I can resume work across sessions.

#### Acceptance Criteria
1. WHEN I save project state THEN it SHALL persist to `.dev_agent/state.json`
2. WHEN I load project state THEN it SHALL restore all data accurately
3. IF state file is corrupted THEN system SHALL handle gracefully

### REQ-2: Document Storage
**User Story:** As a developer, I want to store project documents so that I can maintain project documentation.

#### Acceptance Criteria
1. WHEN I save a document THEN it SHALL be stored in `.dev_agent/documents/`
2. WHEN I load a document THEN it SHALL return the exact content
3. WHEN document doesn't exist THEN system SHALL return None gracefully
"""
    
    success = state_manager.save_document(spec_content, DocumentType.SPECIFICATION)
    print(f"📄 Saved specification document: {'✅' if success else '❌'}")
    
    # Move to design phase
    success = state_manager.update_phase_status(PhaseType.DESIGN, "Specification approved, moving to design")
    print(f"🎨 Updated phase to DESIGN: {'✅' if success else '❌'}")
    
    # Save a design document
    design_content = """# Demo Project Design

## Overview
The state management system provides persistent storage for project state using JSON serialization and file-based document storage.

## Architecture

### Components
- **StateManager**: Core component for state persistence and document storage
- **ProjectState**: Data model representing complete project state
- **DocumentStore**: Handles markdown document storage and retrieval

### Data Flow
1. User creates/modifies project state
2. StateManager serializes state to JSON
3. State persisted to `.dev_agent/state.json`
4. Documents stored separately in `.dev_agent/documents/`

## Error Handling
- Graceful handling of file I/O errors
- JSON parsing error recovery
- Permission error handling with user feedback

## Testing Strategy
- Unit tests for all StateManager methods
- Integration tests for complete workflows
- Error scenario testing with mocked failures
"""
    
    success = state_manager.save_document(design_content, DocumentType.DESIGN)
    print(f"🎨 Saved design document: {'✅' if success else '❌'}")
    
    # Move to implementation phase
    success = state_manager.update_phase_status(PhaseType.IMPLEMENTATION, "Design approved, starting implementation")
    print(f"⚙️ Updated phase to IMPLEMENTATION: {'✅' if success else '❌'}")
    
    # Save tasks document
    tasks_content = """# Demo Project Tasks

- [x] 1. Create StateManager class
  - Implement JSON-based persistence
  - Add document storage methods
  - Handle error scenarios gracefully
  - _Requirements: REQ-1_

- [x] 2. Implement project state models
  - Create ProjectState dataclass
  - Add SessionData and IndexMetadata
  - Support complex document structures
  - _Requirements: REQ-1, REQ-2_

- [ ] 3. Add comprehensive unit tests
  - Test state persistence and recovery
  - Test document storage operations
  - Test error handling scenarios
  - _Requirements: REQ-1, REQ-2_

- [ ] 4. Create integration tests
  - Test complete workflow scenarios
  - Test session resumption
  - Test large state files
  - _Requirements: REQ-1, REQ-2_
"""
    
    success = state_manager.save_document(tasks_content, DocumentType.TASKS)
    print(f"📋 Saved tasks document: {'✅' if success else '❌'}")
    
    # Track some task progress
    success = state_manager.track_task_progress("task-1", TaskStatus.COMPLETED)
    print(f"✅ Marked task-1 as COMPLETED: {'✅' if success else '❌'}")
    
    success = state_manager.track_task_progress("task-2", TaskStatus.COMPLETED)
    print(f"✅ Marked task-2 as COMPLETED: {'✅' if success else '❌'}")
    
    success = state_manager.track_task_progress("task-3", TaskStatus.IN_PROGRESS)
    print(f"🔄 Marked task-3 as IN_PROGRESS: {'✅' if success else '❌'}")
    
    success = state_manager.track_task_progress("task-4", TaskStatus.NOT_STARTED)
    print(f"⏳ Marked task-4 as NOT_STARTED: {'✅' if success else '❌'}")
    
    # Get project info
    project_info = state_manager.get_project_info()
    if project_info:
        print("\n📊 Project Information:")
        print(f"   Current Phase: {project_info['current_phase']}")
        print(f"   Has Specification: {project_info['has_specification']}")
        print(f"   Has Design: {project_info['has_design']}")
        print(f"   Has Tasks: {project_info['has_tasks']}")
        print(f"   Total Tasks: {project_info['total_tasks']}")
        print(f"   Created: {project_info['created_at']}")
        print(f"   Updated: {project_info['updated_at']}")
    
    # Load and verify documents
    print("\n📄 Document Verification:")
    
    loaded_spec = state_manager.load_document(DocumentType.SPECIFICATION)
    print(f"   Specification loaded: {'✅' if loaded_spec else '❌'}")
    if loaded_spec:
        print(f"   Specification length: {len(loaded_spec)} characters")
    
    loaded_design = state_manager.load_document(DocumentType.DESIGN)
    print(f"   Design loaded: {'✅' if loaded_design else '❌'}")
    if loaded_design:
        print(f"   Design length: {len(loaded_design)} characters")
    
    loaded_tasks = state_manager.load_document(DocumentType.TASKS)
    print(f"   Tasks loaded: {'✅' if loaded_tasks else '❌'}")
    if loaded_tasks:
        print(f"   Tasks length: {len(loaded_tasks)} characters")
    
    # Load final state
    final_state = state_manager.load_project_state()
    if final_state:
        print(f"\n🎯 Final State Summary:")
        print(f"   Phase: {final_state.current_phase.value}")
        print(f"   Session ID: {final_state.session_data.session_id}")
        print(f"   Tasks Tracked: {len(final_state.implementation_progress)}")
        
        print(f"\n📈 Task Progress:")
        for task_id, status in final_state.implementation_progress.items():
            status_emoji = {"completed": "✅", "in_progress": "🔄", "not_started": "⏳"}.get(status.value, "❓")
            print(f"   {task_id}: {status_emoji} {status.value}")
    
    print(f"\n📁 Files Created:")
    print(f"   State file: {state_manager.state_file}")
    print(f"   Documents dir: {state_manager.documents_dir}")
    
    # List all created files
    if state_manager.dev_agent_dir.exists():
        for file_path in state_manager.dev_agent_dir.rglob("*"):
            if file_path.is_file():
                size = file_path.stat().st_size
                print(f"   📄 {file_path.relative_to(demo_dir)} ({size} bytes)")
    
    print(f"\n🎉 Demo completed successfully!")
    print(f"💡 You can inspect the created files in: {demo_dir.absolute()}")


if __name__ == "__main__":
    main()