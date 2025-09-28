"""
String matching utilities for date and time patterns.

This module provides functions to validate various date and time string formats,
commonly used for parsing folder names and validating date-based structures.

The functions support different levels of granularity from years to full datetime
strings with customizable separators.

Example:
    >>> is_year("2023")
    True
    >>> is_year_month("2023-12")
    True
    >>> is_time("14:30:45")
    True
"""


def is_year(string):
    """
    Check if a string represents a valid 4-digit year.
    
    Args:
        string (str): The string to validate
        
    Returns:
        bool: True if the string is exactly 4 digits, False otherwise
        
    Examples:
        >>> is_year("2023")
        True
        >>> is_year("23")
        False
        >>> is_year("202a")
        False
    """
    return string.isdigit() and len(string) == 4


def is_year_2000s(string):
    """
    Check if a string represents a valid year in the 2000s (2000-2099).
    
    Args:
        string (str): The string to validate
        
    Returns:
        bool: True if the string represents a year between 2000-2099, False otherwise
        
    Examples:
        >>> is_year_2000s("2023")
        True
        >>> is_year_2000s("1999")
        False
        >>> is_year_2000s("2100")
        False
    """
    return is_year(string) and 2000 <= int(string) < 2100


def is_year_month(string, sep: str = "-"):
    """
    Check if a string represents a valid year-month format.
    
    Validates strings in the format YYYY{sep}MM where the year is 4 digits
    and the month is 1-12.
    
    Args:
        string (str): The string to validate
        sep (str): The separator between year and month (default: "-")
        
    Returns:
        bool: True if the string matches YYYY{sep}MM format with valid values
        
    Examples:
        >>> is_year_month("2023-12")
        True
        >>> is_year_month("2023-13")  # Invalid month
        False
        >>> is_year_month("2023/12", sep="/")
        True
    """
    parts = string.split(sep)
    # only 1 sep
    if len(parts) != 2:
        return False

    return (
        len(parts) == 2
        and is_year(parts[0])
        and parts[1].isdigit()
        and 1 <= int(parts[1]) <= 12
    )


def is_year_month_day(string, sep: str = "-", year_func=is_year_2000s):
    """
    Check if a string represents a valid year-month-day format.
    
    Validates strings in the format YYYY{sep}MM{sep}DD with customizable
    year validation function.
    
    Args:
        string (str): The string to validate
        sep (str): The separator between date components (default: "-")
        year_func (callable): Function to validate the year part (default: is_year_2000s)
        
    Returns:
        bool: True if the string matches the date format with valid values
        
    Examples:
        >>> is_year_month_day("2023-12-31")
        True
        >>> is_year_month_day("2023-02-30")  # Invalid day for February
        True  # Note: This doesn't validate calendar correctness, only ranges
        >>> is_year_month_day("1999-01-01", year_func=is_year)
        True
    """
    parts = string.split(sep)
    # only 2 sep
    if len(parts) != 3:
        return False

    return (
        len(parts) == 3
        and year_func(parts[0])
        and parts[1].isdigit()
        and 1 <= int(parts[1]) <= 12
        and parts[2].isdigit()
        and 1 <= int(parts[2]) <= 31
    )


def is_year_month_day_time(
    string: str, sep: str = "-", time_sep: str = ".", mid_sep: str = " "
) -> bool:
    """
    Check if a string represents a valid date-time format.
    
    Validates strings in the format YYYY-MM-DD HH.MM.SS with customizable separators.
    Uses dot separator for time components by default for Windows compatibility.
    
    Args:
        string (str): The string to validate
        sep (str): The separator between date components (default: "-")
        time_sep (str): The separator between time components (default: ".")
        mid_sep (str): The separator between date and time parts (default: " ")
        
    Returns:
        bool: True if the string matches the datetime format with valid values
        
    Raises:
        ValueError: If the string doesn't contain exactly one mid_sep
        
    Examples:
        >>> is_year_month_day_time("2023-12-31 23.59.59")
        True
        >>> is_year_month_day_time("2023/12/31T23.59.59", sep="/", mid_sep="T")
        True
    """
    date_part, time_part = string.split(mid_sep)
    return is_year_month_day(date_part, sep) and is_time(time_part, time_sep)


