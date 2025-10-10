"""Unit tests for specification generator validation and parsing.

This test module covers:
- Validation of complete specifications (3+ requirements)
- Validation of incomplete specifications (< 3 requirements)
- Parsing AI output with complete requirements
- Parsing AI output with missing requirements
- Parsing handling format variations gracefully
"""

from __future__ import annotations

import pytest

from dev_agent.generation.specification_generator import SpecificationGenerator
from dev_agent.models.documents import Requirement, SpecificationDocument
from dev_agent.models.enums import Priority, SpecificationSource


class TestSpecificationValidation:
    """Test specification validation logic."""

    def test_validate_complete_specification_passes(self):
        """Test that validation passes for a complete specification with 3+ requirements."""
        # Create a complete specification with 3 requirements
        requirements = [
            Requirement(
                id="FR-1",
                user_story="As a developer, I want to validate specifications, so that I can ensure quality",
                acceptance_criteria=[
                    "WHEN validation is run THEN it SHALL check all requirements",
                    "IF a requirement is incomplete THEN the system SHALL report an error",
                ],
                priority=Priority.HIGH,
            ),
            Requirement(
                id="FR-2",
                user_story="As a user, I want to parse AI output, so that I can extract structured data",
                acceptance_criteria=[
                    "WHEN AI content is parsed THEN it SHALL extract user stories",
                    "WHEN AI content is parsed THEN it SHALL extract acceptance criteria",
                    "IF parsing fails THEN the system SHALL log detailed error information",
                ],
                priority=Priority.MEDIUM,
            ),
            Requirement(
                id="FR-3",
                user_story="As a developer, I want to handle format variations, so that parsing is robust",
                acceptance_criteria=[
                    "WHEN different formats are encountered THEN the parser SHALL handle them gracefully",
                    "IF a format is not recognized THEN the system SHALL fall back to alternative patterns",
                ],
                priority=Priority.MEDIUM,
            ),
        ]

        spec = SpecificationDocument(
            introduction="This is a comprehensive specification document for testing validation.",
            key_features=["Feature 1", "Feature 2", "Feature 3"],
            functional_requirements=requirements,
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
        )

        generator = SpecificationGenerator()
        is_valid, issues = generator._validate_specification(spec)

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_incomplete_specification_fails(self):
        """Test that validation fails for a specification with < 3 requirements."""
        # Create an incomplete specification with only 2 requirements
        requirements = [
            Requirement(
                id="FR-1",
                user_story="As a developer, I want to test validation",
                acceptance_criteria=[
                    "WHEN validation runs THEN it SHALL work",
                ],
                priority=Priority.HIGH,
            ),
            Requirement(
                id="FR-2",
                user_story="As a user, I want to use the system",
                acceptance_criteria=[
                    "WHEN using the system THEN it SHALL respond",
                ],
                priority=Priority.MEDIUM,
            ),
        ]

        spec = SpecificationDocument(
            introduction="This is an incomplete specification.",
            key_features=["Feature 1"],
            functional_requirements=requirements,
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
        )

        generator = SpecificationGenerator()
        is_valid, issues = generator._validate_specification(spec)

        assert is_valid is False
        assert len(issues) > 0
        assert any("only 2 requirement(s)" in issue for issue in issues)

    def test_validate_specification_missing_user_story(self):
        """Test that validation fails when a requirement is missing a user story."""
        requirements = [
            Requirement(
                id="FR-1",
                user_story="",  # Missing user story
                acceptance_criteria=[
                    "WHEN validation runs THEN it SHALL work",
                    "IF errors occur THEN they SHALL be reported",
                ],
                priority=Priority.HIGH,
            ),
            Requirement(
                id="FR-2",
                user_story="As a user, I want to use the system",
                acceptance_criteria=[
                    "WHEN using the system THEN it SHALL respond",
                    "IF the system fails THEN it SHALL recover",
                ],
                priority=Priority.MEDIUM,
            ),
            Requirement(
                id="FR-3",
                user_story="As a developer, I want to test the system",
                acceptance_criteria=[
                    "WHEN testing THEN it SHALL pass",
                    "IF tests fail THEN they SHALL be reported",
                ],
                priority=Priority.LOW,
            ),
        ]

        spec = SpecificationDocument(
            introduction="Specification with missing user story.",
            key_features=["Feature 1", "Feature 2"],
            functional_requirements=requirements,
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
        )

        generator = SpecificationGenerator()
        is_valid, issues = generator._validate_specification(spec)

        assert is_valid is False
        assert any("missing user story" in issue for issue in issues)

    def test_validate_specification_insufficient_acceptance_criteria(self):
        """Test that validation fails when a requirement has < 2 acceptance criteria."""
        requirements = [
            Requirement(
                id="FR-1",
                user_story="As a developer, I want to validate specifications",
                acceptance_criteria=[
                    "WHEN validation runs THEN it SHALL work",
                ],  # Only 1 criterion
                priority=Priority.HIGH,
            ),
            Requirement(
                id="FR-2",
                user_story="As a user, I want to use the system",
                acceptance_criteria=[
                    "WHEN using the system THEN it SHALL respond",
                    "IF the system fails THEN it SHALL recover",
                ],
                priority=Priority.MEDIUM,
            ),
            Requirement(
                id="FR-3",
                user_story="As a developer, I want to test the system",
                acceptance_criteria=[
                    "WHEN testing THEN it SHALL pass",
                    "IF tests fail THEN they SHALL be reported",
                ],
                priority=Priority.LOW,
            ),
        ]

        spec = SpecificationDocument(
            introduction="Specification with insufficient acceptance criteria.",
            key_features=["Feature 1", "Feature 2"],
            functional_requirements=requirements,
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
        )

        generator = SpecificationGenerator()
        is_valid, issues = generator._validate_specification(spec)

        assert is_valid is False
        assert any("only 1 acceptance criterion" in issue for issue in issues)

    def test_validate_specification_invalid_user_story_format(self):
        """Test that validation fails when user story doesn't follow 'As a...' format."""
        requirements = [
            Requirement(
                id="FR-1",
                user_story="I want to validate specifications",  # Missing "As a"
                acceptance_criteria=[
                    "WHEN validation runs THEN it SHALL work",
                    "IF errors occur THEN they SHALL be reported",
                ],
                priority=Priority.HIGH,
            ),
            Requirement(
                id="FR-2",
                user_story="As a user, I want to use the system",
                acceptance_criteria=[
                    "WHEN using the system THEN it SHALL respond",
                    "IF the system fails THEN it SHALL recover",
                ],
                priority=Priority.MEDIUM,
            ),
            Requirement(
                id="FR-3",
                user_story="As a developer, I want to test the system",
                acceptance_criteria=[
                    "WHEN testing THEN it SHALL pass",
                    "IF tests fail THEN they SHALL be reported",
                ],
                priority=Priority.LOW,
            ),
        ]

        spec = SpecificationDocument(
            introduction="Specification with invalid user story format.",
            key_features=["Feature 1", "Feature 2"],
            functional_requirements=requirements,
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
        )

        generator = SpecificationGenerator()
        is_valid, issues = generator._validate_specification(spec)

        assert is_valid is False
        assert any("doesn't follow 'As a...'" in issue for issue in issues)

    def test_validate_specification_short_introduction(self):
        """Test that validation fails when introduction is too short."""
        requirements = [
            Requirement(
                id="FR-1",
                user_story="As a developer, I want to validate specifications",
                acceptance_criteria=[
                    "WHEN validation runs THEN it SHALL work",
                    "IF errors occur THEN they SHALL be reported",
                ],
                priority=Priority.HIGH,
            ),
            Requirement(
                id="FR-2",
                user_story="As a user, I want to use the system",
                acceptance_criteria=[
                    "WHEN using the system THEN it SHALL respond",
                    "IF the system fails THEN it SHALL recover",
                ],
                priority=Priority.MEDIUM,
            ),
            Requirement(
                id="FR-3",
                user_story="As a developer, I want to test the system",
                acceptance_criteria=[
                    "WHEN testing THEN it SHALL pass",
                    "IF tests fail THEN they SHALL be reported",
                ],
                priority=Priority.LOW,
            ),
        ]

        spec = SpecificationDocument(
            introduction="Short intro",  # Too short (< 50 characters)
            key_features=["Feature 1", "Feature 2"],
            functional_requirements=requirements,
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
        )

        generator = SpecificationGenerator()
        is_valid, issues = generator._validate_specification(spec)

        assert is_valid is False
        assert any("Introduction is missing or too short" in issue for issue in issues)

    def test_validate_specification_insufficient_key_features(self):
        """Test that validation fails when there are < 2 key features."""
        requirements = [
            Requirement(
                id="FR-1",
                user_story="As a developer, I want to validate specifications",
                acceptance_criteria=[
                    "WHEN validation runs THEN it SHALL work",
                    "IF errors occur THEN they SHALL be reported",
                ],
                priority=Priority.HIGH,
            ),
            Requirement(
                id="FR-2",
                user_story="As a user, I want to use the system",
                acceptance_criteria=[
                    "WHEN using the system THEN it SHALL respond",
                    "IF the system fails THEN it SHALL recover",
                ],
                priority=Priority.MEDIUM,
            ),
            Requirement(
                id="FR-3",
                user_story="As a developer, I want to test the system",
                acceptance_criteria=[
                    "WHEN testing THEN it SHALL pass",
                    "IF tests fail THEN they SHALL be reported",
                ],
                priority=Priority.LOW,
            ),
        ]

        spec = SpecificationDocument(
            introduction="This is a comprehensive specification document for testing validation.",
            key_features=["Feature 1"],  # Only 1 feature
            functional_requirements=requirements,
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
        )

        generator = SpecificationGenerator()
        is_valid, issues = generator._validate_specification(spec)

        assert is_valid is False
        assert any("Only 1 key feature(s)" in issue for issue in issues)


