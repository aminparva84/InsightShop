"""Seasonal Events and Holiday Detection - Based on Current Date."""

from datetime import datetime, date, timedelta
import calendar

# Get current date
def get_current_date():
    """Get the current date."""
    return date.today()

def get_current_datetime():
    """Get the current date and time."""
    return datetime.now()

# Season detection
def get_current_season(current_date=None):
    """
    Determine the current season based on date.
    Returns: 'spring', 'summer', 'fall', 'winter'
    """
    if current_date is None:
        current_date = get_current_date()
    
    month = current_date.month
    day = current_date.day
    
    # Northern Hemisphere seasons
    if month in [12, 1, 2]:
        return 'winter'
    elif month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    elif month in [9, 10, 11]:
        return 'fall'
    
    return 'spring'  # Default

# Major holidays and cultural events
HOLIDAYS = {
    # Winter Holidays
    'new_years': {'month': 1, 'day': 1, 'season': 'winter', 'type': 'celebration'},
    'valentines_day': {'month': 2, 'day': 14, 'season': 'winter', 'type': 'romantic'},
    'st_patricks_day': {'month': 3, 'day': 17, 'season': 'spring', 'type': 'cultural'},
    'easter': {'month': None, 'day': None, 'season': 'spring', 'type': 'religious', 'calculated': True},
    
    # Spring Holidays
    'mothers_day': {'month': 5, 'day': None, 'season': 'spring', 'type': 'family', 'calculated': True},  # Second Sunday in May
    'memorial_day': {'month': 5, 'day': None, 'season': 'spring', 'type': 'patriotic', 'calculated': True},  # Last Monday in May
    
    # Summer Holidays
    'fathers_day': {'month': 6, 'day': None, 'season': 'summer', 'type': 'family', 'calculated': True},  # Third Sunday in June
    'independence_day': {'month': 7, 'day': 4, 'season': 'summer', 'type': 'patriotic'},
    'labor_day': {'month': 9, 'day': None, 'season': 'fall', 'type': 'patriotic', 'calculated': True},  # First Monday in September
    
    # Fall Holidays
    'halloween': {'month': 10, 'day': 31, 'season': 'fall', 'type': 'celebration'},
    'thanksgiving': {'month': 11, 'day': None, 'season': 'fall', 'type': 'family', 'calculated': True},  # Fourth Thursday in November
    'cyber_monday': {'month': 11, 'day': None, 'season': 'fall', 'type': 'shopping', 'calculated': True},  # Monday after Thanksgiving
    
    # Winter Holidays
    'hanukkah': {'month': None, 'day': None, 'season': 'winter', 'type': 'religious', 'calculated': True},  # Varies
    'christmas': {'month': 12, 'day': 25, 'season': 'winter', 'type': 'religious'},
    'kwanzaa': {'month': 12, 'day': 26, 'season': 'winter', 'type': 'cultural', 'duration': 7},
    'new_years_eve': {'month': 12, 'day': 31, 'season': 'winter', 'type': 'celebration'},
}

# Cultural events and observances
CULTURAL_EVENTS = {
    'black_history_month': {'month': 2, 'season': 'winter', 'type': 'cultural', 'duration': 28},
    'womens_history_month': {'month': 3, 'season': 'spring', 'type': 'cultural', 'duration': 31},
    'pride_month': {'month': 6, 'season': 'summer', 'type': 'cultural', 'duration': 30},
    'hispanic_heritage_month': {'month': 9, 'season': 'fall', 'type': 'cultural', 'duration': 30},  # Sep 15 - Oct 15
}

def calculate_easter(year):
    """Calculate Easter date for a given year (simplified algorithm)."""
    # Simplified Easter calculation (works for most years)
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)

def get_mothers_day(year):
    """Get Mother's Day (second Sunday in May)."""
    # Find second Sunday in May
    may_first = date(year, 5, 1)
    # Get day of week (0 = Monday, 6 = Sunday)
    first_day = may_first.weekday()
    # Calculate days to first Sunday
    days_to_sunday = (6 - first_day) % 7
    if days_to_sunday == 0:
        days_to_sunday = 7
    # Second Sunday is 7 days after first
    second_sunday = may_first.replace(day=1 + days_to_sunday + 7)
    return second_sunday

def get_fathers_day(year):
    """Get Father's Day (third Sunday in June)."""
    june_first = date(year, 6, 1)
    first_day = june_first.weekday()
    days_to_sunday = (6 - first_day) % 7
    if days_to_sunday == 0:
        days_to_sunday = 7
    third_sunday = june_first.replace(day=1 + days_to_sunday + 14)
    return third_sunday

def get_memorial_day(year):
    """Get Memorial Day (last Monday in May)."""
    may_last = date(year, 5, 31)
    # Find last Monday
    days_back = may_last.weekday()
    last_monday = may_last.replace(day=31 - days_back)
    return last_monday

