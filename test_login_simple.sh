#!/bin/bash
# Simple test: Create login page in test-app using actual CLI

export GEMINI_API_KEY=AIzaSyB7b0svJ7VFJKiCVq5A1xylYjngGR0E-I0
export GEMINI_MODEL_NAME=gemini-2.5-flash
export GEMINI_EMBEDDING_MODEL=gemini-embedding-001
export PREFERRED_LLM_PROVIDER=gemini

echo "🧪 Testing: Create Login Page in test-app"
echo "=========================================="
echo ""
echo "This will run the actual CLI and simulate user input"
echo ""

# Create input file with all user responses
cat > /tmp/login_test_input.txt << 'EOF'
Create a login page for the Streamlit app with the following requirements:

1. Create a new page called 'Login' (3_Login.py in the pages directory)
2. The page should have:
   - A title "Login" with a lock emoji 🔒
   - An email input field (st.text_input with label "Email")
   - A password input field (st.text_input with type='password' and label "Password")
   - A "Login" button (st.button)
   - Basic validation to check if both fields are filled
   - Success message when login button is clicked with valid inputs
   - Error message if fields are empty
3. Use Streamlit's session state to track login status
4. Follow the same style and structure as existing pages (1_About.py and 2_Contact.py)
5. Add appropriate emojis and styling consistent with the app

The page should be simple, clean, and follow Streamlit best practices.
skip
y
next
y
next
y
exit
EOF

echo "📝 Input prepared. Running CLI..."
echo ""

# Run the CLI with input
uv run dev-agent resume test-app < /tmp/login_test_input.txt

echo ""
echo "✅ Test complete!"
echo ""
echo "📋 Checking generated files..."
echo ""

# Check what was generated
if [ -f "test-app/.dev_agent/documents/specification.md" ]; then
    echo "✅ Specification generated ($(wc -l < test-app/.dev_agent/documents/specification.md) lines)"
else
    echo "❌ Specification not found"
fi

if [ -f "test-app/.dev_agent/documents/design.md" ]; then
    echo "✅ Design generated ($(wc -l < test-app/.dev_agent/documents/design.md) lines)"
else
    echo "❌ Design not found"
fi

if [ -f "test-app/.dev_agent/documents/tasks.md" ]; then
    echo "✅ Tasks generated ($(wc -l < test-app/.dev_agent/documents/tasks.md) lines)"
else
    echo "❌ Tasks not found"
fi

if [ -f "test-app/pages/3_Login.py" ]; then
    echo "✅ Login page created ($(wc -l < test-app/pages/3_Login.py) lines)"
else
    echo "⚠️  Login page not created yet (implementation phase may need completion)"
fi

echo ""
echo "📊 Current state:"
cat test-app/.dev_agent/state.json | python3 -m json.tool | grep -E '"current_phase"|"indexing_complete"|"specification"|"design"|"tasks"' | head -10

echo ""
echo "🎉 Done! Check test-app/.dev_agent/documents/ for generated files"
