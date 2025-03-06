import json
import streamlit as st
import os

def render_debug_panel(data_store, environment, debug_mode):
    """Render debug information panel"""
    if not debug_mode:
        return
    
    with st.expander("Debug Information"):
        st.write(f"**Environment:** {environment}")
        st.write(f"**Data Directory:** {data_store.data_dir}")
        st.write(f"**LLM Model:** {os.getenv('LLM_MODEL', 'llama3-8b-8192')}")
        st.write(f"**API Key Available:** {'Yes' if os.getenv('LLM_API_KEY') else 'No'}")
        st.write(f"**API URL:** {os.getenv('LLM_API_URL')}")
        
        # Show restaurant counts
        restaurants = data_store.get_all_restaurants()
        st.write(f"**Restaurants in database:** {len(restaurants)}")
        
        # Show reservation counts
        reservations = data_store.get_all_reservations()
        st.write(f"**Reservations in database:** {len(reservations)}")

def log_tool_calls(messages, tool_calls):
    """Log tool calls to the debug sidebar"""
    if not os.getenv("DEBUG", "false").lower() == "true":
        return
        
    with st.sidebar.expander("LLM Tool Calls", expanded=True):
        st.write(f"Number of tool calls: {len(tool_calls) if tool_calls else 0}")
        if tool_calls:
            for i, call in enumerate(tool_calls):
                st.write(f"### Tool Call #{i+1}")
                function_name = call["function"]["name"]
                st.write(f"Function: **{function_name}**")
                try:
                    arguments = json.loads(call["function"]["arguments"])
                    st.json(arguments)
                except:
                    st.code(call["function"]["arguments"])