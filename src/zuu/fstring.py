from string import Formatter


def extract_fstring_keys(string: str):
    """
    Extracts the keys used in a formatted string literal (f-string).

    Args:
        string (str): The formatted string literal.

    Returns:
        list: A list of keys used in the f-string.

    This function takes a formatted string literal (f-string) as input and extracts the keys used in it. It checks if the input is a string and if not, it returns an empty list. If the input is a string, it uses the `Formatter().parse()` method to parse the string and extract the keys. It then returns a list of keys used in the f-string. If any error occurs during the parsing, it returns an empty list.

    Example:
        >>> extract_fstring_keys("Hello, {name}!")
        ['name']
        >>> extract_fstring_keys("The answer is {answer}.")
        ['answer']
        >>> extract_fstring_keys("This is not an f-string.")
        []
    """
    if not isinstance(string, str):
        return []
    try:
        return [x[1] for x in Formatter().parse(string) if x[1] is not None]
    except ValueError:
        return []
