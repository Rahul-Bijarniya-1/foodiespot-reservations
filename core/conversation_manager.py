import json
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

class ConversationManager:
    """
    Manages the conversation flow and tool execution following LangChain-style 
    function calling patterns where the LLM determines the intent.
    """
    
    def __init__(self, llm_service, data_store):
        """Initialize the conversation manager"""
        self.llm_service = llm_service
        self.data_store = data_store
        
    def process_message(self, user_message: str, conversation_history: List[Dict], 
                       user_name: str) -> Tuple[str, List[str], List[Dict]]:
        """
        Process a user message using proper tool calling architecture
        
        Args:
            user_message: The user's message
            conversation_history: List of previous messages
            user_name: The user's name
            
        Returns:
            Tuple of (final_response, tool_results, updated_messages)
        """
        # Prepare the system prompt
        system_message = self._create_system_message(user_name)
        
        # Format messages for the LLM
        messages = [system_message]
        
        # Add conversation history (last 5 messages)
        for msg in conversation_history[-5:]:
            messages.append(msg)
        
        # Add the current user message
        messages.append({"role": "user", "content": user_message})
        
        # First LLM call to determine intent and potentially call tools
        response_content, tool_calls = self.llm_service.chat(messages)
        
        # Initial response without tool calls
        if not tool_calls:
            return response_content, [], messages
        
        print(response_content,"\n")
              
        # print(tool_calls,"\n")
            
        # Process tool calls
        tool_results = []
        for tool_call in tool_calls:
            # Execute the tool and get result
            tool_result = self._execute_tool(tool_call)
            tool_results.append(tool_result)
            
            # Add the tool call to message history
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [tool_call]
            })
            
            # Add tool result to message history
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": tool_result
            })
        
        # Second LLM call to generate final response with tool results
        final_content, _ = self.llm_service.chat(messages, tools=False)
        
        return final_content, tool_results, messages
        
    def _create_system_message(self, user_name: str) -> Dict[str, str]:
        """Create the system message with instructions"""
        content = (
            f"You are a helpful restaurant reservation assistant for FoodieSpot. "
            f"The user's name is {user_name}. "
            f"Today's date is {datetime.now().strftime('%Y-%m-%d')}.\n\n"
            f"TOOLS AND CAPABILITIES:\n"
            f"- You can search for restaurants by cuisine, location, price range, and party size\n"
            f"- You can get detailed information about specific restaurants\n"
            f"- You can check availability for restaurants on specific dates and times\n"
            f"- You can make reservations for users\n\n"
            f"GUIDELINES:\n"
            f"1. Analyze the user's request to determine their intent\n"
            f"2. Choose the appropriate tool based on the user's intent\n"
            f"3. If the user's request is ambiguous, ask clarifying questions before using tools\n"
            f"4. Do not make assumptions about parameters not explicitly stated by the user\n"
            f"5. Present tool results in a helpful, conversational way\n"
            f"6. If no tool is needed to respond, simply answer directly\n\n"
            f"Remember: The user can't see the tools - focus on answering their needs, not explaining the tools."
        )
        
        return {"role": "system", "content": content}
        
    def _execute_tool(self, tool_call: Dict) -> str:
        """Execute a tool call and return the result"""
        try:
            function_name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"]["arguments"])
            
            if function_name == "search_restaurants":
                from tools import search_restaurants
                from utils import format_restaurant_list
                
                restaurants = search_restaurants(
                    data_store=self.data_store,
                    cuisine=arguments.get("cuisine"),
                    location=arguments.get("location"),
                    price_range=arguments.get("price_range"),
                    party_size=arguments.get("party_size")
                )
                return format_restaurant_list(restaurants)
            
            elif function_name == "get_restaurant_details":
                from tools import get_restaurant_details
                from utils import format_restaurant_details
                
                restaurant = get_restaurant_details(
                    data_store=self.data_store,
                    restaurant_id=arguments.get("restaurant_id")
                )
                return format_restaurant_details(restaurant)
            
            elif function_name == "check_availability":
                from tools import check_availability
                from utils import format_available_times
                
                available_times = check_availability(
                    data_store=self.data_store,
                    restaurant_id=arguments.get("restaurant_id"),
                    date=arguments.get("date"),
                    time=arguments.get("time"),
                    party_size=arguments.get("party_size")
                )
                return format_available_times(arguments.get("date"), available_times)
            
            elif function_name == "make_reservation":
                from tools import make_reservation, get_restaurant_details
                from utils import format_reservation_confirmation
                
                success, result = make_reservation(
                    data_store=self.data_store,
                    restaurant_id=arguments.get("restaurant_id"),
                    customer_name=arguments.get("customer_name"),
                    date=arguments.get("date"),
                    time=arguments.get("time"),
                    party_size=arguments.get("party_size"),
                    email=arguments.get("email"),
                    phone=arguments.get("phone")
                )
                
                if success:
                    restaurant = get_restaurant_details(
                        data_store=self.data_store,
                        restaurant_id=arguments.get("restaurant_id")
                    )
                    return format_reservation_confirmation(result, restaurant)
                else:
                    return f"Sorry, I couldn't make the reservation: {result}"
            
            else:
                return f"Unknown tool: {function_name}"
                
        except Exception as e:
            import traceback
            print(f"Error executing tool: {str(e)}")
            print(traceback.format_exc())
            return f"Error executing tool: {str(e)}"