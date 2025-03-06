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
    format_reservation_confirmation,
    format_reservation_details,
    format_time,
    get_base_prompt,
    get_search_prompt,
    get_reservation_prompt,
    get_confirmation_prompt,
    get_enhanced_reservation_prompt
)
import tools

# Load environment variables with override to ensure .env takes precedence
load_dotenv(override=True)

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

        # Add tool registration info
        st.write(f"**Registered Tools:** {len(llm.tool_definitions)}")
        if llm.tool_definitions:
            for tool in llm.tool_definitions:
                st.write(f"- {tool['function']['name']}")
        else:
            st.write("*No tools registered*")

# Define tools for the LLM
def register_tools():
    """
    Register tools for the LLM with improved descriptions and parameter formatting
    to encourage proper tool usage
    """
    tool_definitions = [
        {
            "type": "function",
            "function": {
                "name": "search_restaurants",
                "description": "ALWAYS use this tool FIRST to find restaurants based on criteria. You must use this before getting details or making reservations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cuisine": {
                            "type": "string",
                            "description": "Type of cuisine (e.g., Italian, Japanese, Indian, Thai)"
                        },
                        "location": {
                            "type": "string", 
                            "description": "Restaurant location (e.g., Downtown, Uptown, West Side)"
                        },
                        "price_range": {
                            "type": "integer",
                            "description": "Maximum price range (1-4, where 1 is least expensive)"
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
                "description": "Use this tool AFTER search_restaurants to get detailed information about a specific restaurant. You MUST use the restaurant_id from search results.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {
                            "type": "string",
                            "description": "ID of the restaurant (e.g., rest_1, rest_2) - must use ID from search_restaurants results"
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
                "description": "Use this tool AFTER get_restaurant_details to check available time slots for a restaurant on a specific date. You MUST have a restaurant_id from previous steps.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {
                            "type": "string",
                            "description": "ID of the restaurant (e.g., rest_1, rest_2) - must use ID from search_restaurants results"
                        },
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format (e.g., 2025-03-06)"
                        },
                        "time": {
                            "type": "string",
                            "description": "Preferred time in HH:MM format, 24-hour clock (e.g., 19:30 for 7:30 PM)"
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
                "description": "Use this tool ONLY AFTER checking availability to make a restaurant reservation. This is the ONLY way to create a valid reservation.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {
                            "type": "string",
                            "description": "ID of the restaurant (e.g., rest_1, rest_2) - must use ID from search_restaurants results"
                        },
                        "customer_name": {
                            "type": "string",
                            "description": "Full name of the customer"
                        },
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format (e.g., 2025-03-06)"
                        },
                        "time": {
                            "type": "string",
                            "description": "Time in HH:MM format, 24-hour clock (e.g., 19:30 for 7:30 PM)"
                        },
                        "party_size": {
                            "type": "integer",
                            "description": "Size of the party"
                        },
                        "email": {
                            "type": "string",
                            "description": "Customer email address for confirmation"
                        },
                        "phone": {
                            "type": "string",
                            "description": "Customer phone number for contact"
                        }
                    },
                    "required": ["restaurant_id", "customer_name", "date", "time", "party_size"]
                }
            }
        }
    ]
    
    # Register the tool definitions with the LLM service
    llm.register_tools(tool_definitions)
    
    # Print tool registration success in debug mode
    # if DEBUG:
    #     print(f"✅ Registered {len(tool_definitions)} tools for LLM use")
    #     for tool in tool_definitions:
    #         print(f"  - {tool['function']['name']}: {tool['function']['description'][:50]}...")

register_tools()

# Helper function to format preferences
def format_preferences(preferences):
    if not preferences:
        return "No preferences set."
    
    result = ""
    for key, value in preferences.items():
        formatted_key = key.replace("_", " ").title()
        result += f"- **{formatted_key}:** {value}\n"
    
    return result

def log_tool_calls(messages, tool_calls):
    """Log tool calls to the debug sidebar"""
    if not DEBUG:
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

def is_valid_date_format(date_str):
    """Check if date is in YYYY-MM-DD format"""
    import re
    return bool(re.match(r"\d{4}-\d{2}-\d{2}", date_str))

def is_valid_time_format(time_str):
    """Check if time is in HH:MM format"""
    import re
    return bool(re.match(r"\d{2}:\d{2}", time_str))

