import pytest
import datetime
from zuu.date_folder_struct import (
    InMemoryDateFolder,
    get_datefolder_format_type,
    parse_date_range,
    validate_folder_names,
)


class TestGetDatefolderFormatType:
    def test_valid_year_year_format(self):
        assert get_datefolder_format_type("2023_2024") == "YEAR_YEAR"
        assert get_datefolder_format_type("2000_2099") == "YEAR_YEAR"

    def test_valid_year_month_format(self):
        assert get_datefolder_format_type("2023-01_2023-12") == "YEAR-MM_YEAR-MM"
        assert get_datefolder_format_type("2023-06_2024-01") == "YEAR-MM_YEAR-MM"

    def test_valid_year_month_day_format(self):
        assert get_datefolder_format_type("2023-01-01_2023-12-31") == "YEAR-MM-DD_YEAR-MM-DD"
        assert get_datefolder_format_type("2023-06-15_2023-06-30") == "YEAR-MM-DD_YEAR-MM-DD"

    def test_valid_datetime_format(self):
        assert get_datefolder_format_type("2023-01-01-10.30.00_2023-01-01-15.45.30") == "YEAR-MM-DD-HH.MM.SS_YEAR-MM-DD-HH.MM.SS"
        assert get_datefolder_format_type("2023-12-31-23.59.59_2024-01-01-00.00.00") == "YEAR-MM-DD-HH.MM.SS_YEAR-MM-DD-HH.MM.SS"

    def test_valid_special_formats(self):
        assert get_datefolder_format_type("every_tuesday") == "WEEKDAY_PATTERN"
        assert get_datefolder_format_type("every_friday") == "WEEKDAY_PATTERN"
        assert get_datefolder_format_type("every_feb_02") == "MONTHLY_DATE_PATTERN"
        assert get_datefolder_format_type("every_december_25") == "MONTHLY_DATE_PATTERN"

    def test_invalid_formats(self):
        assert get_datefolder_format_type("2023") is None
        assert get_datefolder_format_type("2023_2024_2025") is None
        assert get_datefolder_format_type("invalid_format") is None
        assert get_datefolder_format_type("2023-01_invalid") is None
        assert get_datefolder_format_type("every_funday") is None
        assert get_datefolder_format_type("every_invalid_01") is None

    def test_with_paths(self):
        assert get_datefolder_format_type("/path/to/2023_2024") == "YEAR_YEAR"
        assert get_datefolder_format_type("C:\\path\\to\\2023-01_2023-12") == "YEAR-MM_YEAR-MM"


class TestParseDateRange:
    def test_parse_year_range(self):
        start, end = parse_date_range("2023_2024")
        assert start == datetime.datetime(2023, 1, 1, 0, 0, 0)
        assert end == datetime.datetime(2024, 12, 31, 23, 59, 59)

    def test_parse_year_month_range(self):
        start, end = parse_date_range("2023-01_2023-03")
        assert start == datetime.datetime(2023, 1, 1, 0, 0, 0)
        assert end == datetime.datetime(2023, 3, 31, 23, 59, 59, 999999)

    def test_parse_year_month_day_range(self):
        start, end = parse_date_range("2023-01-15_2023-01-31")
        assert start == datetime.datetime(2023, 1, 15, 0, 0, 0)
        assert end == datetime.datetime(2023, 1, 31, 23, 59, 59)

    def test_parse_datetime_range(self):
        start, end = parse_date_range("2023-01-01-10.30.15_2023-01-01-15.45.30")
        assert start == datetime.datetime(2023, 1, 1, 10, 30, 15)
        assert end == datetime.datetime(2023, 1, 1, 15, 45, 30)

    def test_parse_special_formats(self):
        # Special formats should return None as they don't have specific datetime ranges
        assert parse_date_range("every_tuesday") is None
        assert parse_date_range("every_feb_02") is None

    def test_parse_invalid_range(self):
        assert parse_date_range("invalid_format") is None
        assert parse_date_range("2023") is None


