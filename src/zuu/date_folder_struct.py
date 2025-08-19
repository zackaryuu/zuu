
"""
Date-aware folder structure management system.

This module provides a comprehensive system for managing folder structures based on
date ranges. It supports various date formats and granularities, from yearly folders
to precise datetime ranges.

Key Features:
- Multiple date format support (YEAR_YEAR, YEAR-MM_YEAR-MM, etc.)
- Validation against overlapping date ranges
- Abstract design for testing and real filesystem implementations
- Automatic date range resolution for current/future folder selection

Example Usage:
    >>> # In-memory testing
    >>> folder = InMemoryDateFolder()
    >>> folder.add("YEAR_YEAR", datetime.datetime(2023, 1, 1))
    '2023_2023'
    
    >>> # Filesystem implementation
    >>> folder = DateFolder("/path/to/configs")
    >>> current_config = folder.current()  # Gets folder for current time
"""

import datetime
import os
from abc import ABC, abstractmethod
from typing import List, Dict
from .match_string import (
    is_year, is_year_month, is_year_month_day, is_time, 
    is_weekday_pattern, is_monthly_date_pattern
)


def get_datefolder_format_type(path: str) -> str | None:
    """
    Determines the date format type of a folder based on its name.
    
    Analyzes folder names to identify which date format pattern they follow.
    Supports hierarchical date formats from yearly to precise datetime ranges.
    
    Args:
        path (str): The folder path or name to analyze
        
    Returns:
        str | None: The format type identifier, or None if no valid format is detected
        
    Supported Formats:
        - "YEAR_YEAR": e.g., "2023_2024"
        - "YEAR-MM_YEAR-MM": e.g., "2023-01_2023-12"
        - "YEAR-MM-DD_YEAR-MM-DD": e.g., "2023-01-01_2023-12-31"
        - "YEAR-MM-DD-HH.MM.SS_YEAR-MM-DD-HH.MM.SS": e.g., "2023-01-01-10.30.00_2023-01-01-15.45.30"
        - "WEEKDAY_PATTERN": e.g., "every_tuesday", "every_friday"
        - "MONTHLY_DATE_PATTERN": e.g., "every_feb_02", "every_december_25"
        
    Examples:
        >>> get_datefolder_format_type("2023_2024")
        'YEAR_YEAR'
        >>> get_datefolder_format_type("2023-01-01_2023-12-31")
        'YEAR-MM-DD_YEAR-MM-DD'
        >>> get_datefolder_format_type("invalid_format")
        None
    """
    basename = os.path.basename(path)
    
    # Check for special date formats first (these can have multiple underscores)
    if is_weekday_pattern(basename):
        return "WEEKDAY_PATTERN"
    elif is_monthly_date_pattern(basename):
        return "MONTHLY_DATE_PATTERN"
    
    # count _ only 1 for regular date ranges
    underscore_count = basename.count('_')
    if underscore_count != 1:
        return None

    split1, split2 = basename.split('_')
    split1 = split1.strip()
    split2 = split2.strip()

    # Check for datetime format (YEAR-MM-DD-HH.MM.SS)
    if '-' in split1 and '.' in split1:
        # Split by last dash to separate date and time parts
        date_part1, time_part1 = split1.rsplit('-', 1)
        date_part2, time_part2 = split2.rsplit('-', 1)
        
        if (is_year_month_day(date_part1) and is_time(time_part1, ".") and
            is_year_month_day(date_part2) and is_time(time_part2, ".")):
            return "YEAR-MM-DD-HH.MM.SS_YEAR-MM-DD-HH.MM.SS"

    # Check different date format combinations
    if is_year(split1) and is_year(split2):
        return "YEAR_YEAR"
    elif is_year_month(split1) and is_year_month(split2):
        return "YEAR-MM_YEAR-MM"
    elif is_year_month_day(split1) and is_year_month_day(split2):
        return "YEAR-MM-DD_YEAR-MM-DD"
    
    return None


