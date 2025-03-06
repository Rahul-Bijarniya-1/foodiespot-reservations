import streamlit as st

def render_sidebar(environment, user_name=None):
    """Render the sidebar with user info and controls"""
    st.sidebar.title("Restaurant Assistant")
    st.sidebar.write(f"**Environment:** {environment}")
    
    if user_name:
        st.sidebar.write(f"Welcome, **{user_name}**!")
        
        # Add button to clear chat history
        if st.sidebar.button("Clear Chat History"):
            st.session_state.messages = [
                {"role": "assistant", "content": f"Hi {user_name}! I've cleared our previous conversation. How can I help you today?"}
            ]
            st.rerun()