import streamlit as st

st.set_page_config(page_title="Contact", page_icon="📧")

st.title("📧 Contact Us")

st.markdown("""
Get in touch with us! This page demonstrates form handling in Streamlit.
""")

# Contact form
st.subheader("Send us a message")

with st.form("contact_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Your Name *")
        email = st.text_input("Email Address *")
    
    with col2:
        subject = st.selectbox(
            "Subject *",
            ["General Inquiry", "Bug Report", "Feature Request", "Other"]
        )
        priority = st.select_slider(
            "Priority",
            options=["Low", "Medium", "High"],
            value="Medium"
        )
    
    message = st.text_area("Message *", height=100)
    
    # Form submission
    submitted = st.form_submit_button("Send Message")
    
    if submitted:
        if name and email and message:
            st.success(f"""
            ✅ **Message sent successfully!**
            
            **Details:**
            - Name: {name}
            - Email: {email}
            - Subject: {subject}
            - Priority: {priority}
            - Message: {message[:50]}{'...' if len(message) > 50 else ''}
            
            We'll get back to you soon!
            """)
        else:
            st.error("Please fill in all required fields marked with *")

# Contact information
st.markdown("---")
st.subheader("Other ways to reach us")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **📧 Email**  
    hello@example.com
    """)

with col2:
    st.markdown("""
    **🐦 Twitter**  
    @streamlit
    """)

with col3:
    st.markdown("""
    **💬 Discord**  
    Join our community
    """)

# FAQ section
with st.expander("❓ Frequently Asked Questions"):
    st.markdown("""
    **Q: How do I run this app locally?**  
    A: Use `uv run streamlit run main.py` in your terminal.
    
    **Q: Can I customize the pages?**  
    A: Yes! Edit the Python files in the `pages/` directory.
    
    **Q: How do I add more pages?**  
    A: Create new Python files in the `pages/` directory. Streamlit will automatically detect them.
    
    **Q: Is this app production-ready?**  
    A: This is a demo app. For production, add proper error handling, validation, and security measures.
    """)

st.sidebar.markdown("---")
st.sidebar.info("You're on the Contact page!")