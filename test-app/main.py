import streamlit as st

# Configure the page
st.set_page_config(
    page_title="Hello World App",
    page_icon="👋",
    layout="wide"
)

# Main page content
st.title("👋 Welcome to the Hello World App!")

st.markdown("""
This is a multi-page Streamlit application demonstrating basic functionality.

### Features:
- **Home Page**: You're here! 
- **About Page**: Learn more about this app
- **Contact Page**: Get in touch

### Navigation:
Use the sidebar to navigate between pages.
""")

# Sidebar
st.sidebar.success("Select a page above.")

# Some interactive content
st.subheader("Try this interactive element:")
name = st.text_input("What's your name?")
if name:
    st.write(f"Hello, {name}! 🎉")

# Display some metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Pages", "3", "100%")
with col2:
    st.metric("Framework", "Streamlit")
with col3:
    st.metric("Language", "Python")