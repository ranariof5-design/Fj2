from datetime import datetime
import calendar

# Category color and icon mapping
CATEGORY_COLORS = {
    "Food": {
        "icon": "",
        "color": (1.0, 0.60, 0.20, 1),  # Orange
        "color_light": (1.0, 0.60, 0.20, 0.2)
    },
    "Transport": {
        "icon": "",
        "color": (0.60, 0.80, 1.0, 1),  # Light Blue
        "color_light": (0.60, 0.80, 1.0, 0.2)
    },
    "Entertainment": {
        "icon": "",
        "color": (0.95, 0.40, 0.70, 1),  # Pink
        "color_light": (0.95, 0.40, 0.70, 0.2)
    },
    "Shopping": {
        "icon": "",
        "color": (0.70, 0.40, 1.0, 1),  # Purple
        "color_light": (0.70, 0.40, 1.0, 0.2)
    },
    "Bills": {
        "icon": "",
        "color": (1.0, 0.80, 0.20, 1),  # Yellow
        "color_light": (1.0, 0.80, 0.20, 0.2)
    },
    "Health": {
        "icon": "",
        "color": (0.20, 0.90, 0.60, 1),  # Green
        "color_light": (0.20, 0.90, 0.60, 0.2)
    },
    "Education": {
        "icon": "",
        "color": (0.60, 0.70, 1.0, 1),  # Indigo
        "color_light": (0.60, 0.70, 1.0, 0.2)
    },
    "Other": {
        "icon": "",
        "color": (0.80, 0.80, 0.80, 1),  # Gray
        "color_light": (0.80, 0.80, 0.80, 0.2)
    }
}

def get_category_color(category):
    """Get color for a category"""
    return CATEGORY_COLORS.get(category, CATEGORY_COLORS["Other"])["color"]

def get_category_icon(category):
    """Get icon for a category"""
    return CATEGORY_COLORS.get(category, CATEGORY_COLORS["Other"])["icon"]
def format_amount(amount):
    """Format amount for display - show whole numbers without decimals"""
    if amount == int(amount):
        return f"₱{int(amount):,}"
    else:
        return f"₱{amount:,.2f}"
def parse_amount(amount_str):
    """Parse amount string to float"""
    try:
        cleaned = str(amount_str).replace("₱", "").replace(",", "").strip()
        return float(cleaned)
    except:
        raise ValueError("Invalid amount")

def validate_username(username):
    """Validate username"""
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters"
    if not username.replace("_", "").replace("-", "").isalnum():
        return False, "Username can only contain letters, numbers, _ and -"
    return True, ""

def validate_password(password):
    """Validate password"""
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, ""

def validate_email(email):
    """Basic email validation"""
    if not email:
        return True  # Email is optional
    if "@" not in email or "." not in email.split("@")[1]:
        return False
    return True

def get_current_date():
    """Get current date as YYYY-MM-DD"""
    return datetime.now().strftime("%Y-%m-%d")

def get_year_range(current_year, years_back=5, years_forward=2):
    """Get list of years"""
    return [str(y) for y in range(current_year - years_back, current_year + years_forward + 1)]

def get_month_list():
    """Get list of month names"""
    return [calendar.month_name[i] for i in range(1, 13)]

def get_month_number(month_name):
    """Get month number from name"""
    months = get_month_list()
    try:
        return months.index(month_name) + 1
    except:
        return 1