"""
Simple Flask rate limiting handler.

Provides a class-based approach to rate limiting Flask routes with per-method tracking.
"""

import time
import re
from functools import wraps
from dataclasses import dataclass
from .flask import get_client_ip

@dataclass
class SimpleRateLimit:
    """
    A simple rate limiting handler for Flask applications.
    
    Provides per-method rate limiting with optional exposure of internal tracking data.
    """
    default_max_requests: int = 60
    default_per: str = "1 minute"
    method_limits: dict = None
    tracking_dict: dict = None
    rate_limit_handler: callable = None
    
    def __post_init__(self):
        """Initialize after dataclass creation."""
        if self.method_limits is None:
            self.method_limits = {}
        
        # Internal tracking - method_name -> client_ip -> [timestamps]
        self._internal_tracking = {}
        
        # Optional external tracking exposure
        if self.tracking_dict is not None:
            self.tracking_dict.update(self._internal_tracking)
    
    def _parse_time_period(self, per_string: str) -> int:
        """
        Parse time period string like '5 minutes', '30 seconds', '2 hours' into seconds.
        
        Args:
            per_string: Time period string
            
        Returns:
            Number of seconds
        """
        # Extract number and unit
        match = re.match(r'(\d+)\s*(second|minute|hour|day)s?', per_string.lower())
        if not match:
            raise ValueError(f"Invalid time period format: {per_string}")
        
        number, unit = match.groups()
        number = int(number)
        
        # Convert to seconds
        multipliers = {
            'second': 1,
            'minute': 60,
            'hour': 3600,
            'day': 86400
        }
        
        return number * multipliers[unit]
    
    def limit(self, method_name, max_requests=None, per=None):
        """
        Decorator factory for rate limiting a specific method.
        
        Args:
            method_name: Name of the method/endpoint to rate limit
            max_requests: Optional override for max requests
            per: Optional override for time period (e.g., "5 minutes", "30 seconds")
            
        Returns:
            Decorator function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Determine the rate limit for this method
                if method_name in self.method_limits:
                    method_config = self.method_limits[method_name]
                    method_max_requests = max_requests or method_config.get('max_requests', self.default_max_requests)
                    method_per = per or method_config.get('per', self.default_per)
                else:
                    method_max_requests = max_requests or self.default_max_requests
                    method_per = per or self.default_per
                
                window_seconds = self._parse_time_period(method_per)
                client_ip = get_client_ip()
                
                if self._is_rate_limited(method_name, client_ip, method_max_requests, window_seconds):
                    # Use custom handler if provided, otherwise return None
                    if self.rate_limit_handler:
                        return self.rate_limit_handler(method_name, method_max_requests, method_per, client_ip)
                    else:
                        return None
                
                # Record the request
                self._record_request(method_name, client_ip)
                
                # Update external tracking if provided
                if self.tracking_dict is not None:
                    self.tracking_dict.update(self._internal_tracking)
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def _is_rate_limited(self, method_name, client_ip, max_requests, window_seconds):
        """
        Check if the client has exceeded the rate limit for the given method.
        
        Args:
            method_name: Name of the method being accessed
            client_ip: Client's IP address
            max_requests: Maximum requests allowed in the time window
            window_seconds: Time window in seconds
            
        Returns:
            True if rate limited, False otherwise
        """
        current_time = time.time()
        
        # Initialize tracking for method if not exists
        if method_name not in self._internal_tracking:
            self._internal_tracking[method_name] = {}
        
        # Initialize tracking for client if not exists
        if client_ip not in self._internal_tracking[method_name]:
            self._internal_tracking[method_name][client_ip] = []
        
        # Get request timestamps for this client and method
        timestamps = self._internal_tracking[method_name][client_ip]
        
        # Remove old timestamps outside the window
        cutoff_time = current_time - window_seconds
        timestamps[:] = [ts for ts in timestamps if ts > cutoff_time]
        
        # Check if limit exceeded
        return len(timestamps) >= max_requests
    
    def _record_request(self, method_name, client_ip):
        """
        Record a new request timestamp.
        
        Args:
            method_name: Name of the method being accessed
            client_ip: Client's IP address
        """
        current_time = time.time()
        self._internal_tracking[method_name][client_ip].append(current_time)
    
    def get_stats(self, method_name=None):
        """
        Get rate limiting statistics.
        
        Args:
            method_name: Optional specific method to get stats for
            
        Returns:
            Dictionary containing rate limiting statistics
        """
        if method_name:
            if method_name in self._internal_tracking:
                method_data = self._internal_tracking[method_name]
                return {
                    'method': method_name,
                    'clients': len(method_data),
                    'total_requests': sum(len(timestamps) for timestamps in method_data.values())
                }
            else:
                return {'method': method_name, 'clients': 0, 'total_requests': 0}
        else:
            # Return stats for all methods
            stats = {}
            for method, method_data in self._internal_tracking.items():
                stats[method] = {
                    'clients': len(method_data),
                    'total_requests': sum(len(timestamps) for timestamps in method_data.values())
                }
            return stats
    
    def reset_limits(self, method_name=None, client_ip=None):
        """
        Reset rate limits for specified method/client or all.
        
        Args:
            method_name: Optional specific method to reset
            client_ip: Optional specific client IP to reset
        """
        if method_name and client_ip:
            # Reset specific client for specific method
            if method_name in self._internal_tracking and client_ip in self._internal_tracking[method_name]:
                self._internal_tracking[method_name][client_ip] = []
        elif method_name:
            # Reset all clients for specific method
            if method_name in self._internal_tracking:
                self._internal_tracking[method_name] = {}
        else:
            # Reset everything
            self._internal_tracking = {}
        
        # Update external tracking if provided
        if self.tracking_dict is not None:
            self.tracking_dict.clear()
            self.tracking_dict.update(self._internal_tracking)
