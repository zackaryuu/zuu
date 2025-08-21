

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


def compute_nested(keys : list, *dicts : list[(dict, int)], sep : str = ".", keys_weight = 10, maxlv = -1):
    """
    Computes a nested structure by grouping keys based on supplementary dictionaries,
    removing repeated tokens based on weights.
    
    Args:
        keys (list): List of keys to process
        *dicts: Variable number of tuples (dict, weight) where dict maps keys to group values
        sep (str): Separator for nested paths (default '.')
        keys_weight (int): Weight for the original keys (default 10)
        maxlv (int): Maximum nesting level. -1 means no limit (default -1)
    
    Returns:
        dict: Nested dictionary structure with grouped keys
    """
    if not isinstance(keys, list):
        raise TypeError("keys must be a list")
    
    for d in dicts:
        if not isinstance(d, tuple) or len(d) != 2 or not isinstance(d[0], dict) or not isinstance(d[1], int):
            raise TypeError("Each dict must be a tuple of (dict, int)")
        
        # check if all keys exist in the dictionary
        dict_keys = set(d[0].keys())
        keys_set = set(keys)
        if not keys_set.issubset(dict_keys):
            missing_keys = keys_set - dict_keys
            raise ValueError(f"Dictionary missing keys: {missing_keys}")
    
    def _split_camel_case(s):
        """Split camelCase string into tokens"""
        import re
        return re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', s)
    
    def _remove_common_tokens(key_tokens, group_tokens, keys_weight, group_weight):
        """Remove common tokens based on weight priority"""
        key_tokens_lower = [t.lower() for t in key_tokens]
        group_tokens_lower = [t.lower() for t in group_tokens]
        
        # Find common tokens
        common_tokens = set(key_tokens_lower) & set(group_tokens_lower)
        
        result_tokens = []
        for token in key_tokens:
            token_lower = token.lower()
            if token_lower in common_tokens:
                # Keep token from source with higher weight
                if keys_weight > group_weight:
                    result_tokens.append(token)
                # If group weight is higher or equal, skip this token (remove it)
            else:
                # Token not common, keep it
                result_tokens.append(token)
        
        return result_tokens
    
    # Process each key
    result = {}
    
    for key in keys:
        key_tokens = _split_camel_case(key)
        
        # Collect all groups from all supplementary dicts with their weights
        groups_data = []
        
        for supp_dict, weight in dicts:
            if key in supp_dict:
                group_name = supp_dict[key]
                group_tokens = _split_camel_case(group_name)
                groups_data.append((group_name, group_tokens, weight))
        
        if not groups_data:
            # No group found, skip this key or use key as its own group
            if maxlv == 0:
                result[key] = key
            continue
        
        # Sort groups by weight (descending) to prioritize higher weights
        groups_data.sort(key=lambda x: x[2], reverse=True)
        
        # Start with the original key tokens
        current_tokens = key_tokens[:]
        path_components = []
        
        # Process each group level (respecting maxlv)
        for level, (group_name, group_tokens, group_weight) in enumerate(groups_data):
            if maxlv != -1 and level >= maxlv:
                break
                
            # Remove common tokens between current tokens and this group
            remaining_tokens = _remove_common_tokens(current_tokens, group_tokens, keys_weight, group_weight)
            
            # Add group to path
            path_components.append(group_name)
            
            # Update current tokens for next iteration
            current_tokens = remaining_tokens
        
        # Create final key from remaining tokens
        if current_tokens:
            final_key = current_tokens[0].lower() + ''.join(t.capitalize() for t in current_tokens[1:])
        else:
            # If no tokens remain, use original key
            final_key = key
        
        # Build nested structure
        current_dict = result
        for component in path_components:
            if component not in current_dict:
                current_dict[component] = {}
            current_dict = current_dict[component]
        
        current_dict[final_key] = key
    
    return result