class TestAIOutputParsing:
    """Test parsing of AI-generated specification content."""

    def test_parse_complete_ai_output(self):
        """Test parsing AI output with complete requirements."""
        ai_content = """
# Requirements Document

## Overview

This specification defines the requirements for a user authentication system
that provides secure login and registration functionality.

## Key Features

- User registration with email verification
- Secure password hashing and storage
- Session management with JWT tokens
- Password reset functionality
- Multi-factor authentication support

## Requirements

### Requirement 1

**User Story:** As a user, I want to register for an account, so that I can access the system

#### Acceptance Criteria

1. WHEN a user provides valid registration details THEN the system SHALL create a new account
2. WHEN a user provides an existing email THEN the system SHALL reject the registration
3. IF registration is successful THEN the system SHALL send a verification email

### Requirement 2

**User Story:** As a user, I want to log in securely, so that I can access my account

#### Acceptance Criteria

1. WHEN a user provides valid credentials THEN the system SHALL authenticate the user
2. WHEN a user provides invalid credentials THEN the system SHALL reject the login attempt
3. IF authentication is successful THEN the system SHALL create a session token

### Requirement 3

**User Story:** As a user, I want to reset my password, so that I can recover my account

#### Acceptance Criteria

1. WHEN a user requests a password reset THEN the system SHALL send a reset link
2. WHEN a user clicks the reset link THEN the system SHALL allow password change
3. IF the reset link is expired THEN the system SHALL reject the request
"""

        generator = SpecificationGenerator()
        spec = generator._parse_ai_specification(ai_content, None)

        assert spec is not None
        assert len(spec.functional_requirements) >= 3
        assert spec.introduction != ""
        assert len(spec.key_features) >= 2

        # Validate the parsed specification
        is_valid, issues = generator._validate_specification(spec)
        assert is_valid is True
        assert len(issues) == 0

    def test_parse_ai_output_with_missing_requirements(self):
        """Test parsing AI output with missing or incomplete requirements."""
        ai_content = """
# Requirements Document

## Overview

This is a brief specification with incomplete requirements.

## Key Features

- Feature 1

## Requirements

### Requirement 1

**User Story:** As a user, I want to use the system

#### Acceptance Criteria

1. WHEN using the system THEN it SHALL work
"""

        generator = SpecificationGenerator()
        spec = generator._parse_ai_specification(ai_content, None)

        assert spec is not None
        # Should have at least 1 requirement even if incomplete
        assert len(spec.functional_requirements) >= 1

        # Validation should fail due to insufficient requirements
        is_valid, issues = generator._validate_specification(spec)
        assert is_valid is False
        assert len(issues) > 0

    def test_parse_ai_output_format_variation_numbered(self):
        """Test parsing handles numbered requirement format variation."""
        ai_content = """
# Requirements Document

## Introduction

This specification uses numbered requirements format.

## Functional Requirements

1. **User Story:** As a developer, I want to parse different formats, so that the system is robust

   **Acceptance Criteria:**
   - WHEN different formats are encountered THEN the parser SHALL handle them
   - IF a format is not recognized THEN the system SHALL use fallback patterns

2. **User Story:** As a user, I want reliable parsing, so that I can trust the output

   **Acceptance Criteria:**
   - WHEN parsing occurs THEN it SHALL extract all requirements
   - IF parsing fails THEN the system SHALL log detailed errors

3. **User Story:** As a developer, I want comprehensive validation, so that quality is ensured

   **Acceptance Criteria:**
   - WHEN validation runs THEN it SHALL check all criteria
   - IF validation fails THEN the system SHALL report specific issues
"""

        generator = SpecificationGenerator()
        spec = generator._parse_ai_specification(ai_content, None)

        assert spec is not None
        assert len(spec.functional_requirements) >= 3

        # Check that user stories were extracted
        for req in spec.functional_requirements:
            assert req.user_story != ""
            assert "as a" in req.user_story.lower()
            assert len(req.acceptance_criteria) >= 2

    def test_parse_ai_output_format_variation_bullets(self):
        """Test parsing handles bullet point format variation."""
        ai_content = """
# Specification

## Overview

This specification uses bullet point format for requirements.

## Requirements

- **User Story:** As a developer, I want to handle bullet formats, so that parsing is flexible
  
  **Acceptance Criteria:**
  * WHEN bullet points are used THEN the parser SHALL extract them
  * IF bullets are nested THEN the system SHALL handle them correctly

- **User Story:** As a user, I want consistent parsing, so that I get reliable results
  
  **Acceptance Criteria:**
  * WHEN parsing different formats THEN the system SHALL produce consistent output
  * IF format variations exist THEN the parser SHALL adapt

- **User Story:** As a developer, I want robust error handling, so that failures are graceful
  
  **Acceptance Criteria:**
  * WHEN errors occur THEN the system SHALL log them
  * IF parsing fails THEN the system SHALL provide fallback behavior
"""

        generator = SpecificationGenerator()
        spec = generator._parse_ai_specification(ai_content, None)

        assert spec is not None
        assert len(spec.functional_requirements) >= 3

        # Validate that requirements were properly extracted
        for req in spec.functional_requirements:
            assert req.user_story != ""
            assert len(req.acceptance_criteria) >= 2

    def test_parse_ai_output_format_variation_mixed(self):
        """Test parsing handles mixed format variations gracefully."""
        ai_content = """
# Requirements

## Introduction

This specification mixes different formatting styles to test parser robustness.

## Key Features

* Feature A
* Feature B
- Feature C

## Requirements

#### Requirement 1: User Authentication

As a user, I want to authenticate securely, so that my data is protected

Acceptance Criteria:
- WHEN I provide valid credentials THEN the system SHALL authenticate me
- IF credentials are invalid THEN the system SHALL reject the attempt
- WHEN authentication succeeds THEN the system SHALL create a session

### Requirement 2

User Story: As a developer, I want flexible parsing, so that different formats work

Criteria:
1. WHEN parsing mixed formats THEN the system SHALL extract all requirements
2. IF a format is unusual THEN the parser SHALL adapt
3. WHEN extraction completes THEN all data SHALL be structured correctly

#### Requirement 3

**Story:** As a user, I want reliable functionality, so that I can trust the system

**Criteria:**
* WHEN using the system THEN it SHALL perform as expected
* IF errors occur THEN they SHALL be handled gracefully
* WHEN operations complete THEN results SHALL be accurate
"""

        generator = SpecificationGenerator()
        spec = generator._parse_ai_specification(ai_content, None)

        assert spec is not None
        # Should extract at least 3 requirements despite format variations
        assert len(spec.functional_requirements) >= 3

        # Check that key features were extracted
        assert len(spec.key_features) >= 3

        # Validate that requirements have proper structure
        for req in spec.functional_requirements:
            assert req.user_story != ""
            assert len(req.acceptance_criteria) >= 2


