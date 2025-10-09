import streamlit as st

st.set_page_config(page_title="About", page_icon="📖")

st.title("📖 About This App")

st.markdown("""
## What is this?
This is a simple multi-page Streamlit application built to demonstrate:
- Multi-page navigation
- Basic Streamlit components
- Project structure with uv and pyproject.toml

## Technology Stack
- **Frontend**: Streamlit
- **Language**: Python
- **Package Manager**: uv
- **Configuration**: pyproject.toml

## How it works
Streamlit automatically detects Python files in the `pages/` directory and creates 
navigation links in the sidebar. Each file becomes a separate page in the app.

### File Structure:
```
├── main.py              # Home page
├── pages/
│   ├── 1_About.py       # This page
│   └── 2_Contact.py     # Contact page
├── pyproject.toml       # Project configuration
└── README.md           # Documentation
```
""")

# Add some interactive elements
st.subheader("App Statistics")

import datetime
st.info(f"App loaded at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if st.button("Show Random Fact"):
    facts = [
        "Streamlit was created by Adrien Treuille, Amanda Kelly, and Thiago Teixeira",
        "Streamlit apps are just Python scripts that run from top to bottom",
        "You can deploy Streamlit apps for free on Streamlit Community Cloud",
        "Streamlit supports real-time data updates and interactive widgets"
    ]
    import random
    st.success(f"💡 {random.choice(facts)}")

st.sidebar.markdown("---")
st.sidebar.info("You're on the About page!")