def parse_date_range(folder_name: str) -> tuple[datetime.datetime, datetime.datetime] | None:
    """
    Parse a date range from a folder name string.
    
    Converts folder names in supported date formats into precise datetime ranges.
    The end datetime is automatically set to the maximum possible time for the
    given granularity (e.g., year ends at 23:59:59 on Dec 31).
    
    Args:
        folder_name (str): The folder name to parse
        
    Returns:
        tuple[datetime.datetime, datetime.datetime] | None: A tuple of (start_datetime, end_datetime)
            or None if the folder name format is invalid
            
    Examples:
        >>> parse_date_range("2023_2024")
        (datetime.datetime(2023, 1, 1, 0, 0), datetime.datetime(2024, 12, 31, 23, 59, 59))
        >>> parse_date_range("2023-06_2023-06")
        (datetime.datetime(2023, 6, 1, 0, 0), datetime.datetime(2023, 6, 30, 23, 59, 59, 999999))
        >>> parse_date_range("invalid")
        None
    """
    format_type = get_datefolder_format_type(folder_name)
    if not format_type:
        return None
    
    # Handle special formats
    if format_type == "WEEKDAY_PATTERN":
        # For weekday patterns, we can't determine specific datetime ranges
        # without additional context, so return None for now
        # This could be extended to return recurring patterns
        return None
    elif format_type == "MONTHLY_DATE_PATTERN":
        # For monthly date patterns, we can't determine specific datetime ranges
        # without additional context, so return None for now  
        # This could be extended to return recurring patterns
        return None
    
    split1, split2 = folder_name.split('_')
    split1 = split1.strip()
    split2 = split2.strip()
    
    try:
        if format_type == "YEAR_YEAR":
            start_datetime = datetime.datetime(int(split1), 1, 1, 0, 0, 0)
            end_datetime = datetime.datetime(int(split2), 12, 31, 23, 59, 59)
        elif format_type == "YEAR-MM_YEAR-MM":
            year1, month1 = split1.split('-')
            year2, month2 = split2.split('-')
            start_datetime = datetime.datetime(int(year1), int(month1), 1, 0, 0, 0)
            # Get last day of the month
            if int(month2) == 12:
                end_datetime = datetime.datetime(int(year2), 12, 31, 23, 59, 59)
            else:
                next_month = datetime.datetime(int(year2), int(month2) + 1, 1, 0, 0, 0)
                end_datetime = next_month - datetime.timedelta(microseconds=1)
        elif format_type == "YEAR-MM-DD_YEAR-MM-DD":
            year1, month1, day1 = split1.split('-')
            year2, month2, day2 = split2.split('-')
            start_datetime = datetime.datetime(int(year1), int(month1), int(day1), 0, 0, 0)
            end_datetime = datetime.datetime(int(year2), int(month2), int(day2), 23, 59, 59)
        elif format_type == "YEAR-MM-DD-HH.MM.SS_YEAR-MM-DD-HH.MM.SS":
            date_part1, time_part1 = split1.rsplit('-', 1)
            date_part2, time_part2 = split2.rsplit('-', 1)
            
            year1, month1, day1 = date_part1.split('-')
            hour1, min1, sec1 = time_part1.split('.')
            start_datetime = datetime.datetime(int(year1), int(month1), int(day1), 
                                             int(hour1), int(min1), int(sec1))
            
            year2, month2, day2 = date_part2.split('-')
            hour2, min2, sec2 = time_part2.split('.')
            end_datetime = datetime.datetime(int(year2), int(month2), int(day2), 
                                           int(hour2), int(min2), int(sec2))
        else:
            return None
            
        return start_datetime, end_datetime
    except (ValueError, TypeError):
        return None


def validate_folder_names(folder_names: List[str]) -> List[str]:
    """
    Validate a list of folder names to ensure no invalid date range overlaps.
    
    Implements validation rules for date folder structures to prevent conflicting
    date ranges while allowing valid nesting patterns.
    
    Validation Rules:
        - ✅ Nested ranges are allowed (inner range completely contained within outer)
        - ✅ Separate non-overlapping ranges are allowed
        - ❌ Partial overlaps (crossing boundaries) are forbidden
    
    Args:
        folder_names (List[str]): List of folder names to validate
        
    Returns:
        List[str]: List of validation error messages. Empty list indicates validation passed.
        
    Examples:
        >>> # Valid: nested ranges
        >>> validate_folder_names(["2023-02-05_2023-02-10", "2023-02-07_2023-02-08"])
        []
        
        >>> # Invalid: overlapping edges  
        >>> validate_folder_names(["2023-02-05_2023-02-10", "2023-02-04_2023-02-08"])
        ['Invalid overlap between ...']
        
    Note:
        The validation is performed on the parsed datetime ranges, not just string comparison.
    """
    errors = []
    ranges = []
    
    # Parse all ranges
    for folder_name in folder_names:
        date_range = parse_date_range(folder_name)
        if date_range is None:
            errors.append(f"Invalid folder name format: {folder_name}")
            continue
        ranges.append((folder_name, date_range[0], date_range[1]))
    
    # Sort ranges by start time
    ranges.sort(key=lambda x: x[1])
    
    # Check for invalid overlaps
    for i, (name1, start1, end1) in enumerate(ranges):
        for j, (name2, start2, end2) in enumerate(ranges[i+1:], i+1):
            # Check if ranges overlap
            if start2 <= end1:
                # Check if it's a valid nested relationship or invalid overlap
                if start1 <= start2 and end2 <= end1:
                    # Range 2 is completely inside range 1 (valid nesting)
                    continue
                elif start2 <= start1 and end1 <= end2:
                    # Range 1 is completely inside range 2 (valid nesting)
                    continue
                else:
                    # Invalid overlap (partial overlap)
                    errors.append(f"Invalid overlap between '{name1}' ({start1} to {end1}) and '{name2}' ({start2} to {end2})")
    
    return errors


