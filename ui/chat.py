import streamlit as st

def render_chat_interface():
    """Render the chat interface with message history"""
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Accept user input if name is provided
    if st.session_state.user_name:
        prompt = st.chat_input("Type your message here...")
        return prompt
    
    return None

def render_user_registration():
    """Render the user registration form"""
    if "user_name" not in st.session_state:
        st.session_state.user_name = ""
    
    if not st.session_state.user_name:
        with st.form("user_info_form"):
            name = st.text_input("What's your name?")
            submit = st.form_submit_button("Start Chatting")
            if submit and name:
                st.session_state.user_name = name
                st.rerun()
        
        return False
    
    return True