# Specification Phase Fixes

## Issues Fixed

### Issue 1: Incomplete Requirements Generation

**Problem:** The AI was generating requirements, but they were not being properly extracted and displayed. The output showed "0 requirements" even though the specification content had requirements.

**Root Cause:** 
1. The prompt template didn't explicitly instruct the AI to use a specific format for requirements
2. The parsing logic in `_extract_requirements_from_ai_content()` was not robust enough to handle various AI output formats
3. The requirement block splitting logic was looking for simple numbered items instead of structured requirement headers

**Fixes Applied:**

1. **Enhanced Prompt Templates** (`dev_agent/llm/prompt_templates.py`):
   - Added explicit formatting instructions with example structure
   - Required the AI to use "#### Requirement N: [Title]" headers
   - Added "**User Story:**" and "**Acceptance Criteria:**" labels
   - Emphasized that 3-5 detailed requirements are REQUIRED
   - Applied to both `SPECIFICATION_TEMPLATE` and `SPECIFICATION_NEW_PROJECT_TEMPLATE`

2. **Improved Requirement Extraction** (`dev_agent/generation/specification_generator.py`):
   - Added `_split_requirement_blocks_improved()` method that looks for "#### Requirement" headers
   - Enhanced `_extract_user_story()` to look for "**User Story:**" labels first
   - Enhanced `_extract_acceptance_criteria()` to look for "**Acceptance Criteria:**" section
   - Added fallback logic for both methods to handle variations in AI output
   - Modified `_extract_requirements_from_ai_content()` to use the improved parsing

3. **Better User Feedback** (`dev_agent/workflow/specification_workflow.py`):
   - Added requirement count display after generation
   - Shows warning if no requirements were generated
   - Helps users identify when specification is incomplete

### Issue 2: Unclear Specification Save Location

**Problem:** After approving the specification, the message said "Specification saved to SPECIFICATION.md" without showing the full path. Users couldn't find the file because it's actually saved in `.dev_agent/documents/SPECIFICATION.md`.

**Root Cause:** The save message only showed the filename, not the full path relative to the project root.

**Fix Applied:**

Modified `_save_specification()` in `dev_agent/workflow/specification_workflow.py`:
- Now calculates the full path to the saved file
- Displays the relative path from current working directory
- Example output: "Specification saved to .dev_agent/documents/SPECIFICATION.md"

## Testing the Fixes

To test these fixes:

1. **Start a new specification phase:**
   ```bash
   uv run dev-agent init /path/to/project
   ```

2. **Provide a feature description:**
   - Example: "Add a random joke page that displays a different joke each time"

3. **Verify the output:**
   - Should see "📋 Generated N requirements" message
   - Should see proper file path in save message
   - Check `.dev_agent/documents/SPECIFICATION.md` for complete requirements

4. **Check the specification content:**
   - Should have Introduction section
   - Should have Key Features section
   - Should have Requirements section with multiple requirements
   - Each requirement should have:
     - User Story in format "As a [role], I want [feature], so that [benefit]"
     - Acceptance Criteria with WHEN/THEN, IF/THEN, or SHALL statements

## Expected Output Format

The AI should now generate specifications like this:

```markdown
# Requirements Document

## Introduction
[Description of the feature]

## Key Features
- Feature 1
- Feature 2
- Feature 3

## Requirements

#### Requirement 1: [Title]

**User Story:** As a user, I want to view a random joke, so that I can be entertained

**Acceptance Criteria:**

1. WHEN the user navigates to the joke page THEN the system SHALL display a random joke
2. WHEN the user refreshes the page THEN the system SHALL display a different random joke
3. IF no jokes are available THEN the system SHALL display an appropriate error message

#### Requirement 2: [Title]

**User Story:** As a user, I want the joke to load quickly, so that I don't have to wait

**Acceptance Criteria:**

1. WHEN the joke page loads THEN the system SHALL fetch and display a joke within 2 seconds
2. IF the joke fetch fails THEN the system SHALL retry up to 3 times
```

## Files Modified

1. `dev_agent/llm/prompt_templates.py` - Enhanced prompt templates with explicit formatting
2. `dev_agent/generation/specification_generator.py` - Improved requirement extraction logic
3. `dev_agent/workflow/specification_workflow.py` - Better user feedback and file path display

## Additional Improvements

- Added requirement count validation
- Added warning messages for incomplete specifications
- Improved robustness of parsing with fallback logic
- Better handling of various AI output formats