class TestAcceptanceCriteriaValidation:
    """Test validation of acceptance criteria using EARS format."""

    def test_valid_when_then_shall_criterion(self):
        """Test that WHEN...THEN...SHALL criteria are recognized as valid."""
        generator = SpecificationGenerator()
        
        criterion = "WHEN a user submits a form THEN the system SHALL validate the input"
        assert generator._is_valid_acceptance_criterion(criterion) is True

    def test_valid_if_then_shall_criterion(self):
        """Test that IF...THEN...SHALL criteria are recognized as valid."""
        generator = SpecificationGenerator()
        
        criterion = "IF the input is invalid THEN the system SHALL display an error message"
        assert generator._is_valid_acceptance_criterion(criterion) is True

    def test_valid_where_shall_criterion(self):
        """Test that WHERE...SHALL criteria are recognized as valid."""
        generator = SpecificationGenerator()
        
        criterion = "WHERE data is stored the system SHALL encrypt it"
        assert generator._is_valid_acceptance_criterion(criterion) is True

    def test_invalid_criterion_too_short(self):
        """Test that criteria that are too short are rejected."""
        generator = SpecificationGenerator()
        
        criterion = "SHALL work"
        assert generator._is_valid_acceptance_criterion(criterion) is False

    def test_invalid_criterion_no_ears_keywords(self):
        """Test that criteria without EARS keywords are rejected."""
        generator = SpecificationGenerator()
        
        criterion = "The system must validate user input properly"
        assert generator._is_valid_acceptance_criterion(criterion) is False

    def test_invalid_criterion_empty(self):
        """Test that empty criteria are rejected."""
        generator = SpecificationGenerator()
        
        criterion = ""
        assert generator._is_valid_acceptance_criterion(criterion) is False


