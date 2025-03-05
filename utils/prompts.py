"""
System prompts for FoodieSpot Restaurant Reservation System
"""

def get_base_prompt(user_name="", current_date=""):
    """
    Get the base system prompt for the restaurant assistant
    
    Args:
        user_name: Name of the current user (optional)
        current_date: Current date in YYYY-MM-DD format (optional)
    
    Returns:
        System prompt string
    """
    prompt = "You are a helpful restaurant reservation assistant for FoodieSpot."
    
    if user_name:
        prompt += f" The user's name is {user_name}."
    
    prompt += " Help them find restaurants and make reservations."
    
    if current_date:
        prompt += f" Today's date is {current_date}."
    
    # Add more context about how to interact with the user
    prompt += """
    
    Remember to:
    1. Be friendly and conversational
    2. Ask for all necessary information for restaurant searches (cuisine, location, etc.)
    3. Suggest popular restaurants if the user is unsure
    4. Confirm all reservation details clearly
    5. Provide helpful alternatives if requested times are unavailable
    """
    
    return prompt

def get_search_prompt(user_name="", preferences=None):
    """
    Get the system prompt focused on restaurant search
    
    Args:
        user_name: Name of the current user (optional)
        preferences: Dictionary of user preferences (optional)
    
    Returns:
        System prompt string
    """
    prompt = get_base_prompt(user_name)
    
    prompt += """
    
    Focus on helping the user find a restaurant that matches their preferences.
    Ask about:
    - Cuisine type
    - Location/neighborhood
    - Price range
    - Party size
    - Special requirements (outdoor seating, vegetarian options, etc.)
    """
    
    # Add user preferences if available
    if preferences and isinstance(preferences, dict):
        prompt += "\n\nThe user has the following preferences:"
        
        if preferences.get("cuisine"):
            prompt += f"\n- Cuisine: {preferences['cuisine']}"
        
        if preferences.get("location"):
            prompt += f"\n- Location: {preferences['location']}"
        
        if preferences.get("price_range"):
            prompt += f"\n- Price Range: {'$' * preferences['price_range']}"
        
        if preferences.get("dietary_restrictions"):
            prompt += f"\n- Dietary Restrictions: {preferences['dietary_restrictions']}"
    
    return prompt

def get_reservation_prompt(user_name="", current_date=""):
    """
    Get the system prompt focused on making reservations
    
    Args:
        user_name: Name of the current user (optional)
        current_date: Current date in YYYY-MM-DD format (optional)
    
    Returns:
        System prompt string
    """
    prompt = get_base_prompt(user_name, current_date)
    
    prompt += """

    IMPORTANT: You MUST use the make_reservation tool to create reservations. NEVER tell the user a reservation is confirmed unless you have successfully called the make_reservation tool and received a confirmation.
    
    To make a reservation, follow these steps:
    1. Collect all required information: restaurant_id, date, time, party_size, and customer_name
    2. Call the make_reservation tool with this information
    3. Only confirm the reservation if the tool returns success
    4. Use the exact details returned by the tool in your confirmation message
    
    Never create fictional reservation details like 'Reservation ID: #RSVP-001' or restaurants that don't exist. Only use information that comes directly from the system.
    
    Focus on helping the user make a reservation. Ensure you collect:
    - Restaurant selection (ID or name)
    - Date
    - Time
    - Party size
    - Contact information (name, email, phone)
    
    After making a reservation, always confirm all details with the user and provide:
    - Restaurant name and location
    - Date and time of reservation
    - Party size
    - Reservation ID for future reference
    
    If the desired time is unavailable, offer alternative times or dates.
    """
    
    return prompt

def get_confirmation_prompt(reservation, restaurant):
    """
    Get a prompt for confirming a specific reservation
    
    Args:
        reservation: Reservation object
        restaurant: Restaurant object
    
    Returns:
        System prompt string
    """
    prompt = f"""
    The user has just made a reservation with the following details:
    
    - Restaurant: {restaurant.name}
    - Location: {restaurant.location}
    - Date: {reservation.date}
    - Time: {reservation.time}
    - Party size: {reservation.party_size}
    - Reservation ID: {reservation.id}
    
    Confirm these details with the user and ask if they need anything else.
    Inform them that they can refer to their reservation by ID if they need to modify or cancel it later.
    """
    
    return prompt