class AbstractDateFolder(ABC):
    """
    Abstract base class for date folder operations.
    
    Provides a template for managing collections of date-based folders with validation,
    sorting, and date resolution capabilities. Concrete implementations handle the
    actual I/O operations while sharing common business logic.
    
    The class maintains an internal list of folders sorted by start datetime and
    provides methods for adding new folders, resolving current/future folders,
    and validating date range conflicts.
    
    Attributes:
        _folders (List[Dict[str, any]]): Internal list of folder metadata
    
    Abstract Methods:
        _create_folder: Create the actual folder structure
        _folder_exists: Check if a folder exists
        _list_existing_folders: List existing folders in a path
        
    Example:
        This is an abstract class. Use InMemoryDateFolder for testing or
        DateFolder for filesystem operations.
    """
    
    def __init__(self):
        self._folders: List[Dict[str, any]] = []

    @abstractmethod
    def _create_folder(self, folder_path: str) -> bool:
        """
        Create the actual folder structure.
        
        Args:
            folder_path (str): Path where the folder should be created
            
        Returns:
            bool: True if creation was successful, False otherwise
        """
        pass

    @abstractmethod
    def _folder_exists(self, folder_path: str) -> bool:
        """
        Check if a folder exists.
        
        Args:
            folder_path (str): Path to check for existence
            
        Returns:
            bool: True if folder exists, False otherwise
        """
        pass

    @abstractmethod
    def _list_existing_folders(self, base_path: str) -> List[str]:
        """
        List existing folder names in the base path.
        
        Args:
            base_path (str): Base directory to scan for folders
            
        Returns:
            List[str]: List of folder names (not full paths)
        """
        pass

    def _load_existing_folders(self, base_path: str):
        """
        Load existing folders from the base path.
        
        Scans the base path for folders with valid date formats and adds them
        to the internal folder list with parsed datetime ranges.
        
        Args:
            base_path (str): Base directory to scan for existing folders
        """
        for folder_name in self._list_existing_folders(base_path):
            date_range = parse_date_range(folder_name)
            if date_range:
                folder_path = os.path.join(base_path, folder_name) if hasattr(self, '_DateFolder__path') else folder_name
                self._folders.append({
                    'name': folder_name,
                    'path': folder_path,
                    'start_datetime': date_range[0],
                    'end_datetime': date_range[1],
                    'format_type': get_datefolder_format_type(folder_name)
                })
        
        # Sort folders by start datetime
        self._folders.sort(key=lambda x: x['start_datetime'])

    def current(self, reference_datetime: datetime.datetime = None) -> str | None:
        """
        Get the path of the folder that contains the current or reference datetime.
        
        Searches through all folders to find one whose date range contains the
        specified datetime. If no reference datetime is provided, uses current time.
        
        Args:
            reference_datetime (datetime.datetime, optional): The datetime to search for.
                Defaults to datetime.now() if not provided.
                
        Returns:
            str | None: The path to the matching folder, or None if no folder contains
                the reference datetime.
                
        Examples:
            >>> folder.current()  # Uses current time
            '/path/to/2023_2023'
            >>> folder.current(datetime.datetime(2025, 6, 15))
            None  # No folder contains this date
        """
        if reference_datetime is None:
            reference_datetime = datetime.datetime.now()
            
        for folder in self._folders:
            if folder['start_datetime'] <= reference_datetime <= folder['end_datetime']:
                return folder['path']
        
        return None

    def future(self, dt: datetime.datetime) -> str | None:
        """
        Get the path of the folder that contains the specified datetime.
        
        This method is functionally identical to current() but with a more explicit
        name when you're looking for a folder for a specific future datetime.
        
        Args:
            dt (datetime.datetime): The datetime to search for
            
        Returns:
            str | None: The path to the matching folder, or None if no folder
                contains the specified datetime.
                
        Examples:
            >>> folder.future(datetime.datetime(2023, 6, 15))
            '/path/to/2023_2023'
        """
        for folder in self._folders:
            if folder['start_datetime'] <= dt <= folder['end_datetime']:
                return folder['path']
        
        return None

    def add(self, folder_type: str, start_datetime: datetime.datetime, end_datetime: datetime.datetime = None, base_path: str = None, skip_validation: bool = False) -> str:
        """
        Add a new date folder.
        
        Args:
            folder_type: Type of folder ("YEAR_YEAR", "YEAR-MM_YEAR-MM", etc.)
            start_datetime: Start datetime for the folder
            end_datetime: End datetime for the folder (optional, will be calculated based on type)
            base_path: Base path for creating folder (used by concrete implementations)
            skip_validation: If True, skip overlap validation (used for recurring patterns)
        
        Returns:
            Path to the created folder
        """
        if end_datetime is None:
            end_datetime = self._calculate_default_end_datetime(folder_type, start_datetime)
        
        # Generate folder name based on type
        folder_name = self._generate_folder_name(folder_type, start_datetime, end_datetime)
        
        # Determine folder path
        if base_path:
            folder_path = os.path.join(base_path, folder_name)
        else:
            folder_path = folder_name
        
        # Check if folder already exists
        if self._folder_exists(folder_path):
            raise ValueError(f"Folder already exists: {folder_path}")
        
        # Validate no conflicts with existing folders (unless skipping validation)
        if not skip_validation:
            all_folder_names = [f['name'] for f in self._folders] + [folder_name]
            validation_errors = validate_folder_names(all_folder_names)
            if validation_errors:
                raise ValueError(f"Validation failed: {'; '.join(validation_errors)}")
        
        # Create the folder
        if not self._create_folder(folder_path):
            raise ValueError(f"Failed to create folder: {folder_path}")
        
        # Add to internal list
        self._folders.append({
            'name': folder_name,
            'path': folder_path,
            'start_datetime': start_datetime,
            'end_datetime': end_datetime,
            'format_type': folder_type
        })
        
        # Re-sort folders by start datetime
        self._folders.sort(key=lambda x: x['start_datetime'])
        
        return folder_path

    def _calculate_default_end_datetime(self, folder_type: str, start_datetime: datetime.datetime) -> datetime.datetime:
        """Calculate default end datetime based on folder type."""
        if folder_type == "YEAR_YEAR":
            return datetime.datetime(start_datetime.year, 12, 31, 23, 59, 59)
        elif folder_type == "YEAR-MM_YEAR-MM":
            if start_datetime.month == 12:
                return datetime.datetime(start_datetime.year, 12, 31, 23, 59, 59)
            else:
                next_month = datetime.datetime(start_datetime.year, start_datetime.month + 1, 1, 0, 0, 0)
                return next_month - datetime.timedelta(microseconds=1)
        elif folder_type == "YEAR-MM-DD_YEAR-MM-DD":
            return datetime.datetime(start_datetime.year, start_datetime.month, start_datetime.day, 23, 59, 59)
        elif folder_type == "YEAR-MM-DD-HH.MM.SS_YEAR-MM-DD-HH.MM.SS":
            return start_datetime
        else:
            raise ValueError(f"Unknown folder_type: {folder_type}")

    def _generate_folder_name(self, folder_type: str, start_datetime: datetime.datetime, end_datetime: datetime.datetime) -> str:
        """Generate folder name based on type and datetime range."""
        if folder_type == "YEAR_YEAR":
            return f"{start_datetime.year}_{end_datetime.year}"
        elif folder_type == "YEAR-MM_YEAR-MM":
            return f"{start_datetime.year}-{start_datetime.month:02d}_{end_datetime.year}-{end_datetime.month:02d}"
        elif folder_type == "YEAR-MM-DD_YEAR-MM-DD":
            return f"{start_datetime.year}-{start_datetime.month:02d}-{start_datetime.day:02d}_{end_datetime.year}-{end_datetime.month:02d}-{end_datetime.day:02d}"
        elif folder_type == "YEAR-MM-DD-HH.MM.SS_YEAR-MM-DD-HH.MM.SS":
            start_str = f"{start_datetime.year}-{start_datetime.month:02d}-{start_datetime.day:02d}-{start_datetime.hour:02d}.{start_datetime.minute:02d}.{start_datetime.second:02d}"
            end_str = f"{end_datetime.year}-{end_datetime.month:02d}-{end_datetime.day:02d}-{end_datetime.hour:02d}.{end_datetime.minute:02d}.{end_datetime.second:02d}"
            return f"{start_str}_{end_str}"
        else:
            raise ValueError(f"Unknown folder_type: {folder_type}")

    def list_folders(self) -> List[Dict[str, any]]:
        """Return list of all date folders with their metadata."""
        return self._folders.copy()

    def get_folder_for_datetime(self, target_datetime: datetime.datetime) -> str | None:
        """Get folder path that contains the target datetime."""
        return self.future(target_datetime)

    def add_every(self, pattern: str, start_date: datetime.datetime = None, count: int = None) -> str | List[str]:
        """
        Create folders for recurring patterns.
        
        Args:
            pattern (str): The recurring pattern. Supported patterns:
                - Weekdays: "monday", "tuesday", ..., "sunday"
                - Monthly dates: "jan_01", "feb_14", "dec_25", etc.
                - Time periods: "week", "month", "quarter", "year"
                - Special patterns: "weekend", "workweek"
            start_date (datetime.datetime, optional): Starting date for the pattern.
                Defaults to current date if not provided.
            count (int, optional): Number of occurrences to create.
                Defaults vary by pattern type.
        
        Returns:
            str | List[str]: Single folder name for count=1, list of folder names for count>1
            
        Raises:
            ValueError: For invalid patterns or parameters
            
        Examples:
            >>> folder.add_every("tuesday", count=4)  # Next 4 Tuesdays
            >>> folder.add_every("feb_14", count=3)   # Next 3 Valentine's Days
            >>> folder.add_every("month", count=6)    # Next 6 months
        """
        if start_date is None:
            start_date = datetime.datetime.now()
        
        if count is None:
            count = 1
            
        if count == 0:
            return []
            
        # Import here to avoid circular imports
        from .match_string import is_weekday, is_monthtext_day
        
        created_folders = []
        
        # Handle weekday patterns
        if is_weekday(pattern.lower()):
            created_folders = self._add_every_weekday(pattern.lower(), start_date, count)
            
        # Handle monthly date patterns (both "feb_14" and "february_14" formats)
        elif "_" in pattern and (is_monthtext_day(pattern.lower()) or pattern.lower().startswith("every_")):
            # Remove "every_" prefix if present
            clean_pattern = pattern.lower()
            if clean_pattern.startswith("every_"):
                clean_pattern = clean_pattern[6:]  # Remove "every_" prefix
            
            # Validate the clean pattern before processing
            if not is_monthtext_day(clean_pattern):
                raise ValueError(f"Invalid pattern: {pattern}")
                
            created_folders = self._add_every_monthly_date(clean_pattern, start_date, count)
            
        # Handle time period patterns
        elif pattern.lower() in ["week", "month", "quarter", "year"]:
            created_folders = self._add_every_time_period(pattern.lower(), start_date, count)
            
        # Handle special patterns
        elif pattern.lower() in ["weekend", "workweek"]:
            created_folders = self._add_every_special_pattern(pattern.lower(), start_date, count)
            
        else:
            raise ValueError(f"Invalid pattern: {pattern}")
        
        # Return single string for count=1, list for count>1
        if count == 1 and len(created_folders) == 1:
            return created_folders[0]
        return created_folders

    def _add_every_weekday(self, weekday: str, start_date: datetime.datetime, count: int) -> List[str]:
        """Create folders for recurring weekday pattern."""
        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        target_weekday = weekdays.index(weekday.lower())
        
        created_folders = []
        current_date = start_date
        
        # Find next occurrence of the target weekday
        days_ahead = target_weekday - current_date.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        current_date = current_date + datetime.timedelta(days=days_ahead)
        
        # Create folders for each occurrence
        for i in range(count):
            folder_date = current_date + datetime.timedelta(weeks=i)
            folder_name = self.add("YEAR-MM-DD_YEAR-MM-DD", folder_date, folder_date, skip_validation=True)
            created_folders.append(folder_name)
            
        return created_folders

    def _add_every_monthly_date(self, month_day: str, start_date: datetime.datetime, count: int) -> List[str]:
        """Create folders for recurring monthly date pattern."""
        # Parse month and day from pattern like "feb_14" or "february_14"
        parts = month_day.split('_')
        if len(parts) != 2:
            raise ValueError(f"Invalid monthly date pattern: {month_day}")
            
        month_name, day_str = parts
        
        # Map month names to numbers
        month_map = {
            'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
            'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6,
            'jul': 7, 'july': 7, 'aug': 8, 'august': 8, 'sep': 9, 'september': 9,
            'oct': 10, 'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12
        }
        
        if month_name.lower() not in month_map:
            raise ValueError(f"Invalid month name: {month_name}")
            
        target_month = month_map[month_name.lower()]
        
        try:
            target_day = int(day_str)
            if not (1 <= target_day <= 31):
                raise ValueError(f"Invalid day: {target_day}")
        except ValueError:
            raise ValueError(f"Invalid day format: {day_str}")
        
        created_folders = []
        current_year = start_date.year
        
        # Find next occurrence of the target month/day
        try:
            next_date = datetime.datetime(current_year, target_month, target_day)
            if next_date <= start_date:
                next_date = datetime.datetime(current_year + 1, target_month, target_day)
        except ValueError:
            # Handle invalid dates (like Feb 30)
            next_date = datetime.datetime(current_year + 1, target_month, target_day)
        
        # Create folders for each occurrence
        for i in range(count):
            try:
                folder_date = datetime.datetime(next_date.year + i, target_month, target_day)
                folder_name = self.add("YEAR-MM-DD_YEAR-MM-DD", folder_date, folder_date, skip_validation=True)
                created_folders.append(folder_name)
            except ValueError:
                # Skip invalid dates (like Feb 29 in non-leap years)
                continue
                
        return created_folders

    def _add_every_time_period(self, period: str, start_date: datetime.datetime, count: int) -> List[str]:
        """Create folders for recurring time period pattern."""
        created_folders = []
        
        if period == "week":
            for i in range(count):
                week_start = start_date + datetime.timedelta(weeks=i)
                week_end = week_start + datetime.timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)
                folder_name = self.add("YEAR-MM-DD_YEAR-MM-DD", week_start, week_end, skip_validation=True)
                created_folders.append(folder_name)
                
        elif period == "month":
            for i in range(count):
                if i == 0:
                    month_start = start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                else:
                    # Calculate next month
                    year = start_date.year
                    month = start_date.month + i
                    while month > 12:
                        year += 1
                        month -= 12
                    month_start = datetime.datetime(year, month, 1)
                
                # Calculate month end
                if month_start.month == 12:
                    next_month = datetime.datetime(month_start.year + 1, 1, 1)
                else:
                    next_month = datetime.datetime(month_start.year, month_start.month + 1, 1)
                month_end = next_month - datetime.timedelta(microseconds=1)
                
                folder_name = self.add("YEAR-MM_YEAR-MM", month_start, month_end, skip_validation=True)
                created_folders.append(folder_name)
                
        elif period == "quarter":
            for i in range(count):
                # Determine quarter start
                quarter_month = ((start_date.month - 1) // 3) * 3 + 1 + (i * 3)
                quarter_year = start_date.year
                while quarter_month > 12:
                    quarter_year += 1
                    quarter_month -= 12
                
                quarter_start = datetime.datetime(quarter_year, quarter_month, 1)
                
                # Quarter end (3 months later)
                end_month = quarter_month + 2
                end_year = quarter_year
                if end_month > 12:
                    end_year += 1
                    end_month -= 12
                
                # Last day of quarter
                if end_month == 12:
                    next_month = datetime.datetime(end_year + 1, 1, 1)
                else:
                    next_month = datetime.datetime(end_year, end_month + 1, 1)
                quarter_end = next_month - datetime.timedelta(microseconds=1)
                
                folder_name = self.add("YEAR-MM_YEAR-MM", quarter_start, quarter_end, skip_validation=True)
                created_folders.append(folder_name)
                
        elif period == "year":
            for i in range(count):
                year_start = datetime.datetime(start_date.year + i, 1, 1)
                year_end = datetime.datetime(start_date.year + i, 12, 31, 23, 59, 59)
                folder_name = self.add("YEAR_YEAR", year_start, year_end, skip_validation=True)
                created_folders.append(folder_name)
                
        return created_folders

    def _add_every_special_pattern(self, pattern: str, start_date: datetime.datetime, count: int) -> List[str]:
        """Create folders for special recurring patterns."""
        created_folders = []
        
        if pattern == "weekend":
            current_date = start_date
            
            # Find next Saturday
            days_ahead = 5 - current_date.weekday()  # 5 = Saturday
            if days_ahead <= 0:
                days_ahead += 7
            current_date = current_date + datetime.timedelta(days=days_ahead)
            
            for i in range(count):
                weekend_start = current_date + datetime.timedelta(weeks=i)  # Saturday
                weekend_end = weekend_start + datetime.timedelta(days=1, hours=23, minutes=59, seconds=59)  # Sunday end
                folder_name = self.add("YEAR-MM-DD_YEAR-MM-DD", weekend_start, weekend_end, skip_validation=True)
                created_folders.append(folder_name)
                
        elif pattern == "workweek":
            current_date = start_date
            
            # Find next Monday
            days_ahead = 0 - current_date.weekday()  # 0 = Monday
            if days_ahead <= 0:
                days_ahead += 7
            current_date = current_date + datetime.timedelta(days=days_ahead)
            
            for i in range(count):
                workweek_start = current_date + datetime.timedelta(weeks=i)  # Monday
                workweek_end = workweek_start + datetime.timedelta(days=4, hours=23, minutes=59, seconds=59)  # Friday end
                folder_name = self.add("YEAR-MM-DD_YEAR-MM-DD", workweek_start, workweek_end, skip_validation=True)
                created_folders.append(folder_name)
                
        return created_folders


class InMemoryDateFolder(AbstractDateFolder):
    """
    In-memory implementation of date folder management for testing.
    
    This implementation stores folder information in memory without performing
    any filesystem I/O operations. Perfect for unit testing and scenarios where
    you need to test date folder logic without creating actual directories.
    
    Attributes:
        _existing_folders (set): Set of folder names that existed at initialization
        _created_folders (set): Set of folder names created during this session
        
    Examples:
        >>> # Create empty in-memory folder
        >>> folder = InMemoryDateFolder()
        >>> folder.add("YEAR_YEAR", datetime.datetime(2023, 1, 1))
        '2023_2023'
        
        >>> # Create with existing folders
        >>> folder = InMemoryDateFolder(["2022_2022", "2023_2023"])
        >>> len(folder.list_folders())
        2
    """
    
    def __init__(self, existing_folders: List[str] = None):
        """
        Initialize an in-memory date folder with optional existing folders.
        
        Args:
            existing_folders (List[str], optional): List of folder names that should
                be considered as already existing. Only folders with valid date formats
                will be loaded.
        """
        super().__init__()
        self._existing_folders = set(existing_folders or [])
        self._created_folders = set()
        
        # Load existing folders
        if existing_folders:
            for folder_name in existing_folders:
                date_range = parse_date_range(folder_name)
                if date_range:
                    self._folders.append({
                        'name': folder_name,
                        'path': folder_name,
                        'start_datetime': date_range[0],
                        'end_datetime': date_range[1],
                        'format_type': get_datefolder_format_type(folder_name)
                    })
            
            self._folders.sort(key=lambda x: x['start_datetime'])

    def _create_folder(self, folder_path: str) -> bool:
        """Create the folder in memory."""
        folder_name = os.path.basename(folder_path)
        self._created_folders.add(folder_name)
        return True

    def _folder_exists(self, folder_path: str) -> bool:
        """Check if folder exists in memory."""
        folder_name = os.path.basename(folder_path)
        return folder_name in self._existing_folders or folder_name in self._created_folders

    def _list_existing_folders(self, base_path: str) -> List[str]:
        """List existing folder names."""
        return list(self._existing_folders)

    def get_created_folders(self) -> List[str]:
        """
        Get list of folders created during this session.
        
        Returns:
            List[str]: List of folder names that were created using add() method
                during the current session.
                
        Examples:
            >>> folder = InMemoryDateFolder()
            >>> folder.add("YEAR_YEAR", datetime.datetime(2023, 1, 1))
            '2023_2023'
            >>> folder.get_created_folders()
            ['2023_2023']
        """
        return list(self._created_folders)


class DateFolder(AbstractDateFolder):
    """
    Filesystem-based implementation of date folder management.
    
    This implementation creates and manages actual directories on the filesystem.
    It scans an existing directory for date-formatted folders and allows creation
    of new date-based folder structures.
    
    Args:
        path (str): Base directory path where date folders will be managed
        
    Raises:
        ValueError: If the path doesn't exist or contains non-directory files
        
    Examples:
        >>> folder = DateFolder("/path/to/configs")
        >>> folder.add("YEAR-MM_YEAR-MM", datetime.datetime(2023, 6, 1))
        '/path/to/configs/2023-06_2023-06'
        >>> folder.current()
        '/path/to/configs/2023-06_2023-06'  # If current time is in June 2023
    """
    def __init__(self, path: str):
        super().__init__()
        self.__path = path
        
        if not os.path.exists(path):
            raise ValueError(f"Path does not exist: {path}")
            
        for subpath in os.listdir(self.__path):
            full_subpath = os.path.join(self.__path, subpath)
            if not os.path.isdir(full_subpath):
                raise ValueError(f"Expected first level to be subdirectories only, but got file: {subpath}")
        
        # Load existing folders
        self._load_existing_folders(self.__path)

    def _create_folder(self, folder_path: str) -> bool:
        """Create the actual folder on filesystem."""
        try:
            os.makedirs(folder_path, exist_ok=False)
            return True
        except OSError:
            return False

    def _folder_exists(self, folder_path: str) -> bool:
        """Check if folder exists on filesystem."""
        return os.path.exists(folder_path)

    def _list_existing_folders(self, base_path: str) -> List[str]:
        """List existing folder names in the filesystem."""
        if not os.path.exists(base_path):
            return []
        return [name for name in os.listdir(base_path) 
                if os.path.isdir(os.path.join(base_path, name))]

    def add(self, folder_type: str, start_datetime: datetime.datetime, end_datetime: datetime.datetime = None) -> str:
        """Add a new date folder to the filesystem."""
        return super().add(folder_type, start_datetime, end_datetime, self.__path)


class DateFolderTree:
    """
    Management system for multiple DateFolder collections.
    
    A DateFolderTree manages multiple DateFolder instances within a base directory.
    Each subdirectory in the base path can contain its own collection of date folders,
    allowing for organized hierarchical structures like separate configurations for
    different applications or environments.
    
    Args:
        basepath (str): Base directory path where DateFolder collections will be managed
        
    Examples:
        >>> tree = DateFolderTree("/path/to/configs")
        >>> app1_folder = tree.create_date_folder("app1_configs")
        >>> app2_folder = tree.create_date_folder("app2_configs")
        >>> tree.list_date_folders()
        ['app1_configs', 'app2_configs']
    """
    def __init__(self, basepath: str):
        self.__basepath = basepath
        self.__date_folders: Dict[str, DateFolder] = {}
        
        if not os.path.exists(basepath):
            os.makedirs(basepath, exist_ok=True)
        
        # Scan for existing date folder structures
        self._scan_structure()
    
    def _scan_structure(self):
        """
        Scan the base path for existing date folder structures.
        
        Examines each subdirectory in the base path to see if it contains valid
        date folders. Only directories with valid date folder structures are
        added to the internal collection.
        """
        if not os.path.exists(self.__basepath):
            return
            
        for item in os.listdir(self.__basepath):
            item_path = os.path.join(self.__basepath, item)
            if os.path.isdir(item_path):
                try:
                    date_folder = DateFolder(item_path)
                    if date_folder.list_folders():  # Only add if it has valid date folders
                        self.__date_folders[item] = date_folder
                except ValueError:
                    # Skip directories that don't conform to date folder structure
                    continue
    
    def get_date_folder(self, name: str) -> DateFolder | None:
        """
        Get a specific date folder collection by name.
        
        Args:
            name (str): The name of the date folder collection
            
        Returns:
            DateFolder | None: The DateFolder instance, or None if not found
        """
        return self.__date_folders.get(name)
    
    def create_date_folder(self, name: str) -> DateFolder:
        """
        Create a new date folder collection.
        
        Creates a new directory and DateFolder instance for managing date-based
        folders within that directory.
        
        Args:
            name (str): The name for the new date folder collection
            
        Returns:
            DateFolder: The newly created DateFolder instance
        """
        folder_path = os.path.join(self.__basepath, name)
        os.makedirs(folder_path, exist_ok=True)
        
        date_folder = DateFolder(folder_path)
        self.__date_folders[name] = date_folder
        
        return date_folder
    
    def list_date_folders(self) -> List[str]:
        """
        List all date folder collection names.
        
        Returns:
            List[str]: List of all date folder collection names managed by this tree
        """
        return list(self.__date_folders.keys())