class TestValidateFolderNames:
    def test_valid_nested_ranges(self):
        # Valid: completely nested ranges
        folder_names = ["2023-02-05_2023-02-10", "2023-02-07_2023-02-08"]
        errors = validate_folder_names(folder_names)
        assert errors == []

    def test_valid_separate_ranges(self):
        # Valid: non-overlapping ranges
        folder_names = ["2023-02-01_2023-02-05", "2023-02-10_2023-02-15"]
        errors = validate_folder_names(folder_names)
        assert errors == []

    def test_invalid_overlapping_edges(self):
        # Invalid: overlapping edges
        folder_names = ["2023-02-05_2023-02-10", "2023-02-04_2023-02-08"]
        errors = validate_folder_names(folder_names)
        assert len(errors) == 1
        assert "Invalid overlap" in errors[0]

    def test_invalid_overlapping_edges_reverse_order(self):
        # Invalid: overlapping edges (different input order)
        folder_names = ["2023-02-04_2023-02-08", "2023-02-05_2023-02-10"]
        errors = validate_folder_names(folder_names)
        assert len(errors) == 1
        assert "Invalid overlap" in errors[0]

    def test_multiple_nested_levels(self):
        # Valid: multiple levels of nesting
        folder_names = [
            "2023-01-01_2023-12-31",  # Year level
            "2023-02-01_2023-02-28",  # Month level inside year
            "2023-02-05_2023-02-10",  # Week level inside month
            "2023-02-07_2023-02-08"   # Day level inside week
        ]
        errors = validate_folder_names(folder_names)
        assert errors == []

    def test_invalid_format_in_list(self):
        folder_names = ["2023-02-05_2023-02-10", "invalid_format"]
        errors = validate_folder_names(folder_names)
        assert len(errors) == 1
        assert "Invalid folder name format" in errors[0]

    def test_datetime_ranges_validation(self):
        # Valid: datetime ranges with proper nesting
        folder_names = [
            "2023-02-05-10.00.00_2023-02-05-18.00.00",
            "2023-02-05-12.00.00_2023-02-05-14.00.00"
        ]
        errors = validate_folder_names(folder_names)
        assert errors == []

    def test_datetime_ranges_invalid_overlap(self):
        # Invalid: datetime ranges with overlap
        folder_names = [
            "2023-02-05-10.00.00_2023-02-05-16.00.00",
            "2023-02-05-14.00.00_2023-02-05-18.00.00"
        ]
        errors = validate_folder_names(folder_names)
        assert len(errors) == 1
        assert "Invalid overlap" in errors[0]


