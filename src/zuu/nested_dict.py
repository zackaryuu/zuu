

def flatten_dict(dct : dict, sep : str = ".", maxDepth : int = -1) -> dict:
    """
    Flattens a nested dictionary into a single-level dictionary with keys as paths.
    
    Args:
        dct (dict): The input dictionary to flatten.
        sep (str): Separator for key paths (default '.').
        maxDepth (int): Maximum depth to flatten. -1 means no limit.
    
    Returns:
        dict: Flattened dictionary with keys as paths.
    """
    def _flatten(d, parent_key='', depth=0):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict) and (maxDepth == -1 or depth < maxDepth):
                items.extend(_flatten(v, new_key, depth + 1).items())
            else:
                items.append((new_key, v))
        return dict(items)

    return _flatten(dct)
    
def unflatten_dict(dct : dict, sep : str = ".") -> dict:
    """
    Unflattens a dictionary with keys as paths into a nested dictionary.
    
    Args:
        dct (dict): The input dictionary to unflatten.
        sep (str): Separator used in key paths (default '.').
    
    Returns:
        dict: Nested dictionary reconstructed from the flattened keys.
    """
    result = {}
    for key, value in dct.items():
        parts = key.split(sep)
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return result

def is_nested_dict(dct : dict) -> bool:
    """
    Checks if a dictionary is nested (contains other dictionaries).
    
    Args:
        dct (dict): The dictionary to check.
    
    Returns:
        bool: True if the dictionary is nested, False otherwise.
    """
    return any(isinstance(v, dict) for v in dct.values())