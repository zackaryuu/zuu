
def simple_match(pattern : str, value : str) -> bool:
    """
    Matches a string against a pattern with at most one '*' wildcard.
    - If no '*', checks for exact match.
    - If '*' at start, checks if value ends with the rest.
    - If '*' at end, checks if value starts with the rest.
    - If '*' in middle, checks both start and end.
    Raises ValueError if more than one '*' is present.
    Args:
        pattern (str): Pattern string, may contain one '*'.
        value (str): Value to match against pattern.
    Returns:
        bool: True if value matches pattern, False otherwise.
    """
    count = pattern.count("*")
    if count == 0:
        return pattern == value
    
    if count > 1:
        raise ValueError("Pattern can only contain one '*' wildcard.")
    index = pattern.find("*")
    if index == 0:
        return value.endswith(pattern[1:])
    elif index == len(pattern) - 1:
        return value.startswith(pattern[:-1])
    else:
        return value.startswith(pattern[:index]) and value.endswith(pattern[index + 1:])
    
def rreplace(s: str, old: str, new: str, occurrence):
    """
    Replaces the last occurrence of a substring in a string with a new substring.

    Args:
        s (str): The input string.
        old (str): The substring to be replaced.
        new (str): The new substring to replace the old substring.
        occurrence (int): The number of occurrences of the old substring to replace.

    Returns:
        str: The modified string with the last occurrence of the old substring replaced by the new substring.

    Raises:
        None

    Example:
        >>> rreplace("Hello, world!", "world", "codeium", 1)
        'Hello, codeium!'
    """
    if occurrence <= 0:
        return s

    parts = s.rsplit(old, occurrence)
    return new.join(parts)


def simple_matches(values : list[str], patterns : list[str], useCache : bool = True) -> bool:
    """
    Checks if any value in a list matches any pattern in another list using simple_match.
    Caches results for efficiency if useCache is True.
    
    Args:
        values (list[str]): List of strings to check.
        patterns (list[str]): List of patterns to match against.
        useCache (bool): Whether to cache results for efficiency.
        
    Returns:
        bool: True if any value matches any pattern, False otherwise.
    """
    cache = {}
    
    for value in values:
        for pattern in patterns:
            key = (value, pattern)
            if useCache and key in cache:
                if cache[key]:
                    return True
            else:
                match_result = simple_match(pattern, value)
                if useCache:
                    cache[key] = match_result
                if match_result:
                    return True
    return False