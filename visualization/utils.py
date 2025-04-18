# visualization/utils.py
def format_percentage(value, total, decimals=1):
    """Format a percentage with the given number of decimal places"""
    if total == 0:
        return "0.0%"
    return f"{value / total * 100:.{decimals}f}%"


def get_korean_time():
    """Get the current time in Korean timezone"""
    try:
        from datetime import datetime
        import pytz

        korean_tz = pytz.timezone("Asia/Seoul")
        return datetime.now(korean_tz).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        # Fallback to simple datetime if pytz is not available
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
