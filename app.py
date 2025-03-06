import os
import json
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from utils.llm import LLMService

# Import our modules
from data import DataStore, generate_sample_data
from core import register_tools, LLMProcessor, ConversationManager
from ui import (
    render_chat_interface, 
    render_debug_panel, 
    log_tool_calls,
    render_sidebar,
    render_user_registration
)

# Load environment variables
load_dotenv()

# Check environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Main Streamlit app
def main():
    st.set_page_config(page_title="FoodieSpot Reservations", page_icon="🍽️")
    st.title("🍽️ FoodieSpot Reservations")
    
    # Initialize data store
    data_dir = "data_storage_dev" if ENVIRONMENT == "development" else "data_storage"
    data_store = DataStore(data_dir=data_dir)
    
    # Initialize LLM service
    llm_service = LLMService(
        api_key=os.getenv("LLM_API_KEY"),
        model=os.getenv("LLM_MODEL", "llama3-8b-8192")
    )
    
    # Register tools with the LLM
    tool_definitions = register_tools()
    llm_service.register_tools(tool_definitions)
    
    # Initialize conversation manager
    conversation_manager = ConversationManager(llm_service, data_store)
    
    # Show environment information in sidebar
    render_sidebar(ENVIRONMENT, st.session_state.get("user_name", None))
    
    # Show debug information if enabled
    render_debug_panel(data_store, ENVIRONMENT, DEBUG)
    
    # Generate sample data if needed
    if "data_initialized" not in st.session_state:
        with st.spinner("Setting up restaurant data..."):
            # Only print message once
            generate_sample_data(data_store, debug=False)
        st.session_state.data_initialized = True
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Welcome to FoodieSpot! I can help you find restaurants and make reservations. What are you looking for today?"}
        ]
    
    # Get user registration
    if not render_user_registration():
        return
    
    # Display chat interface
    prompt = render_chat_interface()
    
    # Process user message if provided
    if prompt:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Use the conversation manager to process the message
                    # This follows proper tool calling architecture where LLM determines intent
                    final_response, tool_results, updated_messages = conversation_manager.process_message(
                        prompt,
                        st.session_state.messages,
                        st.session_state.user_name
                    )
                    
                    # Debug: Log the conversation flow
                    if DEBUG:
                        with st.sidebar.expander("Conversation Flow", expanded=True):
                            # Show the tool calls that were made
                            tool_calls = []
                            for msg in updated_messages:
                                if msg.get("role") == "assistant" and msg.get("tool_calls"):
                                    tool_calls.extend(msg.get("tool_calls"))
                            
                            st.write(f"Number of tool calls: {len(tool_calls)}")
                            
                            for i, call in enumerate(tool_calls):
                                st.write(f"### Tool Call #{i+1}")
                                function_name = call["function"]["name"]
                                st.write(f"Function: **{function_name}**")
                                try:
                                    arguments = json.loads(call["function"]["arguments"])
                                    st.json(arguments)
                                except:
                                    st.code(call["function"]["arguments"])
                    
                    # Display tool results first (if any)
                    if tool_results:
                        for result in tool_results:
                            st.markdown(result)
                    
                    # Display the final response
                    st.markdown(final_response)
                    
                    # Determine the assistant's response to save in history
                    if tool_results:
                        # Combine tool results and final response
                        combined_response = "\n\n".join([*tool_results, final_response])
                        st.session_state.messages.append({"role": "assistant", "content": combined_response})
                    else:
                        # Just save the final response
                        st.session_state.messages.append({"role": "assistant", "content": final_response})
                        
                except Exception as e:
                    # Fall back to error message
                    if DEBUG:
                        import traceback
                        st.error(f"Error: {str(e)}")
                        st.code(traceback.format_exc())
                    
                    # Use error response
                    fallback_response = "I'm having trouble processing your request. Let me try a different approach."
                    st.markdown(fallback_response)
                    st.session_state.messages.append({"role": "assistant", "content": fallback_response})

if __name__ == "__main__":
    main()