class TestUserStoryExtraction:
    """Test extraction of user stories from requirement blocks."""

    def test_extract_user_story_with_label(self):
        """Test extracting user story with 'User Story:' label."""
        generator = SpecificationGenerator()
        
        block = """
**User Story:** As a developer, I want to extract user stories, so that I can structure requirements

**Acceptance Criteria:**
1. WHEN extracting THEN it SHALL work
"""
        
        user_story = generator._extract_user_story_enhanced(block)
        assert user_story != ""
        assert "as a developer" in user_story.lower()

    def test_extract_user_story_without_label(self):
        """Test extracting user story without explicit label."""
        generator = SpecificationGenerator()
        
        block = """
As a user, I want to use the system, so that I can accomplish my goals

Acceptance Criteria:
- WHEN using the system THEN it SHALL respond
"""
        
        user_story = generator._extract_user_story_enhanced(block)
        assert user_story != ""
        assert "as a user" in user_story.lower()

    def test_extract_user_story_with_formatting(self):
        """Test extracting user story with various markdown formatting."""
        generator = SpecificationGenerator()
        
        block = """
### Requirement 1

**Story:** As a developer, I want robust parsing, so that I can handle variations

**Criteria:**
- WHEN parsing THEN it SHALL work
"""
        
        user_story = generator._extract_user_story_enhanced(block)
        assert user_story != ""
        assert "as a developer" in user_story.lower()


