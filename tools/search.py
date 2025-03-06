def search_restaurants(data_store, cuisine=None, location=None, 
                      price_range=None, party_size=None, limit=5):
    """
    Search for restaurants based on criteria
    
    Args:
        data_store: Data storage instance
        cuisine: Type of cuisine
        location: Restaurant location
        price_range: Price range (1-4)
        party_size: Size of the dining party
        limit: Maximum number of results
    
    Returns:
        List of matching restaurants
    """
    restaurants = data_store.get_all_restaurants()
    results = []
    
    for restaurant in restaurants:
        # Apply filters
        if cuisine and cuisine.lower() not in restaurant.cuisine.lower():
            continue
        
        if location and location.lower() not in restaurant.location.lower():
            continue
        
        if price_range and restaurant.price_range > price_range:
            continue
        
        if party_size and party_size > restaurant.capacity:
            continue
        
        results.append(restaurant)
        
        if len(results) >= limit:
            break
    
    return results

def get_restaurant_details(data_store, restaurant_id):
    """
    Get detailed information about a restaurant by ID or name
    
    Args:
        data_store: Data storage instance
        restaurant_id: ID of the restaurant OR name of the restaurant
    
    Returns:
        Restaurant object or None if not found
    """
    # First try to get restaurant directly by ID
    restaurant = data_store.get_restaurant(restaurant_id)
    
    # If not found by ID, try to search by name
    if not restaurant:
        # Get all restaurants and search by name (case-insensitive)
        all_restaurants = data_store.get_all_restaurants()
        for rest in all_restaurants:
            # Check if the provided ID is actually a restaurant name
            if restaurant_id.lower() in rest.name.lower():
                restaurant = rest
                break
    
    return restaurant

def recommend_restaurants(data_store, preferences, limit=3):
    """
    Recommend restaurants based on user preferences
    
    Args:
        data_store: Data storage instance
        preferences: Dictionary of user preferences
        limit: Maximum number of recommendations
    
    Returns:
        List of recommended restaurants
    """
    cuisine = preferences.get('cuisine')
    location = preferences.get('location')
    price_range = preferences.get('price_range')
    
    restaurants = data_store.get_all_restaurants()
    scored_restaurants = []
    
    for restaurant in restaurants:
        score = 0
        
        # Score based on cuisine match
        if cuisine and cuisine.lower() in restaurant.cuisine.lower():
            score += 3
        
        # Score based on location
        if location and location.lower() in restaurant.location.lower():
            score += 2
        
        # Score based on price range
        if price_range and restaurant.price_range <= price_range:
            score += 1
        
        # Bonus for high rating
        score += restaurant.rating * 0.5
        
        scored_restaurants.append((restaurant, score))
    
    # Sort by score and return top recommendations
    scored_restaurants.sort(key=lambda x: x[1], reverse=True)
    return [r for r, _ in scored_restaurants[:limit]]