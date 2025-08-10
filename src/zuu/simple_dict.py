
import typing


_throw_error = object()

def deep_get(dct, key : str, separator: str = '/', default = _throw_error):
    """
    Recursively retrieves a value from a nested dict or list using a key path.
    Args:
        dct: The dictionary or list to search.
        key: The key path string (e.g., 'a/b/0/c'), using '/' as the separator by default.
        separator: Separator for splitting the key path (default: '/').
        default: Value to return if key is not found (raises KeyError if not set).
    Returns:
        The value at the specified key path, or default if not found.
    Raises:
        KeyError: If the key path does not exist and no default is provided.
    """
    keys = key.split(separator)
    for k in keys:
        if isinstance(dct, dict) and k in dct:
            dct = dct[k]
        elif isinstance(dct, list) and k.isdigit() and 0 <= int(k) < len(dct):
            dct = dct[int(k)]
        else:
            if default is _throw_error:
                raise KeyError(f"Key '{key}' not found in the dictionary.")
            return default
    return dct

def deep_set(dct, key : str, value, separator: str = '/'):
    """
    Recursively sets a value in a nested dict or list using a key path.
    Args:
        dct: The dictionary or list to modify.
        key: The key path string (e.g., 'a/b/0/c'), using '/' as the separator by default.
        separator: Separator for splitting the key path (default: '/').
        value: The value to set at the specified key path.
    Raises:
        KeyError: If the key path is invalid.
        IndexError: If a list index is out of range.
    """
    keys = key.split(separator)
    for k in keys[:-1]:
        if isinstance(dct, dict):
            if k not in dct or not isinstance(dct[k], (dict, list)):
                # If next key is digit, create a list, else dict
                if k.isdigit():
                    dct[k] = []
                else:
                    dct[k] = {}
            dct = dct[k]
        elif isinstance(dct, list) and k.isdigit():
            index = int(k)
            if len(dct) <= index:
                raise IndexError(f"Index {index} out of range for list at '{key}'.")
            # If not dict, set to dict
            if not isinstance(dct[index], dict):
                dct[index] = {}
            dct = dct[index]
        else:
            raise KeyError(f"Cannot set value at '{key}': invalid path.")
    if isinstance(dct, dict):
        dct[keys[-1]] = value
    elif isinstance(dct, list) and keys[-1].isdigit():
        dct[int(keys[-1])] = value
    else:
        raise KeyError(f"Cannot set value at '{key}': invalid path.")

def deep_pop(dct, key: str, separator: str = '/', default=_throw_error):
    """
    Recursively pops a value from a nested dict or list using a key path.
    Args:
        dct: The dictionary or list to modify.
        key: The key path string (e.g., 'a/b/0/c').
        separator: Separator for splitting the key path (default: '/').
        default: Value to return if key is not found (raises KeyError if not set).
    Returns:
        The popped value at the specified key path, or default if not found.
    Raises:
        KeyError: If the key path does not exist and no default is provided.
    """
    keys = key.split(separator)
    for k in keys[:-1]:
        if isinstance(dct, dict) and k in dct:
            dct = dct[k]
        elif isinstance(dct, list) and k.isdigit() and 0 <= int(k) < len(dct):
            dct = dct[int(k)]
        else:
            if default is _throw_error:
                raise KeyError(f"Key '{key}' not found for pop.")
            return default
    last = keys[-1]
    if isinstance(dct, dict):
        if last in dct:
            return dct.pop(last)
        elif default is not _throw_error:
            return default
        else:
            raise KeyError(f"Key '{key}' not found for pop.")
    elif isinstance(dct, list) and last.isdigit() and 0 <= int(last) < len(dct):
        return dct.pop(int(last))
    else:
        if default is not _throw_error:
            return default
        else:
            raise KeyError(f"Key '{key}' not found for pop.")

def deep_setdefault(dct, key: str, default_value, separator: str = '/'):
    """
    Recursively sets a default value in a nested dict or list using a key path.
    Args:
        dct: The dictionary or list to modify.
        key: The key path string (e.g., 'a/b/0/c').
        separator: Separator for splitting the key path (default: '/').
        default_value: The value to set if the key does not exist.
    Returns:
        The value at the specified key path after setdefault.
    """
    keys = key.split(separator)
    for k in keys[:-1]:
        if isinstance(dct, dict):
            if k not in dct or not isinstance(dct[k], (dict, list)):
                if k.isdigit():
                    dct[k] = []
                else:
                    dct[k] = {}
            dct = dct[k]
        elif isinstance(dct, list) and k.isdigit():
            index = int(k)
            if len(dct) <= index:
                raise IndexError(f"Index {index} out of range for list at '{key}'.")
            if not isinstance(dct[index], dict):
                dct[index] = {}
            dct = dct[index]
        else:
            raise KeyError(f"Cannot setdefault at '{key}': invalid path.")
    last = keys[-1]
    if isinstance(dct, dict):
        return dct.setdefault(last, default_value)
    elif isinstance(dct, list) and last.isdigit():
        index = int(last)
        if len(dct) <= index:
            raise IndexError(f"Index {index} out of range for list at '{key}'.")
        if dct[index] is None:
            dct[index] = default_value
        return dct[index]
    else:
        raise KeyError(f"Cannot setdefault at '{key}': invalid path.")

