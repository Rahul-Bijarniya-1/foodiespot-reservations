import os
from datetime import datetime
from utils.llm import LLMService

class LLMProcessor:
    """Manages interactions with the LLM service"""
    
    def __init__(self, api_key=None, model=None):
        """Initialize the LLM processor"""
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.model = model or os.getenv("LLM_MODEL", "llama3-8b-8192")
        self.llm = LLMService(api_key=self.api_key, model=self.model)
        
    def register_tools(self, tool_definitions):
        """Register tools with the LLM service"""
        self.llm.register_tools(tool_definitions)
    
    def process_user_message(self, user_message, messages_history, user_name):
        """Process a user message and generate responses with tool calls"""
        # Format messages for the LLM
        messages = [
            {
                "role": "system", 
                "content": self._get_system_prompt(user_name)
            },
        ]
        
        # Add chat history (last 5 messages)
        for msg in messages_history[-5:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Call LLM to get initial response and any tool calls
        content, tool_calls = self.llm.chat(messages, tools=True)
        
        return messages, content, tool_calls
    
    def generate_final_response(self, messages, tool_responses):
        """Generate final response after processing tool calls"""
        # Get final response with tool results
        final_content, _ = self.llm.chat(messages, tools=False)
        return final_content
    
    def _get_system_prompt(self, user_name):
        """Generate the system prompt with current date and user info"""
        prompt = (
            f"You are a helpful restaurant reservation assistant for FoodieSpot. "
            f"The user's name is {user_name}. "
            f"Help them find restaurants and make reservations. "
            f"Today's date is {datetime.now().strftime('%Y-%m-%d')}.\n\n"
            f"IMPORTANT: You should ALWAYS use the provided tools to answer the user's questions "
            f"about restaurants, availability, or reservations. Do not make up information or "
            f"simulate responses. Use the search_restaurants tool to find options, "
            f"get_restaurant_details to get information about specific restaurants, "
            f"check_availability to find open slots, and make_reservation to book tables."
        )
        return prompt