class TestAcceptanceCriteriaExtraction:
    """Test extraction of acceptance criteria from requirement blocks."""

    def test_extract_criteria_with_section_label(self):
        """Test extracting criteria with 'Acceptance Criteria:' label."""
        generator = SpecificationGenerator()
        
        block = """
**User Story:** As a user, I want to test extraction

**Acceptance Criteria:**
1. WHEN extraction runs THEN it SHALL find all criteria
2. IF criteria are formatted differently THEN the parser SHALL adapt
3. WHEN parsing completes THEN all criteria SHALL be extracted
"""
        
        criteria = generator._extract_acceptance_criteria_enhanced(block)
        assert len(criteria) >= 3
        for criterion in criteria:
            assert generator._is_valid_acceptance_criterion(criterion)

    def test_extract_criteria_without_section_label(self):
        """Test extracting criteria without explicit section label."""
        generator = SpecificationGenerator()
        
        block = """
As a user, I want to test extraction

WHEN the system processes input THEN it SHALL validate the data
IF validation fails THEN the system SHALL report errors
WHEN processing completes THEN the system SHALL return results
"""
        
        criteria = generator._extract_acceptance_criteria_enhanced(block)
        assert len(criteria) >= 3

    def test_extract_criteria_with_bullets(self):
        """Test extracting criteria formatted as bullet points."""
        generator = SpecificationGenerator()
        
        block = """
**Acceptance Criteria:**
- WHEN a user logs in THEN the system SHALL authenticate them
- IF credentials are invalid THEN the system SHALL reject the attempt
- WHEN authentication succeeds THEN the system SHALL create a session
"""
        
        criteria = generator._extract_acceptance_criteria_enhanced(block)
        assert len(criteria) >= 3

    def test_extract_criteria_mixed_formats(self):
        """Test extracting criteria with mixed formatting."""
        generator = SpecificationGenerator()
        
        block = """
Criteria:
1. WHEN processing data THEN the system SHALL validate it
* IF data is invalid THEN the system SHALL reject it
- WHEN validation passes THEN the system SHALL proceed
"""
        
        criteria = generator._extract_acceptance_criteria_enhanced(block)
        assert len(criteria) >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
