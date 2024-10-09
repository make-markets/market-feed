import pytest

from market_feed.utils.arabic_utils import (
    is_arabic,
    parse_arabic_absolute_date,
    translate_arabic_date,
    translate_arabic_numbers,
    translate_arabic_time_units,
)


def test_is_arabic():
    assert is_arabic("مرحبا") == True
    assert is_arabic("Hello") == False
    assert is_arabic("١٢٣") == True
    assert is_arabic("123") == False


def test_translate_arabic_numbers():
    assert translate_arabic_numbers("١٢٣") == "123"
    assert translate_arabic_numbers("٠٩٨٧٦٥٤٣٢١") == "0987654321"
    assert translate_arabic_numbers("مرحبا ٣ عالم") == "مرحبا 3 عالم"


def test_translate_arabic_time_units():
    assert translate_arabic_time_units("قبل ساعتين") == "ago hours"
    assert translate_arabic_time_units("قبل ٣ أيام") == "ago 3 days"
    assert translate_arabic_time_units("قبل سنة") == "ago year"


def test_translate_arabic_date():
    assert translate_arabic_date("قبل ٣ ساعات") == "ago 3 hours"
    assert translate_arabic_date("قبل ٢ أسابيع") == "ago 2 weeks"
    assert translate_arabic_date("قبل ١٢ يوم") == "ago 12 day"
    assert translate_arabic_date("قبل ساعتين") == "ago hours"
    assert translate_arabic_date("2 hours ago") == "2 hours ago"
    assert translate_arabic_date("vor 2 Stunden") == "vor 2 Stunden"


def test_parse_arabic_absolute_date():
    assert parse_arabic_absolute_date("٤ ديسمبر ٢٠٢٤") == "2024-12-04"
    assert parse_arabic_absolute_date("١٥ يناير ٢٠٢٣") == "2023-01-15"
    assert parse_arabic_absolute_date("٢٨ فبراير ٢٠٢٥") == "2025-02-28"


def test_translate_arabic_date_with_absolute_dates():
    assert translate_arabic_date("٤ ديسمبر ٢٠٢٤") == "2024-12-04"
    assert translate_arabic_date("١٥ يناير ٢٠٢٣") == "2023-01-15"
    assert translate_arabic_date("٢٨ فبراير ٢٠٢٥") == "2025-02-28"
    assert translate_arabic_date("4 December 2024") == "4 December 2024"
