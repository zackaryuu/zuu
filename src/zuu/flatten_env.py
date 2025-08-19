"""
Module for loading and managing environment variables and configuration from multiple sources.

This module provides utilities to load configuration from .env files, system arguments,
and custom dictionaries, with support for flattening and unflattening nested structures.
"""
import os

from zuu.simple_dict import deep_set
from .nested_dict import is_nested_dict, unflatten_dict


def load_env(unflatten: bool = True):
    """
    Load environment variables from a .env file.
    
    Args:
        unflatten (bool): If True, converts flattened keys (e.g., 'db.host') 
                         to nested dictionary structure. Default is True.
    
    Returns:
        dict: Dictionary containing environment variables. Nested if unflatten=True,
              flat if unflatten=False.
    
    Raises:
        AssertionError: If the .env file does not exist.
    
    Example:
        # .env file contains:
        # DB_HOST=localhost
        # DB_PORT=5432
        # API.KEY=secret123
        
        config = load_env(unflatten=True)
        # Returns: {'DB_HOST': 'localhost', 'DB_PORT': '5432', 'API': {'KEY': 'secret123'}}
    """
    assert os.path.exists(".env"), "The .env file does not exist."

    with open(".env", "r") as f:
        lines = f.readlines()

    parsed = {}

    for line in lines:
        key, value = line.strip().split("=", 1)
        parsed[key] = value

    if unflatten:
        return unflatten_dict(parsed)

    return parsed


def load_sys_args(unflatten: bool = True):
    """
    Load configuration from command line arguments.
    
    Args:
        unflatten (bool): If True, converts flattened keys (e.g., 'db.host') 
                         to nested dictionary structure. Default is True.
    
    Returns:
        dict: Dictionary containing parsed command line arguments. Nested if unflatten=True,
              flat if unflatten=False.
    
    Raises:
        AssertionError: If no system arguments are provided.
    
    Example:
        # Command: python script.py db.host=localhost api.key=secret
        config = load_sys_args(unflatten=True)
        # Returns: {'db': {'host': 'localhost'}, 'api': {'key': 'secret'}}
    """
    import sys

    assert len(sys.argv) > 1, "No system arguments provided."

    parsed = dict(arg.split("=") for arg in sys.argv[1:])
    if unflatten:
        return unflatten_dict(parsed)
    return parsed


def deep_overwrite_with_flatten_dict(target: dict, source: dict):
    """
    Deep merge a flattened dictionary into a target dictionary.
    
    Uses dot notation to set nested values in the target dictionary.
    
    Args:
        target (dict): The target dictionary to modify in place.
        source (dict): The source dictionary with potentially flattened keys.
    
    Example:
        target = {'db': {'port': 3306}}
        source = {'db.host': 'localhost', 'api.key': 'secret'}
        deep_overwrite_with_flatten_dict(target, source)
        # target becomes: {'db': {'port': 3306, 'host': 'localhost'}, 'api': {'key': 'secret'}}
    """
    for k, v in source.items():
        deep_set(target, k, v, separator=".")


def load_multi_env(
    env_file: bool = True,
    sys_args: bool = False,
    *args,
    priority=["env_file", "args", "sys_args"],
    check_nested: bool = False
):
    """
    Load configuration from multiple sources with configurable priority.
    
    Merges configuration from .env files, command line arguments, and custom dictionaries
    according to the specified priority order. Later sources in the priority list
    will override values from earlier sources.
    
    Args:
        env_file (bool): Whether to load from .env file. Default is True.
        sys_args (bool): Whether to load from command line arguments. Default is False.
        *args: Additional dictionaries to merge into the configuration.
        priority (list): Order of source priority. Sources later in the list override earlier ones.
                        Valid values: "env_file", "args", "sys_args". 
                        Default is ["env_file", "args", "sys_args"].
        check_nested (bool): If True, check if args dictionaries are already nested before unflattening.
                            Default is False.
    
    Returns:
        dict: Merged configuration dictionary with nested structure.
    
    Example:
        # .env file: DB_HOST=localhost
        # Command line: python script.py db.port=5432
        # Custom args: [{'api.key': 'secret'}]
        
        config = load_multi_env(
            env_file=True, 
            sys_args=True, 
            {'api.timeout': '30'}, 
            priority=["env_file", "sys_args", "args"]
        )
        # Returns merged configuration with sys_args overriding env_file, 
        # and args overriding both
    """
    env = {}
    for p in priority:
        if p == "env_file" and env_file and os.path.exists(".env"):
            deep_overwrite_with_flatten_dict(env, load_env(unflatten=False))
        elif p == "sys_args" and sys_args and len(__import__('sys').argv) > 1:
            deep_overwrite_with_flatten_dict(env, load_sys_args(unflatten=False))
        elif p == "args" and len(args) > 0:
            for arg in args:
                if check_nested and is_nested_dict(arg):
                    # If arg is already nested, flatten it first for consistent processing
                    from .nested_dict import flatten_dict
                    deep_overwrite_with_flatten_dict(env, flatten_dict(arg))
                else:
                    # Assume arg is a flat dict that might need unflattening
                    deep_overwrite_with_flatten_dict(env, arg)
    
    return env
