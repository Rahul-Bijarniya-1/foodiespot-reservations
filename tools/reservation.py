import uuid
from datetime import datetime
from models.reservation import Reservation
from tools.availability import check_availability

def make_reservation(data_store, restaurant_id, customer_name, date, time, 
                     party_size, email=None, phone=None):
    """
    Make a new reservation
    
    Args:
        data_store: Data storage instance
        restaurant_id: ID of the restaurant
        customer_name: Name of the customer
        date: Date of reservation (YYYY-MM-DD)
        time: Time of reservation (HH:MM)
        party_size: Size of the party
        email: Customer email
        phone: Customer phone
    
    Returns:
        (success, reservation_or_error) - Tuple with success flag and either
        the reservation object or error message
    """
    # Validate restaurant exists
    restaurant = data_store.get_restaurant(restaurant_id)
    if not restaurant:
        return False, "Restaurant not found"
    
    # Validate party size
    if party_size > restaurant.capacity:
        return False, f"Party size exceeds restaurant capacity ({restaurant.capacity})"
    
    # Validate inputs
    valid, message = validate_reservation_data(
        data_store, restaurant_id, date, time, party_size
    )
    
    if not valid:
        return False, message


    # Check if the time slot is available
    available_slots = check_availability(
        data_store=data_store,
        restaurant_id=restaurant_id,
        date=date,
        time=time,
        party_size=party_size
    )
    
    if time not in available_slots:
        return False, "The requested time slot is not available"
    
    # Create a new reservation
    reservation_id = f"res_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    reservation = Reservation(
        id=reservation_id,
        restaurant_id=restaurant_id,
        customer_name=customer_name,
        date=date,
        time=time,
        party_size=party_size,
        email=email,
        phone=phone
    )

    # Debug output
    print(f"Creating reservation with ID: {reservation_id}")
    print(f"Reservation details: {reservation.to_dict()}")
    
    # Save the reservation
    save_success = data_store.add_reservation(reservation)
    
    if save_success:
        print(f"✅ Successfully saved reservation to data store")
        # Verify the file exists after saving
        import os
        if os.path.exists(data_store.reservation_file):
            print(f"✅ Reservation file exists at: {data_store.reservation_file}")
            print(f"✅ File size: {os.path.getsize(data_store.reservation_file)} bytes")
        else:
            print(f"❌ Reservation file does not exist at: {data_store.reservation_file}")
    else:
        print(f"❌ Failed to save reservation")
    
    return save_success, reservation

def get_reservation(data_store, reservation_id):
    """
    Get a reservation by ID
    
    Args:
        data_store: Data storage instance
        reservation_id: ID of the reservation
    
    Returns:
        Reservation object or None if not found
    """
    return data_store.get_reservation(reservation_id)

def update_reservation(data_store, reservation_id, updates):
    """
    Update an existing reservation
    
    Args:
        data_store: Data storage instance
        reservation_id: ID of the reservation to update
        updates: Dictionary of fields to update
    
    Returns:
        (success, reservation_or_error) - Tuple with success flag and either
        the updated reservation object or error message
    """
    # Get the reservation
    reservation = data_store.get_reservation(reservation_id)
    if not reservation:
        return False, "Reservation not found"
    
    # Cannot modify cancelled reservations
    if reservation.status == "cancelled":
        return False, "Cannot modify a cancelled reservation"
    
    # Check if we're changing date or time
    new_date = updates.get('date', reservation.date)
    new_time = updates.get('time', reservation.time)
    new_party_size = updates.get('party_size', reservation.party_size)
    
    # If date, time, or party size is changing, check availability
    if (new_date != reservation.date or 
        new_time != reservation.time or 
        new_party_size != reservation.party_size):
        
        available_slots = check_availability(
            data_store=data_store,
            restaurant_id=reservation.restaurant_id,
            date=new_date,
            time=new_time,
            party_size=new_party_size
        )
        
        if new_time not in available_slots:
            return False, "The requested time slot is not available"
    
    # Apply updates
    if 'date' in updates:
        reservation.date = updates['date']
    if 'time' in updates:
        reservation.time = updates['time']
    if 'party_size' in updates:
        reservation.party_size = updates['party_size']
    if 'status' in updates:
        reservation.status = updates['status']
    if 'email' in updates:
        reservation.email = updates['email']
    if 'phone' in updates:
        reservation.phone = updates['phone']
    
    # Save updates
    data_store.add_reservation(reservation)
    
    return True, reservation

def cancel_reservation(data_store, reservation_id):
    """
    Cancel an existing reservation
    
    Args:
        data_store: Data storage instance
        reservation_id: ID of the reservation to cancel
    
    Returns:
        (success, message) - Tuple with success flag and message
    """
    # Get the reservation
    reservation = data_store.get_reservation(reservation_id)
    if not reservation:
        return False, "Reservation not found"
    
    # Check if already cancelled
    if reservation.status == "cancelled":
        return False, "Reservation is already cancelled"
    
    # Cancel the reservation
    reservation.status = "cancelled"
    data_store.add_reservation(reservation)
    
    return True, "Reservation successfully cancelled"

def validate_reservation_data(data_store, restaurant_id, date, time, party_size):
    """
    Validate reservation data before sending to the LLM
    
    Args:
        data_store: Data storage instance
        restaurant_id: ID of the restaurant
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format
        party_size: Size of the party
    
    Returns:
        (valid, message) - Tuple with validation status and message
    """
    # Check if restaurant exists
    restaurant = data_store.get_restaurant(restaurant_id)
    if not restaurant:
        return False, f"Restaurant with ID '{restaurant_id}' does not exist."
    
    # Check date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return False, f"Invalid date format. Please use YYYY-MM-DD format."
    
    # Check time format
    try:
        hours, minutes = time.split(":")
        if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
            return False, f"Invalid time: {time}. Please use HH:MM format (24-hour)."
    except (ValueError, IndexError):
        return False, f"Invalid time format. Please use HH:MM format."
    
    # Check party size
    if not isinstance(party_size, int) or party_size <= 0:
        return False, f"Invalid party size: {party_size}. Must be a positive number."
    
    # Check if party size exceeds restaurant capacity
    if party_size > restaurant.capacity:
        return False, f"Party size {party_size} exceeds restaurant capacity of {restaurant.capacity}."
    
    return True, "Validation successful"