import os
import json
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

# Import our modules
from data import DataStore, generate_sample_data
from models import Restaurant, Reservation
from utils import (
    LLMService, 
    format_restaurant_list,
    format_restaurant_details,
    format_available_times,
    format_reservation_confirmation
)
import tools

# Load environment variables
load_dotenv()

# Check environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Initialize LLM service with Groq API
llm = LLMService(api_key=os.getenv("LLM_API_KEY"), model="llama3-8b-8192")

# Initialize data store
data_dir = "data_storage_dev" if ENVIRONMENT == "development" else "data_storage"
data_store = DataStore(data_dir=data_dir)

# Show debug information if enabled
def show_debug_info():
    if not DEBUG:
        return
    
    with st.expander("Debug Information"):
        st.write(f"**Environment:** {ENVIRONMENT}")
        st.write(f"**Data Directory:** {data_dir}")
        st.write(f"**LLM Model:** {llm.model}")
        st.write(f"**API Key Available:** {'Yes' if os.getenv('LLM_API_KEY') else 'No'}")
        st.write(f"**API URL:** {llm.api_url}")
        
        # Show restaurant counts
        restaurants = data_store.get_all_restaurants()
        st.write(f"**Restaurants in database:** {len(restaurants)}")
        
        # Show reservation counts
        reservations = data_store.get_all_reservations()
        st.write(f"**Reservations in database:** {len(reservations)}")

# Define tools for the LLM
def register_tools():
    tool_definitions = [
        {
            "type": "function",
            "function": {
                "name": "search_restaurants",
                "description": "Search for restaurants based on criteria",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cuisine": {
                            "type": "string",
                            "description": "Type of cuisine (e.g., Italian, Japanese)"
                        },
                        "location": {
                            "type": "string", 
                            "description": "Restaurant location"
                        },
                        "price_range": {
                            "type": "integer",
                            "description": "Maximum price range (1-4)"
                        },
                        "party_size": {
                            "type": "integer",
                            "description": "Size of the dining party"
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_restaurant_details",
                "description": "Get detailed information about a restaurant",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {
                            "type": "string",
                            "description": "ID of the restaurant"
                        }
                    },
                    "required": ["restaurant_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_availability",
                "description": "Check available time slots for a restaurant on a specific date",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {
                            "type": "string",
                            "description": "ID of the restaurant"
                        },
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format"
                        },
                        "time": {
                            "type": "string",
                            "description": "Preferred time in HH:MM format"
                        },
                        "party_size": {
                            "type": "integer",
                            "description": "Size of the party"
                        }
                    },
                    "required": ["restaurant_id", "date"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "make_reservation",
                "description": "Make a restaurant reservation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {
                            "type": "string",
                            "description": "ID of the restaurant"
                        },
                        "customer_name": {
                            "type": "string",
                            "description": "Name of the customer"
                        },
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format"
                        },
                        "time": {
                            "type": "string",
                            "description": "Time in HH:MM format"
                        },
                        "party_size": {
                            "type": "integer",
                            "description": "Size of the party"
                        },
                        "email": {
                            "type": "string",
                            "description": "Customer email address"
                        },
                        "phone": {
                            "type": "string",
                            "description": "Customer phone number"
                        }
                    },
                    "required": ["restaurant_id", "customer_name", "date", "time", "party_size"]
                }
            }
        }
    ]
    
    llm.register_tools(tool_definitions)

# Execute a tool call from the LLM
def execute_tool_call(tool_call):
    try:
        function_name = tool_call["function"]["name"]
        arguments = json.loads(tool_call["function"]["arguments"])
        
        # Log tool call if in debug mode
        if DEBUG:
            print(f"Executing tool: {function_name}")
            print(f"Arguments: {arguments}")
        
        if function_name == "search_restaurants":
            restaurants = tools.search_restaurants(
                data_store=data_store,
                cuisine=arguments.get("cuisine"),
                location=arguments.get("location"),
                price_range=arguments.get("price_range"),
                party_size=arguments.get("party_size")
            )
            return format_restaurant_list(restaurants)
        
        elif function_name == "get_restaurant_details":
            restaurant = tools.get_restaurant_details(
                data_store=data_store,
                restaurant_id=arguments.get("restaurant_id")
            )
            return format_restaurant_details(restaurant)
        
        elif function_name == "check_availability":
            available_times = tools.check_availability(
                data_store=data_store,
                restaurant_id=arguments.get("restaurant_id"),
                date=arguments.get("date"),
                time=arguments.get("time"),
                party_size=arguments.get("party_size")
            )
            return format_available_times(arguments.get("date"), available_times)
        
        elif function_name == "make_reservation":
            success, result = tools.make_reservation(
                data_store=data_store,
                restaurant_id=arguments.get("restaurant_id"),
                customer_name=arguments.get("customer_name"),
                date=arguments.get("date"),
                time=arguments.get("time"),
                party_size=arguments.get("party_size"),
                email=arguments.get("email"),
                phone=arguments.get("phone")
            )
            
            if success:
                restaurant = tools.get_restaurant_details(
                    data_store=data_store,
                    restaurant_id=arguments.get("restaurant_id")
                )
                return format_reservation_confirmation(result, restaurant)
            else:
                return f"Sorry, I couldn't make the reservation: {result}"
        
        else:
            return f"I don't know how to execute the tool '{function_name}'"
    
    except Exception as e:
        if DEBUG:
            import traceback
            print(f"Error executing tool: {str(e)}")
            print(traceback.format_exc())
        return f"Error executing tool: {str(e)}"

