import re

class QueryValidator:
    """
    Validates user queries to prevent LLM from making assumptions
    about search parameters when the user's request is too vague.
    """
    
    @staticmethod
    def is_vague_query(query):
        """
        Check if a query is too vague to directly search restaurants.
        Returns True if the query doesn't contain specific search criteria.
        """
        query = query.lower()
        
        # Define patterns for specific queries
        cuisine_pattern = r'(italian|french|indian|chinese|japanese|thai|mexican|american|mediterranean)'
        location_pattern = r'(downtown|uptown|midtown|west side|east side|waterfront)'
        
        # If query explicitly mentions "search" or includes specific criteria, it's not vague
        if (re.search(cuisine_pattern, query) or
            re.search(location_pattern, query) or
            'search' in query or
            'find' in query or
            'looking for' in query or
            'price' in query or
            '$' in query or
            'people' in query or
            'person' in query):
            return False
        
        # Check for very generic requests
        vague_patterns = [
            r'show me options',
            r'give me options',
            r'list restaurants',
            r'what do you have',
            r'what\'s available',
            r'show me restaurants',
            r'give me restaurants',
            r'restaurants',
            r'options'
        ]
        
        for pattern in vague_patterns:
            if re.search(pattern, query):
                return True
        
        return False
    
    @staticmethod
    def get_clarification_prompt():
        """
        Return a clarification prompt for vague queries
        """
        return (
            "I'd be happy to help you find a restaurant! To give you the best recommendations, "
            "could you please tell me more about what you're looking for? For example:\n\n"
            "- What type of cuisine are you interested in? (Italian, Chinese, Thai, etc.)\n"
            "- Do you have a preferred location?\n"
            "- What's your price range? ($ to $$$$)\n"
            "- How many people will be dining?\n\n"
            "The more details you provide, the better I can help you find the perfect restaurant!"
        )