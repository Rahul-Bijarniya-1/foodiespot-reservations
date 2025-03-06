import os
import json
import requests
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

class LLMService:
    """Simple service for interacting with a language model API"""
    
    def __init__(self, api_key=None, model="llama3-8b-8192"):
        """Initialize the LLM service"""
        self.api_key = api_key or os.environ.get("LLM_API_KEY")
        self.api_url = os.getenv("LLM_API_URL", "https://api.groq.com/openai/v1/chat/completions")
        self.model = model
        self.tool_definitions = []
    
    def register_tools(self, tools):
        """Register tools that the LLM can call"""
        self.tool_definitions = tools
    
    def chat(self, messages, tools=True, temperature=0.2) -> Tuple[str, Optional[List]]:
        """
        Send a chat request to the LLM
        
        Args:
            messages: List of message objects with role and content
            tools: Whether to enable tool calling
            temperature: Sampling temperature (0-1)
        
        Returns:
            Tuple of (response_content, tool_calls)
        """
        # If we don't have an API key, return an error
        if not self.api_key:
            return "Sorry, I'm not able to process your request without my API key. Please check your .env file.", None
        
        # Prepare the API request
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
            data["tools"] = self.tool_definitions
        
        # Send the request
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            # Check for errors
            if response.status_code != 200:
                print(f"API Error {response.status_code}: {response.text}")
                return f"I'm having trouble connecting to my brain right now (Error {response.status_code}). Please check your API key and configuration.", None
            
            result = response.json()
            
            # Extract content and tool calls
            message = result["choices"][0]["message"]
            content = message.get("content", "")
            tool_calls = message.get("tool_calls", None)
            
            return content, tool_calls
        except Exception as e:
            print(f"Error calling LLM API: {e}")
            return f"I encountered an error while processing your request: {str(e)}", None