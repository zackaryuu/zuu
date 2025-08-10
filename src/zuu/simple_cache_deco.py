
"""
Module: simple_cache_deco
-------------------------
Provides a simple caching decorator for Python functions.

Features:
- Decorator to cache function results based on input arguments.
- Useful for optimizing expensive or frequently called functions.
- Supports basic cache invalidation and customization.

Usage:
    @simple_cache_deco
    def expensive_function(args):
        ...

Author: zackaryuu
License: See LICENSE in project root.
"""

_funcCacheMap = {}

def cache_func(func, *args, **kwargs):
    key = (func, args, frozenset(kwargs.items()))
    
    if key not in _funcCacheMap:
        _funcCacheMap[key] = func(*args, **kwargs)
    
    return _funcCacheMap[key]
    
