from datetime import datetime

def check_availability(data_store, restaurant_id, date, time=None, party_size=None):
    """
    Check available time slots for a restaurant on a specific date
    
    Args:
        data_store: Data storage instance
        restaurant_id: ID of the restaurant
        date: Date to check (YYYY-MM-DD format)
        time: Optional specific time to check (HH:MM format)
        party_size: Size of the party
    
    Returns:
        List of available time slots (HH:MM format)
    """
    # Get restaurant
    restaurant = data_store.get_restaurant(restaurant_id)
    if not restaurant:
        return []
    
    # Check party size
    if party_size and party_size > restaurant.capacity:
        return []
    
    # Get existing reservations for this date
    existing_reservations = data_store.get_reservations_by_date(restaurant_id, date)
    booked_times = [r.time for r in existing_reservations]
    
    # Determine day type (weekday/weekend)
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        day_type = "weekend" if date_obj.weekday() >= 5 else "weekday"
    except ValueError:
        return []  # Invalid date format
    
    # Get restaurant hours for this day
    hours = restaurant.hours.get(day_type)
    if not hours:
        return []
    
    # Generate available time slots (every 30 minutes from opening to closing)
    open_hour, open_minute = map(int, hours["open"].split(":"))
    close_hour, close_minute = map(int, hours["close"].split(":"))
    
    # Generate all slots
    available_slots = []
    current_hour = open_hour
    current_minute = open_minute
    
    while current_hour < close_hour or (current_hour == close_hour and current_minute < close_minute):
        # Format time slot
        time_slot = f"{current_hour:02d}:{current_minute:02d}"
        
        # Check if this slot is already booked
        if time_slot not in booked_times:
            available_slots.append(time_slot)
        
        # Advance by 30 minutes
        current_minute += 30
        if current_minute >= 60:
            current_minute = 0
            current_hour += 1
    
    # If specific time is provided, filter slots near that time
    if time:
        try:
            requested_hour, requested_minute = map(int, time.split(":"))
            requested_minutes = requested_hour * 60 + requested_minute
            
            # Filter to slots within 2 hours of requested time
            filtered_slots = []
            for slot in available_slots:
                slot_hour, slot_minute = map(int, slot.split(":"))
                slot_minutes = slot_hour * 60 + slot_minute
                
                if abs(slot_minutes - requested_minutes) <= 120:  # 2 hours
                    filtered_slots.append(slot)
            
            available_slots = filtered_slots
        except ValueError:
            pass  # Invalid time format, use all slots
    
    return available_slots

def suggest_alternative_times(data_store, restaurant_id, date, time, party_size, num_alternatives=3):
    """
    Suggest alternative times if preferred time is not available
    
    Args:
        data_store: Data storage instance
        restaurant_id: ID of the restaurant
        date: Preferred date (YYYY-MM-DD format)
        time: Preferred time (HH:MM format)
        party_size: Size of the party
        num_alternatives: Number of alternatives to suggest
    
    Returns:
        List of alternative time suggestions
    """
    available_slots = check_availability(
        data_store=data_store,
        restaurant_id=restaurant_id,
        date=date,
        party_size=party_size
    )
    
    if not available_slots:
        return []
    
    # If preferred time is available, it should be first
    if time in available_slots:
        available_slots.remove(time)
        alternatives = [time]
        remaining_slots = num_alternatives - 1
    else:
        alternatives = []
        remaining_slots = num_alternatives
    
    # Sort other slots by proximity to preferred time
    try:
        preferred_hour, preferred_minute = map(int, time.split(":"))
        preferred_minutes = preferred_hour * 60 + preferred_minute
        
        scored_slots = []
        for slot in available_slots:
            slot_hour, slot_minute = map(int, slot.split(":"))
            slot_minutes = slot_hour * 60 + slot_minute
            diff = abs(slot_minutes - preferred_minutes)
            scored_slots.append((slot, diff))
        
        scored_slots.sort(key=lambda x: x[1])
        alternatives.extend([slot for slot, _ in scored_slots[:remaining_slots]])
    except ValueError:
        # If time parsing fails, just return some available slots
        alternatives.extend(available_slots[:remaining_slots])
    
    return alternatives