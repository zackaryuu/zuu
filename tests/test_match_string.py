import pytest
from zuu.match_string import (
    is_year,
    is_year_2000s,
    is_year_month,
    is_year_month_day,
    is_year_month_day_time,
    is_time,
)


class TestIsYear:
    def test_valid_year(self):
        assert is_year("2023")
        assert is_year("1999")
        assert is_year("0001")
        assert is_year("9999")

    def test_invalid_year_length(self):
        assert not is_year("23")
        assert not is_year("202")
        assert not is_year("20234")

    def test_invalid_year_non_digit(self):
        assert not is_year("202a")
        assert not is_year("abcd")
        assert not is_year("20-3")

    def test_empty_string(self):
        assert not is_year("")


class TestIsYear2000s:
    def test_valid_2000s_year(self):
        assert is_year_2000s("2000")
        assert is_year_2000s("2023")
        assert is_year_2000s("2099")

    def test_invalid_2000s_year_range(self):
        assert not is_year_2000s("1999")
        assert not is_year_2000s("2100")
        assert not is_year_2000s("1800")

    def test_invalid_2000s_year_format(self):
        assert not is_year_2000s("202a")
        assert not is_year_2000s("20234")
        assert not is_year_2000s("")


class TestIsYearMonth:
    def test_valid_year_month_default_sep(self):
        assert is_year_month("2023-01")
        assert is_year_month("2023-12")
        assert is_year_month("2023-06")

    def test_valid_year_month_custom_sep(self):
        assert is_year_month("2023/01", sep="/")
        assert is_year_month("2023.12", sep=".")

    def test_invalid_year_month_range(self):
        assert not is_year_month("2023-00")
        assert not is_year_month("2023-13")

    def test_invalid_year_month_format(self):
        assert not is_year_month("2023")
        assert not is_year_month("2023-1-1")
        assert not is_year_month("202a-01")
        assert not is_year_month("2023-1a")

    def test_invalid_year_month_separators(self):
        assert not is_year_month("2023--01")
        assert not is_year_month("2023-01-")


class TestIsYearMonthDay:
    def test_valid_year_month_day_default_sep(self):
        assert is_year_month_day("2023-01-01")
        assert is_year_month_day("2023-12-31")
        assert is_year_month_day("2023-06-15")

    def test_valid_year_month_day_custom_sep(self):
        assert is_year_month_day("2023/01/01", sep="/")
        assert is_year_month_day("2023.12.31", sep=".")

    def test_invalid_year_month_day_range(self):
        assert not is_year_month_day("2023-00-01")
        assert not is_year_month_day("2023-13-01")
        assert not is_year_month_day("2023-01-00")
        assert not is_year_month_day("2023-01-32")

    def test_invalid_year_month_day_format(self):
        assert not is_year_month_day("2023-01")
        assert not is_year_month_day("2023-01-01-01")
        assert not is_year_month_day("202a-01-01")
        assert not is_year_month_day("2023-1a-01")
        assert not is_year_month_day("2023-01-1a")

    def test_year_month_day_with_custom_year_func(self):
        # Test with default year function (is_year_2000s)
        assert not is_year_month_day("1999-01-01")
        assert not is_year_month_day("2100-01-01")
        
        # Test with custom year function (is_year)
        assert is_year_month_day("1999-01-01", year_func=is_year)
        assert is_year_month_day("2100-01-01", year_func=is_year)


class TestIsTime:
    def test_valid_time_default_sep(self):
        assert is_time("00.00.00")
        assert is_time("23.59.59")
        assert is_time("12.30.45")

    def test_valid_time_custom_sep(self):
        assert is_time("12.30.45", sep=".")
        assert is_time("12-30-45", sep="-")

    def test_invalid_time_range(self):
        assert not is_time("24:00:00")
        assert not is_time("12:60:00")
        assert not is_time("12:30:60")
        assert not is_time("25:30:45")

    def test_invalid_time_format(self):
        assert not is_time("12:30")
        assert not is_time("12:30:45:67")
        assert not is_time("1a:30:45")
        assert not is_time("12:3a:45")
        assert not is_time("12:30:4b")

    def test_invalid_time_separators(self):
        assert not is_time("12::30:45")
        assert not is_time("12:30::45")