def deep_delete(dct, key: str, separator: str = '/'):
    """
    Recursively deletes a value from a nested dict or list using a key path.
    Args:
        dct: The dictionary or list to modify.
        key: The key path string (e.g., 'a/b/0/c').
        separator: Separator for splitting the key path (default: '/').
    Raises:
        KeyError: If the key path does not exist.
    """
    keys = key.split(separator)
    for k in keys[:-1]:
        if isinstance(dct, dict) and k in dct:
            dct = dct[k]
        elif isinstance(dct, list) and k.isdigit() and 0 <= int(k) < len(dct):
            dct = dct[int(k)]
        else:
            raise KeyError(f"Key '{key}' not found for delete.")
    
    last = keys[-1]
    if isinstance(dct, dict):
        if last in dct:
            del dct[last]
        else:
            raise KeyError(f"Key '{key}' not found for delete.")
    elif isinstance(dct, list) and last.isdigit() and 0 <= int(last) < len(dct):
        del dct[int(last)]
    else:
        raise KeyError(f"Key '{key}' not found for delete.")

def deep_get_2(dct, key : str, separator : str = '/', default = _throw_error):
    """
    Recursively retrieves a value from a nested dict or list of dicts using a key path.
    If a list is encountered, applies the remaining key path to each dict in the list and returns a list of results.
    Does not support numeric indices.
    Args:
        dct: The dictionary or list to search.
        key: The key path string (e.g., 'a/b/c'), using '/' as the separator by default.
        separator: Separator for splitting the key path (default: '/').
        default: Value to return if key is not found (raises KeyError if not set).
    Returns:
        The value at the specified key path, or a list of values if a list is encountered.
    Raises:
        KeyError: If the key path does not exist and no default is provided.
    """
    keys = key.split(separator)
    def _get(obj, keys):
        if not keys:
            return obj
        k = keys[0]
        rest = keys[1:]
        if isinstance(obj, dict):
            if k in obj:
                return _get(obj[k], rest)
            else:
                if default is _throw_error:
                    raise KeyError(f"Key '{key}' not found in the dictionary.")
                return default
        elif isinstance(obj, list):
            results = []
            for item in obj:
                if isinstance(item, dict):
                    val = _get(item, keys)
                    if val is default and default is not _throw_error:
                        results.append(default)
                    elif val is default:
                        # If any mapping is missing and no default, fail the whole function
                        raise KeyError(f"Key '{key}' not found in one or more mappings.")
                    else:
                        results.append(val)
                else:
                    # If any item is not a dict, fail the whole function
                    raise KeyError(f"Key '{key}' not found in one or more mappings.")
            return results
        else:
            if default is _throw_error:
                raise KeyError(f"Key '{key}' not found in the dictionary.")
            return default
    return _get(dct, keys)
    
def merge_dict(
        *dicts, 
        list_merge_method : typing.Literal["extend", "replace", "keep", "merge"] = "extend", 
        dict_merge_method : typing.Literal["replace", "keep", "merge"] = "replace"
    ):
    """
    deep merging, fails when values are of different types
    """
    if len(dicts) == 0:
        return {}
    
    if len(dicts) == 1:
        return dicts[0]
    
    d1 = dicts[0]
    assert isinstance(d1, (dict, list)), "First argument must be a dictionary or list."

    current = 0
    while current < len(dicts) - 1:
        d2 = dicts[current + 1]
        if not isinstance(d2, (dict, list)):
            raise TypeError("All inputs must be dictionaries or lists.")

        if type(d1) is not type(d2):
            raise TypeError("All inputs must be of the same type (dict or list).")

        if isinstance(d1, dict):
            _merge_dict(d1, d2, list_merge_method, dict_merge_method)
        else:
            d1 = _merge_list(d1, d2, list_merge_method, dict_merge_method)

        current += 1

    return d1

def _merge_dict(d1 : dict, d2 : dict, list_merge_method, dict_merge_method):
    """
    Merges two dictionaries recursively.
    """
    for key, value in d2.items():
        if key in d1:
            if isinstance(d1[key], dict) and isinstance(value, dict):
                d1[key] = _merge_dict(d1[key], value, list_merge_method, dict_merge_method)
            elif isinstance(d1[key], list) and isinstance(value, list):
                d1[key] = _merge_list(d1[key], value, list_merge_method, dict_merge_method)
            elif dict_merge_method == "merge":
                # Accumulate all values as a list, regardless of type
                if not isinstance(d1[key], list):
                    d1[key] = [d1[key]]
                d1[key].append(value)
            elif d1[key] is None and dict_merge_method == "replace":
                d1[key] = value
            elif type(d1[key]) is not type(value):
                raise TypeError(f"Type mismatch for key '{key}': {type(d1[key])} vs {type(value)}")
            elif dict_merge_method == "replace":
                d1[key] = value
            elif dict_merge_method == "keep":
                continue
        else:
            d1[key] = value
    return d1

def _merge_list(d1 : list, d2 : list, list_merge_method, dict_merge_method):
    """
    Merges two lists.
    """
    if list_merge_method == "extend":
        return d1 + d2
    elif list_merge_method == "replace":
        return d2
    elif list_merge_method == "keep":
        return d1
    elif list_merge_method == "merge":
        merged = []
        for item1, item2 in zip(d1, d2):
            if isinstance(item1, dict) and isinstance(item2, dict):
                # Merge dicts as a pair, not in-place
                merged.append([item1, item2])
            elif isinstance(item1, list) and isinstance(item2, list):
                merged.append([item1, item2])
            elif type(item1) is not type(item2):
                raise TypeError(f"Type mismatch in list merge: {type(item1)} vs {type(item2)}")
            else:
                merged.append([item1, item2])
        return merged
    else:
        raise ValueError(f"Unknown list merge method: {list_merge_method}")