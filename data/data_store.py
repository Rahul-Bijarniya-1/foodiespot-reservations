import json
import os
from datetime import datetime
from models.restaurant import Restaurant
from models.reservation import Reservation

class DataStore:
    """Simple JSON file-based data storage"""
    
    def __init__(self, data_dir="data"):
        """Initialize with directory to store data files"""
        self.data_dir = data_dir
        self.restaurant_file = os.path.join(data_dir, "restaurants.json")
        self.reservation_file = os.path.join(data_dir, "reservations.json")
        
        # Create directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize empty data if files don't exist
        if not os.path.exists(self.restaurant_file):
            self._save_json(self.restaurant_file, [])
        
        if not os.path.exists(self.reservation_file):
            self._save_json(self.reservation_file, [])
    
    def _load_json(self, filepath):
        """Load data from JSON file"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_json(self, filepath, data):
        """Save data to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    # Restaurant methods
    def get_all_restaurants(self):
        """Get all restaurants"""
        data = self._load_json(self.restaurant_file)
        return [Restaurant.from_dict(r) for r in data]
    
    def get_restaurant(self, restaurant_id):
        """Get restaurant by ID"""
        restaurants = self.get_all_restaurants()
        for restaurant in restaurants:
            if restaurant.id == restaurant_id:
                return restaurant
        return None
    
    def add_restaurant(self, restaurant):
        """Add or update a restaurant"""
        restaurants = self.get_all_restaurants()
        
        # Update if exists, otherwise add
        for i, r in enumerate(restaurants):
            if r.id == restaurant.id:
                restaurants[i] = restaurant
                break
        else:
            restaurants.append(restaurant)
        
        # Save changes
        data = [r.to_dict() for r in restaurants]
        self._save_json(self.restaurant_file, data)
    
    def add_restaurants(self, restaurants):
        """Add multiple restaurants"""
        for restaurant in restaurants:
            self.add_restaurant(restaurant)
    
    # Reservation methods
    def get_all_reservations(self):
        """Get all reservations"""
        data = self._load_json(self.reservation_file)
        return [Reservation.from_dict(r) for r in data]
    
    def get_reservation(self, reservation_id):
        """Get reservation by ID"""
        reservations = self.get_all_reservations()
        for reservation in reservations:
            if reservation.id == reservation_id:
                return reservation
        return None
    
    def get_reservations_by_date(self, restaurant_id, date):
        """Get reservations for a restaurant on a specific date"""
        reservations = self.get_all_reservations()
        return [r for r in reservations 
                if r.restaurant_id == restaurant_id and 
                   r.date == date and 
                   r.status == "confirmed"]
    
    def add_reservation(self, reservation):
        """Add or update a reservation"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.reservation_file), exist_ok=True)
        
            # Get current reservations
            current_reservations = self.get_all_reservations()
            
            # Add new reservation to the list
            found = False
            for i, r in enumerate(current_reservations):
                if r.id == reservation.id:
                    current_reservations[i] = reservation
                    found = True
                    break
            
            if not found:
                current_reservations.append(reservation)
            
            # Convert to dictionaries
            reservation_dicts = [r.to_dict() for r in current_reservations]
            
            # Save to file
            with open(self.reservation_file, 'w') as f:
                json.dump(reservation_dicts, f, indent=2)
            
            print(f"Saved {len(current_reservations)} reservations to {self.reservation_file}")
            return True
        except Exception as e:
            import traceback
            print(f"Error saving reservation: {e}")
            print(traceback.format_exc())
            return False
    
    def get_customer_reservations(self, customer_name, email=None):
        """Get reservations for a customer"""
        reservations = self.get_all_reservations()
        customer_reservations = []
        
        for r in reservations:
            if r.customer_name.lower() == customer_name.lower():
                if email is None or r.email == email:
                    customer_reservations.append(r)
        
        return customer_reservations