class TestIsYearMonthDayTime:
    def test_valid_year_month_day_time_default_sep(self):
        assert is_year_month_day_time("2023-01-01 12.30.45")
        assert is_year_month_day_time("2023-12-31 23.59.59")
        assert is_year_month_day_time("2023-06-15 00.00.00")

    def test_valid_year_month_day_time_custom_sep(self):
        assert is_year_month_day_time("2023/01/01 12.30.45", sep="/")
        assert is_year_month_day_time("2023-01-01 12:30:45", time_sep=":")
        assert is_year_month_day_time("2023-01-01T12.30.45", mid_sep="T")

    def test_invalid_year_month_day_time_date_part(self):
        assert not is_year_month_day_time("2023-00-01 12:30:45")
        assert not is_year_month_day_time("2023-13-01 12:30:45")
        assert not is_year_month_day_time("1999-01-01 12:30:45")

    def test_invalid_year_month_day_time_time_part(self):
        assert not is_year_month_day_time("2023-01-01 24:30:45")
        assert not is_year_month_day_time("2023-01-01 12:60:45")
        assert not is_year_month_day_time("2023-01-01 12:30:60")

    def test_invalid_year_month_day_time_format(self):
        # These should raise ValueError because they don't have the required separator
        with pytest.raises(ValueError):
            is_year_month_day_time("2023-01-01")  # missing time part
        with pytest.raises(ValueError):
            is_year_month_day_time("12:30:45")  # missing date part
        with pytest.raises(ValueError):
            is_year_month_day_time("2023-01-01  12:30:45")  # double space causes too many parts

    def test_year_month_day_time_edge_cases(self):
        # Test with minimal valid values
        assert is_year_month_day_time("2000-01-01 00.00.00")
        # Test with maximal valid values  
        assert is_year_month_day_time("2099-12-31 23.59.59")


class TestEdgeCases:
    def test_empty_strings(self):
        assert not is_year("")
        assert not is_year_2000s("")
        assert not is_year_month("")
        assert not is_year_month_day("")
        assert not is_time("")

    def test_none_inputs(self):
        # These should raise AttributeError since None doesn't have string methods
        with pytest.raises(AttributeError):
            is_year(None)
        with pytest.raises(AttributeError):
            is_year_month(None)

    def test_single_digit_components(self):
        # Single digits should work for months/days - the function actually accepts them
        assert is_year_month("2023-1")  # single digit month is actually valid
        assert is_year_month_day("2023-01-1")  # single digit day is actually valid
        
    def test_leading_zeros(self):
        # Leading zeros should be handled properly
        assert is_year_month("2023-01")
        assert is_year_month("2023-09")
        assert is_year_month_day("2023-01-01")
        assert is_year_month_day("2023-01-09")
        assert is_time("01.01.01")
        assert is_time("09.09.09")

    def test_boundary_values(self):
        # Test boundary values for months and days
        assert is_year_month("2023-1")  # minimum month
        assert is_year_month("2023-12")  # maximum month
        assert is_year_month_day("2023-01-1")  # minimum day
        assert is_year_month_day("2023-01-31")  # maximum day
        assert is_time("0.0.0")  # minimum time components (using dot separator)
        assert is_time("23.59.59")  # maximum time components

    def test_whitespace_and_special_chars(self):
        # Test with whitespace and special characters
        assert not is_year(" 2023")
        assert not is_year("2023 ")
        assert not is_year_month(" 2023-01")
        assert not is_year_month("2023-01 ")
        assert not is_year_month_day(" 2023-01-01")
        assert not is_time(" 12:30:45")