def validate_reservation_parameters(arguments):
    """Validate reservation parameters and fix common issues"""
    required_params = ["restaurant_id", "customer_name", "date", "time", "party_size"]
    
    # Check for missing parameters
    missing = [param for param in required_params if param not in arguments]
    if missing:
        return False, f"Missing required parameters: {', '.join(missing)}"
    
    # Validate and fix date format if needed
    date = arguments.get("date")
    if date and not is_valid_date_format(date):
        try:
            # Try to convert to YYYY-MM-DD format
            import datetime
            import re
            
            # Check if it's in MM/DD/YYYY format
            if re.match(r"\d{1,2}/\d{1,2}/\d{4}", date):
                month, day, year = date.split("/")
                arguments["date"] = f"{year}-{int(month):02d}-{int(day):02d}"
            # Other formats can be handled here
            else:
                return False, f"Could not parse date format: {date}"
        except:
            return False, f"Invalid date format: {date}"
    
    # Validate and fix time format if needed
    time = arguments.get("time")
    if time and not is_valid_time_format(time):
        try:
            # Try to convert to 24-hour format
            import re
            import datetime
            
            # Check if it's in 12-hour format with AM/PM
            am_pm_match = re.match(r"(\d{1,2}):?(\d{2})?\s*(AM|PM)", time, re.IGNORECASE)
            if am_pm_match:
                hour, minute, period = am_pm_match.groups()
                hour = int(hour)
                minute = int(minute) if minute else 0
                
                # Adjust hour for PM
                if period.upper() == "PM" and hour < 12:
                    hour += 12
                elif period.upper() == "AM" and hour == 12:
                    hour = 0
                
                arguments["time"] = f"{hour:02d}:{minute:02d}"
            else:
                return False, f"Could not parse time format: {time}"
        except:
            return False, f"Invalid time format: {time}"
    
    # Convert party_size to integer if it's a string
    if isinstance(arguments.get("party_size"), str):
        try:
            arguments["party_size"] = int(arguments["party_size"])
        except:
            return False, f"Invalid party size: {arguments['party_size']}"
    
    return True, "Parameters are valid"

def add_reservation_debug():
    """Add extra debug information for reservations"""
    # Display all available restaurants
    st.sidebar.subheader("Available Restaurants")
    restaurants = data_store.get_all_restaurants()
    
    # Show first 5 restaurants for easy reference
    for i, rest in enumerate(restaurants[:5]):
        st.sidebar.markdown(f"**{rest.name}** (ID: `{rest.id}`)")
        st.sidebar.markdown(f"Cuisine: {rest.cuisine} | Location: {rest.location}")
        st.sidebar.markdown("---")
    
    # Add reservation monitor
    st.sidebar.subheader("Reservation Monitor")
    if st.sidebar.button("Check Reservations"):
        reservations = data_store.get_all_reservations()
        if reservations:
            st.sidebar.success(f"Found {len(reservations)} reservations")
            for res in reservations:
                rest = data_store.get_restaurant(res.restaurant_id)
                rest_name = rest.name if rest else "Unknown Restaurant"
                st.sidebar.markdown(f"• {res.date} at {res.time} - {rest_name} for {res.party_size} people")
        else:
            st.sidebar.warning("No reservations found in system")
            
            # Check if file exists
            import os
            if os.path.exists(data_store.reservation_file):
                try:
                    with open(data_store.reservation_file, 'r') as f:
                        content = f.read()
                    st.sidebar.code(content, language="json")
                except Exception as e:
                    st.sidebar.error(f"Error reading file: {str(e)}")
            else:
                st.sidebar.error(f"Reservation file not found: {data_store.reservation_file}")
                
    # Add restaurant lookup
    st.sidebar.subheader("Restaurant Lookup")
    restaurant_name = st.sidebar.text_input("Enter name to search")
    if restaurant_name and st.sidebar.button("Search Restaurants"):
        matching = [r for r in restaurants if restaurant_name.lower() in r.name.lower()]
        if matching:
            st.sidebar.success(f"Found {len(matching)} matching restaurants")
            for m in matching:
                st.sidebar.markdown(f"**{m.name}** (ID: `{m.id}`)")
                st.sidebar.markdown(f"Cuisine: {m.cuisine} | Location: {m.location}")
        else:
            st.sidebar.warning(f"No restaurants found with name '{restaurant_name}'")

