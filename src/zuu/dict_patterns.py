
import typing

from zuu.simple_string import simple_match


def extract_nested_keys(dct : dict | list, separator: str = '/', current : str = ''):
    """
    Recursively yields all nested keys in a dictionary or list structure as path strings.
    Args:
        dct (dict | list): The input dictionary or list to extract keys from.
        separator (str): Separator used in key paths (default '/').
        current (str): Current path prefix (used internally).
    Yields:
        str: Path string for each leaf value in the structure.
    Note:
        This function only yields keys, not values. For key-value pairs, use iter_nested_keys.
    """
    method = _extract_dict if isinstance(dct, dict) else _extract_list
    for key, _ in method(dct, separator, current):
        yield key

def _extract_dict(dct : dict, separator : str, current : str, exclusion : list[str] = None):
    """
    Helper to recursively extract keys and values from a dictionary.
    Args:
        dct (dict): The dictionary to process.
        separator (str): Separator for key paths.
        current (str): Current path prefix.
        exclusion (list[str], optional): List of mask patterns to exclude certain keys (uses simple_match).
    Yields:
        tuple: (key_path, value) for each leaf value.
    """
    for k, v in dct.items():
        new_key = f"{current}{separator}{k}" if current else k
        if isinstance(v, dict):
            yield from _extract_dict(v, separator, new_key, exclusion)
        elif isinstance(v, list):
            yield from _extract_list(v, separator, new_key, exclusion)
        else:
            if exclusion and any(simple_match(mask, new_key) for mask in exclusion):
                continue
            yield new_key, v

def _extract_list(dct : list, separator : str, current : str, exclusion : list[str] = None):
    """
    Helper to recursively extract keys and values from a list.
    Args:
        dct (list): The list to process.
        separator (str): Separator for key paths.
        current (str): Current path prefix.
        exclusion (list[str], optional): List of mask patterns to exclude certain keys (uses simple_match).
    Yields:
        tuple: (key_path, value) for each leaf value.
    """
    for i, v in enumerate(dct):
        new_key = f"{current}{separator}{i}" if current else str(i)
        if isinstance(v, dict):
            yield from _extract_dict(v, separator, new_key, exclusion)
        elif isinstance(v, list):
            yield from _extract_list(v, separator, new_key, exclusion)
        else:
            if exclusion and any(simple_match(mask, new_key) for mask in exclusion):
                continue
            yield new_key, v


def iter_nested_keys(dct : dict | list, separator: str = '/', masks :list[str] = None, iter_type : typing.Literal["key", "value", "both"] = "key"):
    """
    Iterates over all nested keys and/or values in a dictionary or list structure.
    Args:
        dct (dict | list): The input dictionary or list to iterate.
        separator (str): Separator used in key paths (default '/').
        masks (list[str], optional): List of mask patterns to exclude certain keys (uses simple_match).
        iter_type (str): What to yield: 'key' (default), 'value', or 'both'.
            - 'key': yields key paths only
            - 'value': yields values only
            - 'both': yields (key, value) tuples
    Yields:
        str, value, or tuple: Depending on iter_type.
    Raises:
        ValueError: If iter_type is not one of 'key', 'value', or 'both'.
    """
    def _internal():
        current = ''
        if isinstance(dct, dict):
            yield from _extract_dict(dct, separator, current, masks)
        elif isinstance(dct, list):
            yield from _extract_list(dct, separator, current, masks)

    for key in _internal():
        if iter_type == "key":
            yield key[0]
        elif iter_type == "value":
            yield key[1]
        elif iter_type == "both":
            yield key
        else:
            raise ValueError("iter_type must be 'key', 'value', or 'both'.")
