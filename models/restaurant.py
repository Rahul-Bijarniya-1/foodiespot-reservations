class Restaurant:
    """Simple restaurant model"""
    
    def __init__(self, id, name, cuisine, location, capacity, 
                 price_range, rating, description, hours=None):
        self.id = id
        self.name = name
        self.cuisine = cuisine
        self.location = location
        self.capacity = capacity  # Maximum party size
        self.price_range = price_range  # 1-4 ($-$$$$)
        self.rating = rating  # 1-5 stars
        self.description = description
        self.hours = hours or {
            "weekday": {"open": "11:00", "close": "22:00"},
            "weekend": {"open": "10:00", "close": "23:00"}
        }
    
    def to_dict(self):
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "name": self.name,
            "cuisine": self.cuisine,
            "location": self.location,
            "capacity": self.capacity,
            "price_range": self.price_range,
            "rating": self.rating,
            "description": self.description,
            "hours": self.hours
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        return cls(
            id=data["id"],
            name=data["name"],
            cuisine=data["cuisine"],
            location=data["location"],
            capacity=data["capacity"],
            price_range=data["price_range"],
            rating=data["rating"],
            description=data["description"],
            hours=data.get("hours")
        )
    
    def is_open_at(self, day_type, time):
        """Check if restaurant is open at a specific time"""
        day_hours = self.hours.get(day_type, self.hours["weekday"])
        return day_hours["open"] <= time <= day_hours["close"]