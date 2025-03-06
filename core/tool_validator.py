import json
import re

class ToolValidator:
    """
    Validates and filters tool calls to prevent LLM from using hallucinated parameters.
    """
    
    @staticmethod
    def validate_search_restaurants_tool(tool_call, user_query):
        """
        Validate that search_restaurants tool calls only use parameters
        explicitly mentioned by the user.
        """
        if not tool_call or tool_call["function"]["name"] != "search_restaurants":
            return True
        
        user_query = user_query.lower()
        try:
            arguments = json.loads(tool_call["function"]["arguments"])
            
            # Check for hallucinated parameters
            for param, value in arguments.items():
                if param == "cuisine" and value:
                    if not ToolValidator._mentioned_cuisine(user_query, value):
                        return False
                
                if param == "location" and value:
                    if not ToolValidator._mentioned_location(user_query, value):
                        return False
                
                if param == "price_range" and value:
                    if not ToolValidator._mentioned_price(user_query, value):
                        return False
                        
            return True
        except:
            return False
    
    @staticmethod
    def _mentioned_cuisine(query, cuisine):
        """Check if cuisine was mentioned in the query"""
        # Convert both to lowercase for comparison
        cuisine = cuisine.lower()
        
        # Direct mention of cuisine
        if cuisine in query:
            return True
            
        # Common cuisine aliases/misspellings
        cuisine_variations = {
            "italian": ["pasta", "pizza", "italian food"],
            "chinese": ["chinese food", "asian", "dim sum"],
            "japanese": ["sushi", "ramen", "japanese food"],
            "mexican": ["tacos", "mexican food", "burritos"],
            "indian": ["curry", "indian food", "tikka"],
            "thai": ["thai food", "pad thai"],
            "american": ["burger", "american food", "steak"],
            "french": ["french food", "bistro"]
        }
        
        # Check for variations
        if cuisine in cuisine_variations:
            for variation in cuisine_variations[cuisine]:
                if variation in query:
                    return True
        
        return False
    
    @staticmethod
    def _mentioned_location(query, location):
        """Check if location was mentioned in the query"""
        location = location.lower()
        
        # Direct mention of location
        if location in query:
            return True
            
        # Common location aliases
        location_variations = {
            "downtown": ["city center", "central"],
            "uptown": ["upper", "north"],
            "midtown": ["middle", "center"],
            "west side": ["western", "west"],
            "east side": ["eastern", "east"],
            "waterfront": ["by the water", "near water", "riverside", "lakeside"]
        }
        
        # Check for variations
        if location in location_variations:
            for variation in location_variations[location]:
                if variation in query:
                    return True
        
        return False
    
    @staticmethod
    def _mentioned_price(query, price_range):
        """Check if price range was mentioned in the query"""
        # Look for $ symbols
        dollar_count = query.count('$')
        if 1 <= dollar_count <= 4:
            return dollar_count >= price_range
            
        # Look for text mentions of price
        price_patterns = {
            1: ["cheap", "inexpensive", "budget", "affordable"],
            2: ["moderate", "mid-range", "reasonable"],
            3: ["expensive", "high-end", "pricey"],
            4: ["very expensive", "luxury", "top-end", "finest"]
        }
        
        # Check if the query mentions price range
        if price_range in price_patterns:
            for pattern in price_patterns[price_range]:
                if pattern in query:
                    return True
                
        # General mentions of price that don't specify a level
        price_words = ["price", "cost", "expensive", "cheap", "affordable", "budget"]
        for word in price_words:
            if word in query:
                return True
                
        return False