class TestInMemoryDateFolder:
    def test_init_empty(self):
        folder = InMemoryDateFolder()
        assert folder.list_folders() == []
        assert folder.get_created_folders() == []

    def test_init_with_existing_folders(self):
        existing = ["2023_2024", "2025_2026"]
        folder = InMemoryDateFolder(existing)
        
        folders = folder.list_folders()
        assert len(folders) == 2
        assert any(f['name'] == "2023_2024" for f in folders)
        assert any(f['name'] == "2025_2026" for f in folders)

    def test_init_with_invalid_existing_folders(self):
        existing = ["2023_2024", "invalid_format", "2025_2026"]
        folder = InMemoryDateFolder(existing)
        
        folders = folder.list_folders()
        # Should only load valid folders
        assert len(folders) == 2
        assert any(f['name'] == "2023_2024" for f in folders)
        assert any(f['name'] == "2025_2026" for f in folders)

    def test_add_year_folder(self):
        folder = InMemoryDateFolder()
        start_datetime = datetime.datetime(2023, 1, 1)
        
        folder_path = folder.add("YEAR_YEAR", start_datetime)
        
        assert folder_path == "2023_2023"
        assert "2023_2023" in folder.get_created_folders()
        
        folders = folder.list_folders()
        assert len(folders) == 1
        assert folders[0]['name'] == "2023_2023"
        assert folders[0]['start_datetime'] == datetime.datetime(2023, 1, 1, 0, 0, 0)
        assert folders[0]['end_datetime'] == datetime.datetime(2023, 12, 31, 23, 59, 59)

    def test_add_year_month_folder(self):
        folder = InMemoryDateFolder()
        start_datetime = datetime.datetime(2023, 6, 1)
        
        folder_path = folder.add("YEAR-MM_YEAR-MM", start_datetime)
        
        assert folder_path == "2023-06_2023-06"
        
        folders = folder.list_folders()
        assert len(folders) == 1
        assert folders[0]['start_datetime'] == datetime.datetime(2023, 6, 1, 0, 0, 0)
        assert folders[0]['end_datetime'] == datetime.datetime(2023, 6, 30, 23, 59, 59, 999999)

    def test_add_year_month_day_folder(self):
        folder = InMemoryDateFolder()
        start_datetime = datetime.datetime(2023, 6, 15)
        
        folder_path = folder.add("YEAR-MM-DD_YEAR-MM-DD", start_datetime)
        
        assert folder_path == "2023-06-15_2023-06-15"
        
        folders = folder.list_folders()
        assert folders[0]['start_datetime'] == datetime.datetime(2023, 6, 15, 0, 0, 0)
        assert folders[0]['end_datetime'] == datetime.datetime(2023, 6, 15, 23, 59, 59)

    def test_add_datetime_folder(self):
        folder = InMemoryDateFolder()
        start_datetime = datetime.datetime(2023, 6, 15, 10, 30, 45)
        end_datetime = datetime.datetime(2023, 6, 15, 15, 45, 30)

        folder_path = folder.add("YEAR-MM-DD-HH.MM.SS_YEAR-MM-DD-HH.MM.SS", start_datetime, end_datetime)
        assert folder_path == "2023-06-15-10.30.45_2023-06-15-15.45.30"
        
        folders = folder.list_folders()
        assert folders[0]['start_datetime'] == start_datetime
        assert folders[0]['end_datetime'] == end_datetime

    def test_add_with_custom_end_datetime(self):
        folder = InMemoryDateFolder()
        start_datetime = datetime.datetime(2023, 1, 1)
        end_datetime = datetime.datetime(2023, 6, 30, 23, 59, 59)
        
        folder_path = folder.add("YEAR-MM-DD_YEAR-MM-DD", start_datetime, end_datetime)
        
        assert folder_path == "2023-01-01_2023-06-30"

    def test_add_duplicate_folder_raises_error(self):
        folder = InMemoryDateFolder()
        start_datetime = datetime.datetime(2023, 1, 1)
        
        folder.add("YEAR_YEAR", start_datetime)
        
        with pytest.raises(ValueError, match="Folder already exists"):
            folder.add("YEAR_YEAR", start_datetime)

    def test_add_with_existing_folder_conflict(self):
        existing = ["2023_2023"]
        folder = InMemoryDateFolder(existing)
        start_datetime = datetime.datetime(2023, 1, 1)
        
        with pytest.raises(ValueError, match="Folder already exists"):
            folder.add("YEAR_YEAR", start_datetime)

    def test_add_invalid_overlap_raises_error(self):
        folder = InMemoryDateFolder()
        
        # Add first folder
        folder.add("YEAR-MM-DD_YEAR-MM-DD", datetime.datetime(2023, 2, 5), datetime.datetime(2023, 2, 10))
        
        # Try to add overlapping folder (should fail)
        with pytest.raises(ValueError, match="Validation failed"):
            folder.add("YEAR-MM-DD_YEAR-MM-DD", datetime.datetime(2023, 2, 4), datetime.datetime(2023, 2, 8))

    def test_add_valid_nested_folder(self):
        folder = InMemoryDateFolder()
        
        # Add outer folder
        folder.add("YEAR-MM-DD_YEAR-MM-DD", datetime.datetime(2023, 2, 5), datetime.datetime(2023, 2, 10))
        
        # Add nested folder (should succeed)
        folder.add("YEAR-MM-DD_YEAR-MM-DD", datetime.datetime(2023, 2, 7), datetime.datetime(2023, 2, 8))
        
        folders = folder.list_folders()
        assert len(folders) == 2

    def test_current_folder(self):
        folder = InMemoryDateFolder()
        
        # Add folders for different years
        folder.add("YEAR_YEAR", datetime.datetime(2022, 1, 1))
        folder.add("YEAR_YEAR", datetime.datetime(2023, 1, 1))
        folder.add("YEAR_YEAR", datetime.datetime(2024, 1, 1))
        
        # Test with reference datetime in 2023
        current_path = folder.current(datetime.datetime(2023, 6, 15, 12, 30, 45))
        assert current_path == "2023_2023"

    def test_current_folder_no_match(self):
        folder = InMemoryDateFolder()
        
        # Add folder for 2023
        folder.add("YEAR_YEAR", datetime.datetime(2023, 1, 1))
        
        # Test with reference datetime in 2024
        current_path = folder.current(datetime.datetime(2024, 6, 15))
        assert current_path is None

    def test_current_folder_default_now(self):
        folder = InMemoryDateFolder()
        
        # Add folder for current year
        current_year = datetime.datetime.now().year
        folder.add("YEAR_YEAR", datetime.datetime(current_year, 1, 1))
        
        # Test with no reference datetime (should use current time)
        current_path = folder.current()
        assert current_path == f"{current_year}_{current_year}"

    def test_future_folder(self):
        folder = InMemoryDateFolder()
        
        # Add folders for different periods
        folder.add("YEAR-MM_YEAR-MM", datetime.datetime(2023, 1, 1))
        folder.add("YEAR-MM_YEAR-MM", datetime.datetime(2023, 6, 1))
        
        # Test getting folder for specific datetime
        future_path = folder.future(datetime.datetime(2023, 6, 15, 10, 30))
        assert future_path == "2023-06_2023-06"

    def test_get_folder_for_datetime(self):
        folder = InMemoryDateFolder()
        
        folder.add("YEAR-MM-DD-HH.MM.SS_YEAR-MM-DD-HH.MM.SS", 
                  datetime.datetime(2023, 6, 15, 10, 0, 0),
                  datetime.datetime(2023, 6, 15, 18, 0, 0))
        
        folder_path = folder.get_folder_for_datetime(datetime.datetime(2023, 6, 15, 14, 30, 0))
        assert folder_path == "2023-06-15-10.00.00_2023-06-15-18.00.00"

    def test_folders_sorted_by_start_datetime(self):
        folder = InMemoryDateFolder()
        
        # Add folders in non-chronological order
        folder.add("YEAR-MM-DD_YEAR-MM-DD", datetime.datetime(2023, 3, 1), datetime.datetime(2023, 3, 31))
        folder.add("YEAR-MM-DD_YEAR-MM-DD", datetime.datetime(2023, 1, 1), datetime.datetime(2023, 1, 31))
        folder.add("YEAR-MM-DD_YEAR-MM-DD", datetime.datetime(2023, 2, 1), datetime.datetime(2023, 2, 28))
        
        folders = folder.list_folders()
        assert len(folders) == 3
        
        # Check they're sorted by start datetime
        assert folders[0]['start_datetime'] == datetime.datetime(2023, 1, 1, 0, 0, 0)
        assert folders[1]['start_datetime'] == datetime.datetime(2023, 2, 1, 0, 0, 0)
        assert folders[2]['start_datetime'] == datetime.datetime(2023, 3, 1, 0, 0, 0)

    def test_unknown_folder_type_raises_error(self):
        folder = InMemoryDateFolder()
        
        with pytest.raises(ValueError, match="Unknown folder_type"):
            folder.add("UNKNOWN_TYPE", datetime.datetime(2023, 1, 1))