def get_labor_day(year):
    """Get Labor Day (first Monday in September)."""
    sep_first = date(year, 9, 1)
    first_day = sep_first.weekday()
    days_to_monday = (7 - first_day) % 7
    if days_to_monday == 0:
        days_to_monday = 7
    first_monday = sep_first.replace(day=1 + days_to_monday - 1)
    return first_monday

def get_thanksgiving(year):
    """Get Thanksgiving (fourth Thursday in November)."""
    nov_first = date(year, 11, 1)
    first_day = nov_first.weekday()
    # Calculate days to first Thursday
    days_to_thursday = (3 - first_day) % 7
    if days_to_thursday == 0 and first_day != 3:
        days_to_thursday = 7
    # Fourth Thursday is 21 days after first
    fourth_thursday = nov_first.replace(day=1 + days_to_thursday + 21)
    return fourth_thursday

def get_cyber_monday(year):
    """Get Cyber Monday (Monday after Thanksgiving)."""
    thanksgiving = get_thanksgiving(year)
    # Cyber Monday is the Monday after Thanksgiving
    days_after = (7 - thanksgiving.weekday()) % 7
    if days_after == 0:
        days_after = 7
    cyber_monday = thanksgiving + timedelta(days=days_after)
    return cyber_monday

def get_upcoming_holidays(current_date=None, days_ahead=30):
    """Get upcoming holidays within the next N days."""
    if current_date is None:
        current_date = get_current_date()
    
    upcoming = []
    year = current_date.year
    
    # Calculate variable holidays
    easter = calculate_easter(year)
    mothers_day = get_mothers_day(year)
    fathers_day = get_fathers_day(year)
    memorial_day = get_memorial_day(year)
    labor_day = get_labor_day(year)
    thanksgiving = get_thanksgiving(year)
    cyber_monday = get_cyber_monday(year)
    
    # Check fixed holidays
    for holiday_name, holiday_info in HOLIDAYS.items():
        if holiday_info.get('calculated'):
            # Use calculated date
            if holiday_name == 'easter':
                holiday_date = easter
            elif holiday_name == 'mothers_day':
                holiday_date = mothers_day
            elif holiday_name == 'fathers_day':
                holiday_date = fathers_day
            elif holiday_name == 'memorial_day':
                holiday_date = memorial_day
            elif holiday_name == 'labor_day':
                holiday_date = labor_day
            elif holiday_name == 'thanksgiving':
                holiday_date = thanksgiving
            elif holiday_name == 'cyber_monday':
                holiday_date = cyber_monday
            else:
                continue
        else:
            holiday_date = date(year, holiday_info['month'], holiday_info['day'])
        
        # Check if holiday is upcoming
        days_until = (holiday_date - current_date).days
        if 0 <= days_until <= days_ahead:
            upcoming.append({
                'name': holiday_name,
                'date': holiday_date,
                'days_until': days_until,
                'season': holiday_info['season'],
                'type': holiday_info['type']
            })
    
    # Check cultural events
    for event_name, event_info in CULTURAL_EVENTS.items():
        event_month = event_info['month']
        if current_date.month == event_month:
            upcoming.append({
                'name': event_name,
                'date': current_date,  # Current month
                'days_until': 0,
                'season': event_info['season'],
                'type': event_info['type'],
                'is_month_long': True
            })
    
    return sorted(upcoming, key=lambda x: x['days_until'])

def get_current_holidays_and_events(current_date=None):
    """Get holidays and events happening today or this month."""
    if current_date is None:
        current_date = get_current_date()
    
    current = []
    year = current_date.year
    month = current_date.month
    day = current_date.day
    
    # Calculate variable holidays for this year
    easter = calculate_easter(year)
    mothers_day = get_mothers_day(year)
    fathers_day = get_fathers_day(year)
    memorial_day = get_memorial_day(year)
    labor_day = get_labor_day(year)
    thanksgiving = get_thanksgiving(year)
    cyber_monday = get_cyber_monday(year)
    
    # Check fixed holidays
    for holiday_name, holiday_info in HOLIDAYS.items():
        if holiday_info.get('calculated'):
            if holiday_name == 'easter':
                holiday_date = easter
            elif holiday_name == 'mothers_day':
                holiday_date = mothers_day
            elif holiday_name == 'fathers_day':
                holiday_date = fathers_day
            elif holiday_name == 'memorial_day':
                holiday_date = memorial_day
            elif holiday_name == 'labor_day':
                holiday_date = labor_day
            elif holiday_name == 'thanksgiving':
                holiday_date = thanksgiving
            elif holiday_name == 'cyber_monday':
                holiday_date = cyber_monday
            else:
                continue
        else:
            holiday_date = date(year, holiday_info['month'], holiday_info['day'])
        
        if holiday_date == current_date:
            current.append({
                'name': holiday_name,
                'date': holiday_date,
                'season': holiday_info['season'],
                'type': holiday_info['type']
            })
    
    # Check cultural events (month-long)
    for event_name, event_info in CULTURAL_EVENTS.items():
        if event_info['month'] == month:
            current.append({
                'name': event_name,
                'date': current_date,
                'season': event_info['season'],
                'type': event_info['type'],
                'is_month_long': True
            })
    
    return current

