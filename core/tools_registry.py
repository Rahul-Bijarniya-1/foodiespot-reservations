import json
import os
import tools
from utils import (
    format_restaurant_list,
    format_restaurant_details,
    format_available_times,
    format_reservation_confirmation
)

def register_tools():
    """Define tools for the LLM to use"""
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
    
    return tool_definitions

def execute_tool_call(tool_call, data_store):
    """Execute a tool call from the LLM"""
    try:
        function_name = tool_call["function"]["name"]
        arguments = json.loads(tool_call["function"]["arguments"])
        
        # Log tool call if in debug mode
        if os.getenv("DEBUG", "false").lower() == "true":
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
        if os.getenv("DEBUG", "false").lower() == "true":
            import traceback
            print(f"Error executing tool: {str(e)}")
            print(traceback.format_exc())
        return f"Error executing tool: {str(e)}"