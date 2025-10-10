#!/bin/bash
# Interactive test for creating login page

export GEMINI_API_KEY=AIzaSyB7b0svJ7VFJKiCVq5A1xylYjngGR0E-I0
export GEMINI_MODEL_NAME=gemini-2.5-flash
export GEMINI_EMBEDDING_MODEL=gemini-embedding-001
export PREFERRED_LLM_PROVIDER=gemini

echo "🧪 Creating Login Page in test-app"
echo "===================================="
echo ""
echo "This test will:"
echo "1. Generate specification for login page"
echo "2. Generate design document"
echo "3. Generate implementation tasks"
echo ""

# Use the CLI commands directly
echo "Step 1: Generating specification..."
uv run dev-agent resume test-app <<EOF
spec
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
4. Follow the same style and structure as existing pages
5. Add appropriate emojis and styling consistent with the app
approve
exit
EOF

echo ""
echo "Step 2: Generating design..."
uv run dev-agent resume test-app <<EOF
design
approve
exit
EOF

echo ""
echo "Step 3: Generating tasks..."
uv run dev-agent resume test-app <<EOF
tasks
approve
exit
EOF

echo ""
echo "✅ Workflow complete!"
echo ""
echo "📋 Generated files:"
ls -lh test-app/.dev_agent/documents/ 2>/dev/null || echo "No documents directory"
echo ""
echo "📄 Specification preview:"
head -20 test-app/.dev_agent/documents/specification.md 2>/dev/null || echo "Not generated"
echo ""
echo "🎉 Done!"
