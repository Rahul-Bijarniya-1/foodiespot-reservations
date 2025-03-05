from datetime import datetime

class Reservation:
    """Simple reservation model"""
    
    def __init__(self, id, restaurant_id, customer_name, date, time, 
                 party_size, email=None, phone=None, status="confirmed"):
        self.id = id
        self.restaurant_id = restaurant_id
        self.customer_name = customer_name
        self.date = date  # YYYY-MM-DD
        self.time = time  # HH:MM
        self.party_size = party_size
        self.email = email
        self.phone = phone
        self.status = status  # confirmed, cancelled
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def to_dict(self):
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "restaurant_id": self.restaurant_id,
            "customer_name": self.customer_name,
            "date": self.date,
            "time": self.time,
            "party_size": self.party_size,
            "email": self.email,
            "phone": self.phone,
            "status": self.status,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        reservation = cls(
            id=data["id"],
            restaurant_id=data["restaurant_id"],
            customer_name=data["customer_name"],
            date=data["date"],
            time=data["time"],
            party_size=data["party_size"],
            email=data.get("email"),
            phone=data.get("phone"),
            status=data.get("status", "confirmed")
        )
        reservation.created_at = data.get("created_at", reservation.created_at)
        return reservation
    
    def cancel(self):
        """Cancel the reservation"""
        self.status = "cancelled"
        return self