# Execute a tool call from the LLM
def execute_tool_call(tool_call):
    try:
        function_name = tool_call["function"]["name"]
        arguments = json.loads(tool_call["function"]["arguments"])
        
        # Log tool call if in debug mode
        if DEBUG:
            print(f"Executing tool: {function_name}")
            print(f"Arguments: {json.dumps(arguments, indent=2)}")
        
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
        
        # Modified version of execute_tool_call for the make_reservation case
        elif function_name == "make_reservation":
            # Validate and fix parameters
            valid, message = validate_reservation_parameters(arguments)
            
            if not valid:
                if DEBUG:
                    st.sidebar.error(f"Invalid parameters: {message}")
                return f"I couldn't make the reservation because of a technical issue: {message}"
            
            # Debug output
            if DEBUG:
                st.sidebar.write("### LLM Reservation Attempt")
                st.sidebar.write(f"Arguments after validation: {arguments}")
            
            # More verbose logging for this specific case
            try:
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
                
                if DEBUG:
                    if success:
                        st.sidebar.success(f"✅ Reservation successful: {result.id}")
                    else:
                        st.sidebar.error(f"❌ Reservation failed: {result}")
                    
                    # Check if the reservation was saved correctly
                    reservations = data_store.get_all_reservations()
                    st.sidebar.write(f"Current reservations: {len(reservations)}")
                
                if success:
                    restaurant = tools.get_restaurant_details(
                        data_store=data_store,
                        restaurant_id=arguments.get("restaurant_id")
                    )
                    return format_reservation_confirmation(result, restaurant)
                else:
                    return f"Sorry, I couldn't make the reservation: {result}"
            except Exception as e:
                if DEBUG:
                    import traceback
                    st.sidebar.error(f"Exception in make_reservation: {str(e)}")
                    st.sidebar.code(traceback.format_exc())
                return f"Sorry, I couldn't make the reservation due to an error: {str(e)}"
        
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
                    current_date = datetime.now().strftime('%Y-%m-%d')
                    
                    # Choose the appropriate prompt based on message content
                    user_message = prompt.lower()
                    if any(word in user_message for word in ["find", "search", "looking", "cuisine", "restaurant"]):
                        # Use search-focused prompt
                        system_prompt = get_search_prompt(user_name=st.session_state.user_name)
                    elif any(word in user_message for word in ["book", "reserve", "reservation", "time", "date"]):
                        # Use reservation-focused prompt
                        system_prompt = get_enhanced_reservation_prompt(
                            user_name=st.session_state.user_name,
                            current_date=current_date
                        )
                    else:
                        # Use base prompt
                        system_prompt = get_base_prompt(
                            user_name=st.session_state.user_name,
                            current_date=current_date
                        )
                    
                    # In the main chat loop, update the system prompt addition:
                    CRITICAL_TOOL_INSTRUCTIONS = """
                    CRITICAL INSTRUCTIONS FOR TOOL USAGE:
                    1. For initial restaurant search:
                       - Use search_restaurants with cuisine and/or location
                       - ALWAYS include restaurant IDs in search results
                       Example: search_restaurants({"cuisine": "Italian"})

                    2. When user selects a specific restaurant:
                       - Use get_restaurant_details with the EXACT restaurant_id from search results
                       - NEVER use restaurant names as IDs
                       Example: get_restaurant_details({"restaurant_id": "rest_1"})

                    3. For checking availability:
                       - Use check_availability with the EXACT restaurant_id
                       Example: check_availability({"restaurant_id": "rest_1", "date": "2025-03-05"})

                    4. For making reservations:
                       - Use make_reservation with the EXACT restaurant_id
                       Example: make_reservation({"restaurant_id": "rest_1", "date": "2025-03-05", ...})

                    NEVER make up restaurant information. ALWAYS use the appropriate tool for each step.
                    ALWAYS include restaurant IDs in your responses when listing restaurants.
                    """
                    
                    # Update the system prompt in the messages list
                    messages = [
                        {"role": "system", "content": system_prompt + CRITICAL_TOOL_INSTRUCTIONS}
                    ]
                    
                    # Add chat history (last 5 messages)
                    for msg in st.session_state.messages[-5:]:
                        messages.append({"role": msg["role"], "content": msg["content"]})


                    # Before the LLM call
                    if DEBUG:
                        print("System prompt:", system_prompt)
                        print("Messages:", messages)
                        print("Tools enabled:", True)
                        print("Registered tools:", len(llm.tool_definitions))  # Use tool_definitions instead
    
                        # Add more detailed tool logging
                        for tool in llm.tool_definitions:
                            print(f"- {tool['function']['name']}")
                    
                    # Call the LLM
                    try:
                        # For tool-enabled mode
                        content, tool_calls = llm.chat(messages, tools=True)
                        print("Tool calls returned:", tool_calls)
                        
                        # Debug: Log the messages sent to the LLM
                        if DEBUG:
                            with st.sidebar.expander("Messages Sent to LLM"):
                                for msg in messages:
                                    st.write(f"**{msg['role']}**: {msg['content'][:100]}...")
                        
                        # Log tool calls if any
                        log_tool_calls(messages, tool_calls)
                        
                        # Process tool calls if any
                        if tool_calls:
                            tool_responses = []
                            
                            # Track if we have a successful reservation for special handling
                            successful_reservation = None
                            reservation_restaurant = None
                            
                            for tool_call in tool_calls:
                                tool_response = execute_tool_call(tool_call)
                                tool_responses.append(tool_response)
                                
                                # Check if this was a successful reservation
                                if tool_call["function"]["name"] == "make_reservation":
                                    arguments = json.loads(tool_call["function"]["arguments"])
                                    if "Sorry, I couldn't make the reservation" not in tool_response:
                                        # Get the reservation and restaurant for confirmation
                                        reservations = data_store.get_all_reservations()
                                        if reservations:
                                            successful_reservation = reservations[-1]  # Most recent reservation
                                            reservation_restaurant = tools.get_restaurant_details(
                                                data_store=data_store,
                                                restaurant_id=arguments.get("restaurant_id")
                                            )
                                
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
                            
                            # If we have a successful reservation, add confirmation context
                            if successful_reservation and reservation_restaurant:
                                confirmation_prompt = get_confirmation_prompt(
                                    successful_reservation, 
                                    reservation_restaurant
                                )
                                messages.append({
                                    "role": "system",
                                    "content": confirmation_prompt
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
    
    # Add a debug section to test reservations directly
    if DEBUG and st.session_state.user_name:
        with st.sidebar.expander("Debug: Test Reservation"):
            with st.form("test_reservation"):
                rest_id = st.text_input("Restaurant ID", "rest_1")
                name = st.text_input("Customer Name", st.session_state.user_name)
                date = st.date_input("Date").strftime("%Y-%m-%d")
                time = st.time_input("Time").strftime("%H:%M")
                party_size = st.number_input("Party Size", 1, 10, 2)
                email = st.text_input("Email", "test@example.com")
                submit = st.form_submit_button("Make Test Reservation")
                
                if submit:
                    success, result = tools.make_reservation(
                        data_store=data_store,
                        restaurant_id=rest_id,
                        customer_name=name,
                        date=date,
                        time=time,
                        party_size=party_size,
                        email=email
                    )
                    
                    if success:
                        restaurant = tools.get_restaurant_details(data_store=data_store, restaurant_id=rest_id)
                        st.success(format_reservation_confirmation(result, restaurant))
                        
                        # Check if the reservation was saved correctly
                        reservations = data_store.get_all_reservations()
                        st.write(f"Current reservations: {len(reservations)}")
                        
                        # Display the reservation file contents
                        if os.path.exists(data_store.reservation_file):
                            st.write(f"Reservation file exists: {data_store.reservation_file}")
                            try:
                                with open(data_store.reservation_file, 'r') as f:
                                    st.code(f.read())
                            except Exception as e:
                                st.error(f"Error reading file: {e}")
                        else:
                            st.error(f"Reservation file does not exist: {data_store.reservation_file}")
                    else:
                        st.error(f"Reservation failed: {result}")

    # Add debug section for forcing a reservation
    if DEBUG and st.session_state.user_name:
        with st.sidebar.expander("Debug: Force Reservation Intent"):
            if st.button("Force LLM to Make a Reservation"):
                # Add a message to the chat history instructing to make a reservation
                restaurant = data_store.get_restaurant("rest_1")
                if restaurant:
                    force_msg = f"Please make a reservation at {restaurant.name} for tomorrow at 7:00 PM for 2 people. My name is {st.session_state.user_name}."
                    st.session_state.messages.append({"role": "user", "content": force_msg})
                    st.experimental_rerun()

if __name__ == "__main__":
    main()