# Main Streamlit app
def main():
    st.set_page_config(page_title="FoodieSpot Reservations", page_icon="🍽️")
    st.title("🍽️ FoodieSpot Reservations")
    
    # Show environment information in sidebar
    st.sidebar.title("Restaurant Assistant")
    st.sidebar.write(f"**Environment:** {ENVIRONMENT}")
    
    # Show debug information if enabled
    show_debug_info()
    
    # Generate sample data if needed
    if "data_initialized" not in st.session_state:
        with st.spinner("Setting up restaurant data..."):
            # Only print message once
            did_generate = generate_sample_data(data_store, debug=False)
            register_tools()
        st.session_state.data_initialized = True
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Welcome to FoodieSpot! I can help you find restaurants and make reservations. What are you looking for today?"}
        ]
    
    # Add user name input
    if "user_name" not in st.session_state:
        st.session_state.user_name = ""
    
    if not st.session_state.user_name:
        with st.form("user_info_form"):
            name = st.text_input("What's your name?")
            submit = st.form_submit_button("Start Chatting")
            if submit and name:
                st.session_state.user_name = name
                st.rerun()
    else:
        st.sidebar.write(f"Welcome, **{st.session_state.user_name}**!")
        
        # Add button to clear chat history
        if st.sidebar.button("Clear Chat History"):
            st.session_state.messages = [
                {"role": "assistant", "content": f"Hi {st.session_state.user_name}! I've cleared our previous conversation. How can I help you today?"}
            ]
            st.rerun()
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Accept user input if name is provided
    if st.session_state.user_name:
        if prompt := st.chat_input("Type your message here..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # Format messages for the LLM
                    messages = [
                        {"role": "system", "content": f"You are a helpful restaurant reservation assistant for FoodieSpot. The user's name is {st.session_state.user_name}. Help them find restaurants and make reservations. Today's date is {datetime.now().strftime('%Y-%m-%d')}."},
                    ]
                    
                    # Add chat history (last 5 messages)
                    for msg in st.session_state.messages[-5:]:
                        messages.append({"role": msg["role"], "content": msg["content"]})
                    
                    # Call process_message instead of chat directly
                    try:
                        # For tool-enabled mode
                        content, tool_calls = llm.chat(messages, tools=True)
                        
                        # Process tool calls if any
                        if tool_calls:
                            tool_responses = []
                            for tool_call in tool_calls:
                                tool_response = execute_tool_call(tool_call)
                                tool_responses.append(tool_response)
                                
                                # Add tool results to messages for context
                                messages.append({
                                    "role": "assistant",
                                    "content": None,
                                    "tool_calls": [tool_call]
                                })
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call["id"],
                                    "content": tool_response
                                })
                            
                            # Get final response with tool results
                            final_content, _ = llm.chat(messages, tools=False)
                            
                            # Show tool responses first, then the LLM's interpretation
                            for tool_response in tool_responses:
                                st.markdown(tool_response)
                            st.markdown(final_content)
                            
                            # Save the final response with tool results
                            combined_response = "\n\n".join([*tool_responses, final_content])
                            st.session_state.messages.append({"role": "assistant", "content": combined_response})
                        else:
                            # No tool calls, just display the response
                            st.markdown(content)
                            st.session_state.messages.append({"role": "assistant", "content": content})
                    except Exception as e:
                        # Fall back to development mode if there's an error
                        if DEBUG:
                            st.error(f"Error: {str(e)}")
                        
                        # Use simulated response
                        fallback_response = "I'm having trouble processing your request. Let me try a different approach."
                        st.markdown(fallback_response)
                        st.session_state.messages.append({"role": "assistant", "content": fallback_response})

if __name__ == "__main__":
    main()