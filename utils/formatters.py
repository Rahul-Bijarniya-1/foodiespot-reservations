def format_restaurant_list(restaurants):
    """Format a list of restaurants into user-friendly text"""
    if not restaurants:
        return "I couldn't find any restaurants matching your criteria."
    
    result = "Here are some restaurants that match your criteria:\n\n"
    for i, restaurant in enumerate(restaurants, 1):
        result += f"{i}. **{restaurant.name}** - {restaurant.cuisine}\n"
        result += f"   📍 {restaurant.location} | 💰 {'$' * restaurant.price_range} | ⭐ {restaurant.rating}\n"
        result += f"   {restaurant.description[:100]}...\n\n"
    
    return result

def format_restaurant_details(restaurant):
    """Format detailed information for a single restaurant"""
    if not restaurant:
        return "Restaurant details not found."
    
    # Format hours
    weekday_hours = f"{restaurant.hours['weekday']['open']} - {restaurant.hours['weekday']['close']}"
    weekend_hours = f"{restaurant.hours['weekend']['open']} - {restaurant.hours['weekend']['close']}"
    
    details = f"# {restaurant.name}\n\n"
    details += f"**Cuisine:** {restaurant.cuisine}\n"
    details += f"**Location:** {restaurant.location}\n"
    details += f"**Price Range:** {'$' * restaurant.price_range}\n"
    details += f"**Rating:** {restaurant.rating} stars\n"
    details += f"**Capacity:** {restaurant.capacity} guests\n\n"
    details += f"**Hours:**\n- Weekdays: {weekday_hours}\n- Weekends: {weekend_hours}\n\n"
    details += f"**Description:**\n{restaurant.description}\n"
    
    return details

def format_available_times(date, available_times):
    """Format available time slots"""
    if not available_times:
        return f"I'm sorry, there are no available time slots for {date}."
    
    result = f"Available time slots for {date}:\n\n"
    
    # Group times by hour for cleaner display
    hour_groups = {}
    for t in available_times:
        hour = int(t.split(':')[0])
        if hour not in hour_groups:
            hour_groups[hour] = []
        hour_groups[hour].append(t)
    
    for hour in sorted(hour_groups.keys()):
        # Format hour (e.g., "7 PM")
        hour_display = f"{hour if hour <= 12 else hour-12} {'AM' if hour < 12 else 'PM'}"
        
        # Format minutes (e.g., "7:00 PM, 7:30 PM")
        times_display = ", ".join([
            f"{int(t.split(':')[0]) if int(t.split(':')[0]) <= 12 else int(t.split(':')[0])-12}:{t.split(':')[1]} {'AM' if int(t.split(':')[0]) < 12 else 'PM'}"
            for t in sorted(hour_groups[hour])
        ])
        
        result += f"- {times_display}\n"
    
    return result

def format_reservation_confirmation(reservation, restaurant):
    """Format a reservation confirmation message"""
    return f"""
# Reservation Confirmed!

Your reservation at **{restaurant.name}** has been confirmed.

**Details:**
- **Date:** {reservation.date}
- **Time:** {format_time(reservation.time)}
- **Party Size:** {reservation.party_size} people
- **Reservation ID:** {reservation.id}

**Restaurant Information:**
- **Address:** {restaurant.location}
- **Cuisine:** {restaurant.cuisine}
- **Price Range:** {'$' * restaurant.price_range}

Thank you for choosing our service! If you need to modify or cancel your reservation, please use your reservation ID.
"""

def format_reservation_details(reservation, restaurant):
    """Format details of an existing reservation"""
    return f"""
# Reservation Details

**Reservation ID:** {reservation.id}
**Status:** {reservation.status.capitalize()}

**Restaurant:** {restaurant.name}
**Date:** {reservation.date}
**Time:** {format_time(reservation.time)}
**Party Size:** {reservation.party_size} people

**Customer Information:**
- **Name:** {reservation.customer_name}
{f"- **Email:** {reservation.email}" if reservation.email else ""}
{f"- **Phone:** {reservation.phone}" if reservation.phone else ""}

**Created at:** {reservation.created_at}
"""

def format_time(time_str):
    """Format time from 24-hour to 12-hour format"""
    try:
        hour, minute = map(int, time_str.split(':'))
        period = "AM" if hour < 12 else "PM"
        hour = hour if hour <= 12 else hour - 12
        hour = 12 if hour == 0 else hour  # 0:00 should be 12:00 AM
        return f"{hour}:{minute:02d} {period}"
    except:
        return time_str  # Return as-is if parsing fails