def is_time(string: str, sep: str = ".") -> bool:
    """
    Check if a string represents a valid time format.
    
    Validates strings in the format HH{sep}MM{sep}SS where hours are 0-23,
    minutes and seconds are 0-59. Uses dot separator by default for Windows compatibility.
    
    Args:
        string (str): The string to validate
        sep (str): The separator between time components (default: ".")
        
    Returns:
        bool: True if the string matches HH{sep}MM{sep}SS format with valid values
        
    Examples:
        >>> is_time("23.59.59")
        True
        >>> is_time("24.00.00")  # Invalid hour
        False
        >>> is_time("12:30:45", sep=":")
        True
    """
    parts = string.split(sep)
    return (
        len(parts) == 3
        and all(part.isdigit() for part in parts)
        and 0 <= int(parts[0]) < 24
        and 0 <= int(parts[1]) < 60
        and 0 <= int(parts[2]) < 60
    )


def is_weekday_pattern(string: str) -> bool:
    """
    Check if a string represents a valid weekday pattern.
    
    Validates strings in the format "every_weekday" where weekday is a valid
    day name (monday through sunday).
    
    Args:
        string (str): The string to validate
        
    Returns:
        bool: True if the string matches the weekday pattern
        
    Examples:
        >>> is_weekday_pattern("every_tuesday")
        True
        >>> is_weekday_pattern("every_monday")
        True
        >>> is_weekday_pattern("every_funday")
        False
    """
    if not string.startswith("every_"):
        return False
    
    weekday = string[6:].lower()  # Remove "every_" prefix
    valid_weekdays = {
        'monday', 'tuesday', 'wednesday', 'thursday', 
        'friday', 'saturday', 'sunday'
    }
    return weekday in valid_weekdays


def is_monthly_date_pattern(string: str) -> bool:
    """
    Check if a string represents a valid monthly date override pattern.
    
    Validates strings in the format "every_month_day" where month is a valid
    month name and day is 01-31.
    
    Args:
        string (str): The string to validate
        
    Returns:
        bool: True if the string matches the monthly date pattern
        
    Examples:
        >>> is_monthly_date_pattern("every_feb_02")
        True
        >>> is_monthly_date_pattern("every_december_25")
        True
        >>> is_monthly_date_pattern("every_invalid_01")
        False
    """
    if not string.startswith("every_"):
        return False
    
    parts = string[6:].split('_')  # Remove "every_" prefix and split
    if len(parts) != 2:
        return False
    
    month_part, day_part = parts
    month_part = month_part.lower()
    
    # Valid month names (both full and abbreviated)
    valid_months = {
        'jan', 'january', 'feb', 'february', 'mar', 'march',
        'apr', 'april', 'may', 'jun', 'june',
        'jul', 'july', 'aug', 'august', 'sep', 'september',
        'oct', 'october', 'nov', 'november', 'dec', 'december'
    }
    
    # Check if day is valid format (01-31)
    if not day_part.isdigit() or len(day_part) != 2:
        return False
    
    day_num = int(day_part)
    if not (1 <= day_num <= 31):
        return False
    
    return month_part in valid_months


def is_monthtext_day(string: str, sep: str = "_") -> bool:
    """
    Check if a string represents a valid month-day format using text month names.
    
    Validates strings in the format "month{sep}day" where month is a valid
    month name (full or abbreviated) and day is 01-31.
    
    Args:
        string (str): The string to validate
        sep (str): The separator between month and day (default: "_")
        
    Returns:
        bool: True if the string matches the month-day format
        
    Examples:
        >>> is_monthtext_day("feb_02")
        True
        >>> is_monthtext_day("december_25")
        True
        >>> is_monthtext_day("invalid_01")
        False
    """
    parts = string.split(sep)
    if len(parts) != 2:
        return False
    
    month_part, day_part = parts
    month_part = month_part.lower()
    
    # Valid month names (both full and abbreviated)
    valid_months = {
        'jan', 'january', 'feb', 'february', 'mar', 'march',
        'apr', 'april', 'may', 'jun', 'june',
        'jul', 'july', 'aug', 'august', 'sep', 'september',
        'oct', 'october', 'nov', 'november', 'dec', 'december'
    }
    
    # Check if day is valid format (01-31)
    if not day_part.isdigit() or len(day_part) != 2:
        return False
    
    day_num = int(day_part)
    if not (1 <= day_num <= 31):
        return False
    
    return month_part in valid_months


def is_weekday(string: str) -> bool:
    """
    Check if a string represents a valid weekday name.
    
    Args:
        string (str): The string to validate
        
    Returns:
        bool: True if the string is a valid weekday name
        
    Examples:
        >>> is_weekday("tuesday")
        True
        >>> is_weekday("monday")
        True
        >>> is_weekday("funday")
        False
    """
    weekday = string.lower()
    valid_weekdays = {
        'monday', 'tuesday', 'wednesday', 'thursday', 
        'friday', 'saturday', 'sunday'
    }
    return weekday in valid_weekdays
