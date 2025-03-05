import random
import uuid
from models.restaurant import Restaurant

def generate_sample_restaurants(count=20):
    """Generate sample restaurant data"""
    cuisines = ['Italian', 'Japanese', 'Indian', 'Mexican', 'Chinese', 'Thai', 'American', 'French']
    locations = ['Downtown', 'Uptown', 'Midtown', 'West Side', 'East Side', 'Waterfront']
    
    restaurants = []
    
    for i in range(count):
        # Select random values
        cuisine = random.choice(cuisines)
        location = random.choice(locations)
        capacity = random.randint(20, 100)
        price_range = random.randint(1, 4)
        rating = round(random.uniform(3.0, 5.0), 1)
        
        # Create name
        if random.random() < 0.5:
            name = f"The {random.choice(['Tasty', 'Delicious', 'Amazing'])} {cuisine}"
        else:
            name = f"{location} {cuisine} {random.choice(['Bistro', 'Restaurant', 'Kitchen', ''])}"
        
        # Create description
        description = f"{name} offers authentic {cuisine} cuisine in {location}. "
        description += f"Seating capacity of {capacity} and a cozy atmosphere."
        
        # Create hours
        hours = {
            "weekday": {
                "open": f"{random.randint(10, 12)}:00",
                "close": f"{random.randint(20, 23)}:00"
            },
            "weekend": {
                "open": f"{random.randint(8, 11)}:00",
                "close": f"{random.randint(21, 23)}:00"
            }
        }
        
        # Create restaurant
        restaurant = Restaurant(
            id=f"rest_{i+1}",
            name=name,
            cuisine=cuisine,
            location=location,
            capacity=capacity,
            price_range=price_range,
            rating=rating,
            description=description,
            hours=hours
        )
        
        restaurants.append(restaurant)
    
    return restaurants

def generate_sample_data(data_store, debug=False):
    """Generate and save sample data to the data store"""
    # Check if data already exists
    existing_restaurants = data_store.get_all_restaurants()
    
    if not existing_restaurants:
        print("Generating sample restaurant data...")
        restaurants = generate_sample_restaurants()
        data_store.add_restaurants(restaurants)
        print(f"Created {len(restaurants)} sample restaurants")
        return True
    elif debug:
        # Only print if debug is enabled
        print(f"Data store already contains {len(existing_restaurants)} restaurants")
    return False