class TestEdgeCases:
    def test_datetime_ranges_at_boundaries(self):
        folder = InMemoryDateFolder()
        
        # Add ranges that touch at boundaries (should be valid)
        folder.add("YEAR-MM-DD-HH.MM.SS_YEAR-MM-DD-HH.MM.SS",
                  datetime.datetime(2023, 1, 1, 0, 0, 0),
                  datetime.datetime(2023, 1, 1, 12, 0, 0))
        
        folder.add("YEAR-MM-DD-HH.MM.SS_YEAR-MM-DD-HH.MM.SS",
                  datetime.datetime(2023, 1, 1, 12, 0, 1),
                  datetime.datetime(2023, 1, 1, 23, 59, 59))
        
        folders = folder.list_folders()
        assert len(folders) == 2

    def test_microsecond_precision(self):
        folder = InMemoryDateFolder()
        
        # Test with microsecond precision
        start = datetime.datetime(2023, 1, 1, 12, 0, 0, 123456)
        end = datetime.datetime(2023, 1, 1, 12, 0, 0, 789012)
        
        folder.add("YEAR-MM-DD-HH.MM.SS_YEAR-MM-DD-HH.MM.SS", start, end)
        
        folders = folder.list_folders()
        # Note: folder name won't include microseconds, but internal datetime should
        assert folders[0]['start_datetime'] == start
        assert folders[0]['end_datetime'] == end