def get_seasonal_recommendations(current_date=None):
    """Get seasonal fashion recommendations based on current date."""
    if current_date is None:
        current_date = get_current_date()
    
    season = get_current_season(current_date)
    upcoming_holidays = get_upcoming_holidays(current_date, days_ahead=60)
    current_events = get_current_holidays_and_events(current_date)
    
    recommendations = {
        'season': season,
        'current_date': current_date.strftime('%B %d, %Y'),
        'seasonal_items': [],
        'holiday_items': [],
        'occasion_items': []
    }
    
    # Seasonal recommendations
    seasonal_items = {
        'spring': ['Light jackets', 'Pastel colors', 'Floral prints', 'Lightweight fabrics', 'Rain boots', 'Cardigans'],
        'summer': ['Sundresses', 'Shorts', 'Tank tops', 'Sandals', 'Swimwear', 'Light colors', 'Breathable fabrics'],
        'fall': ['Sweaters', 'Boots', 'Jackets', 'Scarves', 'Warm colors', 'Layering pieces', 'Jeans'],
        'winter': ['Coats', 'Wool sweaters', 'Boots', 'Gloves', 'Hats', 'Warm layers', 'Dark colors']
    }
    
    recommendations['seasonal_items'] = seasonal_items.get(season, [])
    
    # Holiday-specific recommendations
    for holiday in upcoming_holidays[:3]:  # Top 3 upcoming holidays
        holiday_name = holiday['name']
        holiday_type = holiday['type']
        
        if holiday_type == 'romantic':
            recommendations['holiday_items'].append({
                'holiday': holiday_name,
                'suggestions': ['Elegant dresses', 'Formal wear', 'Jewelry', 'Heels', 'Romantic colors (red, pink)']
            })
        elif holiday_type == 'celebration':
            recommendations['holiday_items'].append({
                'holiday': holiday_name,
                'suggestions': ['Party dresses', 'Festive colors', 'Accessories', 'Formal wear']
            })
        elif holiday_type == 'family':
            recommendations['holiday_items'].append({
                'holiday': holiday_name,
                'suggestions': ['Comfortable casual wear', 'Family-friendly outfits', 'Layered clothing']
            })
        elif holiday_type == 'patriotic':
            recommendations['holiday_items'].append({
                'holiday': holiday_name,
                'suggestions': ['Red, white, and blue', 'Casual patriotic wear', 'Outdoor-friendly clothing']
            })
    
    # Current events
    for event in current_events:
        if event.get('is_month_long'):
            recommendations['occasion_items'].append({
                'event': event['name'],
                'suggestions': ['Cultural celebration colors', 'Traditional patterns', 'Festive accessories']
            })
    
    return recommendations

def get_seasonal_context_text(current_date=None):
    """Get a formatted text description of current seasonal context for AI."""
    if current_date is None:
        current_date = get_current_date()
    
    season = get_current_season(current_date)
    upcoming = get_upcoming_holidays(current_date, days_ahead=30)
    current_events = get_current_holidays_and_events(current_date)
    recommendations = get_seasonal_recommendations(current_date)
    
    context = f"Current Date: {current_date.strftime('%B %d, %Y')}\n"
    context += f"Current Season: {season.capitalize()}\n\n"
    
    if current_events:
        context += "Current Events/Holidays:\n"
        for event in current_events:
            event_name = event['name'].replace('_', ' ').title()
            context += f"- {event_name} (Today)\n"
        context += "\n"
    
    if upcoming:
        context += "Upcoming Holidays (next 30 days):\n"
        for holiday in upcoming[:5]:  # Top 5
            holiday_name = holiday['name'].replace('_', ' ').title()
            days = holiday['days_until']
            if days == 0:
                context += f"- {holiday_name} (Today)\n"
            elif days == 1:
                context += f"- {holiday_name} (Tomorrow)\n"
            else:
                context += f"- {holiday_name} (in {days} days)\n"
        context += "\n"
    
    context += f"Seasonal Recommendations for {season.capitalize()}:\n"
    for item in recommendations['seasonal_items']:
        context += f"- {item}\n"
    
    if recommendations['holiday_items']:
        context += "\nHoliday-Specific Recommendations:\n"
        for holiday_info in recommendations['holiday_items']:
            holiday_name = holiday_info['holiday'].replace('_', ' ').title()
            context += f"{holiday_name}:\n"
            for suggestion in holiday_info['suggestions']:
                context += f"  - {suggestion}\n"
    
    return context

