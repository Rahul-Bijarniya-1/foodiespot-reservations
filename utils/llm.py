import os
import json
import requests
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import re

class LLMService:
    """Simple service for interacting with a language model API"""
    
    def __init__(self, api_key=None, model="llama3-8b-8192"):
        """Initialize the LLM service"""
        self.api_key = api_key or os.environ.get("LLM_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = model
        self.tool_definitions = []
        self.tools = []  # Add this new attribute
        
        # Keep a simple conversation memory
        self.conversation_memory = []
    
    def register_tools(self, tools):
        """Register tools that the LLM can call"""
        self.tool_definitions = tools
        self.tools = tools  # Store in new attribute
    
    def process_message(self, user_message: str, customer_name: str = "") -> str:
        """
        Process a user message and generate a response
        
        Args:
            user_message: The user's message
            customer_name: The name of the customer (optional)
            
        Returns:
            Generated response from the LLM
        """
        # Add message to memory
        self.conversation_memory.append({"role": "user", "content": user_message})
        
        # Prepare system prompt with customer info
        system_prompt = f"You are a helpful restaurant reservation assistant for FoodieSpot."
        if customer_name:
            system_prompt += f" You're speaking with {customer_name}."
        system_prompt += " Help them find restaurants and make reservations."
        
        # Prepare messages for LLM
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add recent conversation history (last 5 messages)
        if len(self.conversation_memory) > 0:
            for msg in self.conversation_memory[-5:]:
                messages.append(msg)
        
        # Get LLM response
        try:
            content, tool_calls = self.chat(messages)
            
            # Add response to memory
            self.conversation_memory.append({"role": "assistant", "content": content})
            
            return content, tool_calls
        except Exception as e:
            error_response = f"I apologize, but I'm having trouble processing your request right now. Error: {str(e)}"
            self.conversation_memory.append({"role": "assistant", "content": error_response})
            return error_response, None
    
    def chat(self, messages, tools=True, temperature=0.2) -> Tuple[str, Optional[List]]:
        """Send a chat request to the LLM"""
        if not self.api_key:
            return self._simulate_response(messages)
        
        # Analyze the user's intent
        last_user_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user_message = msg["content"].lower()
                break
        
        # Determine which tool to use based on context
        force_tool = None
        tool_arguments = {}
        
        # Check if user is selecting a specific restaurant
        if "go with" in last_user_message or "choose" in last_user_message or "select" in last_user_message:
            force_tool = "get_restaurant_details"
            # Extract restaurant name and find matching ID from previous search results
            restaurant_name = None
            restaurant_id = None
            
            # Look for the restaurant name in the last assistant message
            for msg in reversed(messages):
                if msg["role"] == "assistant" and "**" in msg["content"]:
                    # Extract restaurant names and IDs from the previous search results
                    matches = re.findall(r'\*\*(.*?)\*\* - .*?rest_\d+', msg["content"])
                    if matches:
                        for match in matches:
                            if match.lower() in last_user_message.lower():
                                # Extract the restaurant ID
                                id_match = re.search(r'(rest_\d+)', msg["content"])
                                if id_match:
                                    restaurant_id = id_match.group(1)
                                    break
                    break
            
            if restaurant_id:
                tool_arguments = {"restaurant_id": restaurant_id}
            else:
                # If we can't find the ID, do a new search
                force_tool = "search_restaurants"
                # Extract cuisine from previous search if available
                for msg in reversed(messages):
                    if msg["role"] == "assistant" and any(cuisine in msg["content"].lower() for cuisine in ["indian", "italian", "chinese"]):
                        for cuisine in ["indian", "italian", "chinese"]:
                            if cuisine in msg["content"].lower():
                                tool_arguments = {"cuisine": cuisine.capitalize()}
                                break
                        break
        
        # Check if this is a search request
        elif any(word in last_user_message for word in ["find", "search", "show", "list", "looking"]):
            force_tool = "search_restaurants"
            # Extract cuisine type if mentioned
            for cuisine in ["italian", "chinese", "indian", "japanese", "thai"]:
                if cuisine in last_user_message:
                    tool_arguments["cuisine"] = cuisine.capitalize()
            # Extract location if mentioned
            for location in ["downtown", "uptown", "waterfront"]:
                if location in last_user_message:
                    tool_arguments["location"] = location.capitalize()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1000
        }
        
        # Add tools if requested and available
        if tools and self.tool_definitions:
            data["functions"] = [tool["function"] for tool in self.tool_definitions]
            
            # Force specific tool usage if determined
            if force_tool:
                data["function_call"] = {
                    "name": force_tool,
                    "arguments": json.dumps(tool_arguments)
                }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 429:  # Rate limit error
                print("Rate limit reached, falling back to previous results")
                return "I already have the information you need. Let me help you with that.", None
            
            if response.status_code != 200:
                print(f"API Error {response.status_code}: {response.text}")
                if force_tool:
                    # Create a manual tool call
                    tool_calls = [{
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": force_tool,
                            "arguments": json.dumps(tool_arguments)
                        }
                    }]
                    return "Let me help you with that.", tool_calls
                return "I apologize, but I'm having trouble processing your request. Could you please try again?", None
            
            result = response.json()
            message = result["choices"][0]["message"]
            content = message.get("content", "")
            
            # Handle function calls
            function_call = message.get("function_call")
            if function_call:
                tool_calls = [{
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": function_call["name"],
                        "arguments": function_call["arguments"]
                    }
                }]
                return content, tool_calls
            
            return content, None
        
        except Exception as e:
            print(f"Error calling LLM API: {str(e)}")
            return self._simulate_response(messages)
    
    def _simulate_response(self, messages) -> Tuple[str, Optional[List]]:
        """Simulate an LLM response for development without an API key"""
        # Get the last user message
        user_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                user_message = msg["content"].lower()
                break
        
        # Simple keyword-based responses for development
        if "hello" in user_message or "hi" in user_message:
            return "Hello! I'm your restaurant reservation assistant. How can I help you today?", None
        
        if "restaurant" in user_message:
            if "italian" in user_message:
                return "I'd be happy to help you find an Italian restaurant. What area would you like to dine in?", [
                    {
                        "id": "call_search",
                        "type": "function",
                        "function": {
                            "name": "search_restaurants",
                            "arguments": json.dumps({"cuisine": "Italian", "limit": 3})
                        }
                    }
                ]
            
            if "search" in user_message:
                return "I'll help you search for restaurants. Could you tell me what cuisine you're interested in?", None
        
        if "reservation" in user_message or "book" in user_message:
            return "I'd be happy to help you make a reservation. Which restaurant would you like to book?", None
        
        if "available" in user_message or "time" in user_message:
            return "I can check availability for you. Which restaurant and what date are you interested in?", None
        
        # Default response
        return "I'm here to help you find and book restaurants. What are you looking for today?", None
    
    def parse_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse tool calling format from LLM response text"""
        try:
            lines = response.strip().split('\n')
            tool_call = {}
            
            for line in lines:
                if line.startswith('TOOL:'):
                    tool_call['name'] = line.replace('TOOL:', '').strip()
                elif line.startswith('PARAMS:'):
                    params_str = line.replace('PARAMS:', '').strip()
                    tool_call['parameters'] = json.loads(params_str)
            
            return tool_call if 'name' in tool_call else None
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing tool call: {e}")
            return None