class TestAddEveryMethod:
    """Test cases for the add_every method for recurring patterns."""

    def test_add_every_weekday_pattern(self):
        """Test creating recurring weekday folders."""
        folder = InMemoryDateFolder()
        start_date = datetime.datetime(2025, 8, 18)  # Monday
        
        # Add next 3 Tuesdays
        result = folder.add_every("tuesday", start_date=start_date, count=3)
        
        # Should create 3 folders for consecutive Tuesdays
        folders = folder.list_folders()
        assert len(folders) == 3
        
        # Check folder names are for Tuesdays
        expected_dates = [
            datetime.datetime(2025, 8, 19),  # First Tuesday after start
            datetime.datetime(2025, 8, 26),  # Following Tuesday
            datetime.datetime(2025, 9, 2)    # Third Tuesday
        ]
        
        for i, expected_date in enumerate(expected_dates):
            expected_name = f"{expected_date.strftime('%Y-%m-%d')}_{expected_date.strftime('%Y-%m-%d')}"
            assert folders[i]['name'] == expected_name

    def test_add_every_all_weekdays(self):
        """Test all weekday patterns."""
        folder = InMemoryDateFolder()
        start_date = datetime.datetime(2025, 8, 18)  # Monday
        
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        for weekday in weekdays:
            # Clear folder for each test
            folder_test = InMemoryDateFolder()
            result = folder_test.add_every(weekday, start_date=start_date, count=2)
            
            folders = folder_test.list_folders()
            assert len(folders) == 2
            
            # Verify folders are 7 days apart (weekly recurring)
            first_date = folders[0]['start_datetime']
            second_date = folders[1]['start_datetime']
            assert (second_date - first_date).days == 7

    def test_add_every_monthly_date_pattern(self):
        """Test creating recurring monthly date folders."""
        folder = InMemoryDateFolder()
        start_date = datetime.datetime(2025, 8, 18)
        
        # Add next 3 occurrences of February 2nd
        result = folder.add_every("feb_02", start_date=start_date, count=3)
        
        folders = folder.list_folders()
        assert len(folders) == 3
        
        # Should create folders for Feb 2nd in consecutive years
        expected_dates = [
            datetime.datetime(2026, 2, 2),   # Next Feb 2nd after start
            datetime.datetime(2027, 2, 2),   # Following year
            datetime.datetime(2028, 2, 2)    # Third year
        ]
        
        for i, expected_date in enumerate(expected_dates):
            expected_name = f"{expected_date.strftime('%Y-%m-%d')}_{expected_date.strftime('%Y-%m-%d')}"
            assert folders[i]['name'] == expected_name

    def test_add_every_monthly_date_abbreviated_months(self):
        """Test monthly patterns with abbreviated month names."""
        folder = InMemoryDateFolder()
        start_date = datetime.datetime(2025, 8, 18)
        
        test_cases = [
            ("jan_01", 1, 1),    # New Year's Day
            ("jul_04", 7, 4),    # Independence Day
            ("dec_25", 12, 25),  # Christmas
            ("mar_17", 3, 17),   # St. Patrick's Day
        ]
        
        for pattern, expected_month, expected_day in test_cases:
            folder_test = InMemoryDateFolder()
            result = folder_test.add_every(pattern, start_date=start_date, count=1)
            
            folders = folder_test.list_folders()
            assert len(folders) == 1
            
            created_date = folders[0]['start_datetime']
            assert created_date.month == expected_month
            assert created_date.day == expected_day

    def test_add_every_monthly_date_full_month_names(self):
        """Test monthly patterns with full month names."""
        folder = InMemoryDateFolder()
        start_date = datetime.datetime(2025, 8, 18)
        
        test_cases = [
            ("february_14", 2, 14),   # Valentine's Day
            ("october_31", 10, 31),   # Halloween
            ("november_24", 11, 24),  # Example Thanksgiving
        ]
        
        for pattern, expected_month, expected_day in test_cases:
            folder_test = InMemoryDateFolder()
            result = folder_test.add_every(pattern, start_date=start_date, count=1)
            
            folders = folder_test.list_folders()
            assert len(folders) == 1
            
            created_date = folders[0]['start_datetime']
            assert created_date.month == expected_month
            assert created_date.day == expected_day

    def test_add_every_time_period_week(self):
        """Test creating weekly period folders."""
        folder = InMemoryDateFolder()
        start_date = datetime.datetime(2025, 8, 18)
        
        result = folder.add_every("week", start_date=start_date, count=4)
        
        folders = folder.list_folders()
        assert len(folders) == 4
        
        # Each folder should represent a week (7-day period)
        for i, folder_info in enumerate(folders):
            expected_start = start_date + datetime.timedelta(weeks=i)
            expected_end = expected_start + datetime.timedelta(days=6, hours=23, minutes=59, seconds=59)
            
            assert folder_info['start_datetime'].date() == expected_start.date()
            assert folder_info['end_datetime'].date() == expected_end.date()

    def test_add_every_time_period_month(self):
        """Test creating monthly period folders."""
        folder = InMemoryDateFolder()
        start_date = datetime.datetime(2025, 8, 1)  # Start of month for clean test
        
        result = folder.add_every("month", start_date=start_date, count=3)
        
        folders = folder.list_folders()
        assert len(folders) == 3
        
        # Should create month-range folders
        expected_months = [
            (2025, 8),   # August 2025
            (2025, 9),   # September 2025
            (2025, 10),  # October 2025
        ]
        
        for i, (expected_year, expected_month) in enumerate(expected_months):
            folder_info = folders[i]
            assert folder_info['start_datetime'].year == expected_year
            assert folder_info['start_datetime'].month == expected_month
            assert folder_info['start_datetime'].day == 1

    def test_add_every_time_period_quarter(self):
        """Test creating quarterly period folders."""
        folder = InMemoryDateFolder()
        start_date = datetime.datetime(2025, 7, 1)  # Q3 start
        
        result = folder.add_every("quarter", start_date=start_date, count=2)
        
        folders = folder.list_folders()
        assert len(folders) == 2
        
        # First quarter should be Q3 2025 (July-September)
        first_quarter = folders[0]
        assert first_quarter['start_datetime'] == datetime.datetime(2025, 7, 1)
        assert first_quarter['end_datetime'].month == 9
        
        # Second quarter should be Q4 2025 (October-December)
        second_quarter = folders[1]
        assert second_quarter['start_datetime'] == datetime.datetime(2025, 10, 1)
        assert second_quarter['end_datetime'].month == 12

    def test_add_every_time_period_year(self):
        """Test creating yearly period folders."""
        folder = InMemoryDateFolder()
        start_date = datetime.datetime(2025, 1, 1)
        
        result = folder.add_every("year", start_date=start_date, count=3)
        
        folders = folder.list_folders()
        assert len(folders) == 3
        
        # Should create year-range folders
        for i, folder_info in enumerate(folders):
            expected_year = 2025 + i
            assert folder_info['start_datetime'].year == expected_year
            assert folder_info['start_datetime'] == datetime.datetime(expected_year, 1, 1)
            assert folder_info['end_datetime'].year == expected_year

    def test_add_every_default_parameters(self):
        """Test add_every with default parameters."""
        folder = InMemoryDateFolder()
        
        # Should use current date as start_date when not specified
        result = folder.add_every("week", count=2)
        
        folders = folder.list_folders()
        assert len(folders) == 2

    def test_add_every_weekend_pattern(self):
        """Test creating weekend folders."""
        folder = InMemoryDateFolder()
        start_date = datetime.datetime(2025, 8, 18)  # Monday
        
        result = folder.add_every("weekend", start_date=start_date, count=3)
        
        folders = folder.list_folders()
        assert len(folders) == 3
        
        # Each weekend should be Saturday-Sunday
        for folder_info in folders:
            start_day = folder_info['start_datetime'].weekday()  # 0=Monday, 6=Sunday
            end_day = folder_info['end_datetime'].weekday()
            
            assert start_day == 5  # Saturday
            assert end_day == 6    # Sunday

    def test_add_every_workweek_pattern(self):
        """Test creating workweek folders (Monday-Friday)."""
        folder = InMemoryDateFolder()
        start_date = datetime.datetime(2025, 8, 18)  # Monday
        
        result = folder.add_every("workweek", start_date=start_date, count=2)
        
        folders = folder.list_folders()
        assert len(folders) == 2
        
        # Each workweek should be Monday-Friday
        for folder_info in folders:
            start_day = folder_info['start_datetime'].weekday()  # 0=Monday
            end_day = folder_info['end_datetime'].weekday()      # 4=Friday
            
            assert start_day == 0  # Monday
            assert end_day == 4    # Friday

    def test_add_every_invalid_pattern(self):
        """Test add_every with invalid patterns."""
        folder = InMemoryDateFolder()
        
        invalid_patterns = [
            "invalid_weekday",
            "every_invalidday",
            "feb_32",           # Invalid day
            "invalid_month_01", # Invalid month
            "unknown_period",
        ]
        
        for pattern in invalid_patterns:
            with pytest.raises(ValueError, match=f"Invalid pattern: {pattern}"):
                folder.add_every(pattern, count=1)

    def test_add_every_edge_cases(self):
        """Test edge cases for add_every method."""
        folder = InMemoryDateFolder()
        
        # Test with count=0
        result = folder.add_every("tuesday", count=0)
        folders = folder.list_folders()
        assert len(folders) == 0
        
        # Test with count=1
        result = folder.add_every("month", count=1)
        folders = folder.list_folders()
        assert len(folders) == 1

    def test_add_every_return_values(self):
        """Test return values of add_every method."""
        folder = InMemoryDateFolder()
        
        # Single occurrence should return string
        result = folder.add_every("month", count=1)
        assert isinstance(result, str)
        
        # Multiple occurrences should return list
        folder_multi = InMemoryDateFolder()
        result_multi = folder_multi.add_every("tuesday", count=3)
        assert isinstance(result_multi, list)
        assert len(result_multi) == 3
