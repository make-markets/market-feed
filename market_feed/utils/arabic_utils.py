import re
from datetime import datetime

from langdetect import detect


def is_arabic(text: str) -> bool:
    """Detect if the given text is in Arabic."""
    try:
        return detect(text) == "ar"
    except:
        return False


def translate_arabic_numbers(text: str) -> str:
    """Translate Arabic numerals to English numerals."""
    arabic_numbers = {
        "٠": "0",
        "١": "1",
        "٢": "2",
        "٣": "3",
        "٤": "4",
        "٥": "5",
        "٦": "6",
        "٧": "7",
        "٨": "8",
        "٩": "9",
    }
    for arabic, english in arabic_numbers.items():
        text = text.replace(arabic, english)
    return text


def translate_arabic_time_units(text: str) -> str:
    """Translate Arabic time units to English."""
    arabic_to_english = {
        "ثانية": "second",
        "ثانيتين": "seconds",
        "ثواني": "seconds",
        "دقيقة": "minute",
        "دقيقتين": "minutes",
        "دقائق": "minutes",
        "ساعة": "hour",
        "ساعتين": "hours",
        "ساعات": "hours",
        "يوم": "day",
        "يومين": "days",
        "أيام": "days",
        "أسبوع": "week",
        "أسبوعين": "weeks",
        "أسابيع": "weeks",
        "شهر": "month",
        "شهرين": "months",
        "أشهر": "months",
        "سنة": "year",
        "سنتين": "years",
        "سنوات": "years",
        "قبل": "ago",
    }
    for arabic, english in arabic_to_english.items():
        text = text.replace(arabic, english)
    return text


def translate_arabic_months(text: str) -> str:
    """Translate Arabic month names to English."""
    arabic_months = {
        "يناير": "January",
        "فبراير": "February",
        "مارس": "March",
        "أبريل": "April",
        "مايو": "May",
        "يونيو": "June",
        "يوليو": "July",
        "أغسطس": "August",
        "سبتمبر": "September",
        "أكتوبر": "October",
        "نوفمبر": "November",
        "ديسمبر": "December",
    }
    for arabic, english in arabic_months.items():
        text = text.replace(arabic, english)
    return text


def parse_arabic_absolute_date(date_string: str) -> str:
    """Parse and translate an absolute Arabic date to English format."""
    # Translate Arabic numbers and month names
    date_string = translate_arabic_numbers(date_string)
    date_string = translate_arabic_months(date_string)

    # Define regex pattern for date formats like "4 December 2024" or "4 Dec 2024"
    pattern = r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})"
    match = re.search(pattern, date_string)

    if match:
        day, month, year = match.groups()
        # Convert to a standardized format
        try:
            date_obj = datetime.strptime(f"{day} {month} {year}", "%d %B %Y")
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            # If full month name fails, try with abbreviated month name
            try:
                date_obj = datetime.strptime(f"{day} {month} {year}", "%d %b %Y")
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                return date_string  # Return original string if parsing fails

    return date_string  # Return original string if no match found


def translate_arabic_date(date_string: str) -> str:
    """Translate an Arabic date string to English if it's in Arabic."""
    if is_arabic(date_string):
        # First, try to parse as an absolute date
        translated_date = parse_arabic_absolute_date(date_string)
        if translated_date != date_string:
            return translated_date

        # If not an absolute date, translate relative date terms
        date_string = translate_arabic_numbers(date_string)
        date_string = translate_arabic_time_units(date_string)
    return date_string
