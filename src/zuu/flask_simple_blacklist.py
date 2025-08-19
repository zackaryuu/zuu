"""
Simple Flask IP blacklist handler.

Provides a class-based approach to blocking requests from blacklisted IPs.
"""

from functools import wraps
from dataclasses import dataclass
from flask import request
from .flask import get_client_ip

@dataclass
class SimpleBlacklist:
    """
    A simple IP blacklist handler for Flask applications.
    
    Provides IP-based blocking with customizable blacklist behavior.
    """
    blacklisted_ips: set = None
    blacklist_handler: callable = None
    tracking_dict: dict = None
    max_stored_attempts: int = 1000
    
    def __post_init__(self):
        """Initialize after dataclass creation."""
        if self.blacklisted_ips is None:
            self.blacklisted_ips = set()
        
        # Internal tracking - ip -> [timestamps of blocked attempts]
        self._blocked_attempts = {}
        self._total_stored_attempts = 0
        
        # Optional external tracking exposure
        if self.tracking_dict is not None:
            self.tracking_dict.update(self._blocked_attempts)
    
    def block(self, method_name=None):
        """
        Decorator for blocking requests from blacklisted IPs.
        
        Args:
            method_name: Optional method name for tracking purposes
            
        Returns:
            Decorator function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                client_ip = get_client_ip(request)
                
                if self._is_blacklisted(client_ip):
                    # Record the blocked attempt
                    self._record_blocked_attempt(client_ip, method_name or func.__name__)
                    
                    # Update external tracking if provided
                    if self.tracking_dict is not None:
                        self.tracking_dict.update(self._blocked_attempts)
                    
                    # Use custom handler if provided, otherwise return None
                    if self.blacklist_handler:
                        return self.blacklist_handler(client_ip, method_name or func.__name__)
                    else:
                        return None
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def _is_blacklisted(self, client_ip: str) -> bool:
        """
        Check if the client IP is blacklisted.
        
        Args:
            client_ip: Client's IP address
            
        Returns:
            True if blacklisted, False otherwise
        """
        return client_ip in self.blacklisted_ips
    
    def _record_blocked_attempt(self, client_ip: str, method_name: str):
        """
        Record a blocked attempt with FIFO eviction.
        
        Args:
            client_ip: Client's IP address
            method_name: Name of the method being accessed
        """
        import time
        
        if client_ip not in self._blocked_attempts:
            self._blocked_attempts[client_ip] = []
        
        # Add new attempt
        attempt = {
            'timestamp': time.time(),
            'method': method_name
        }
        self._blocked_attempts[client_ip].append(attempt)
        self._total_stored_attempts += 1
        
        # Evict oldest attempts if we exceed max_stored_attempts
        while self._total_stored_attempts > self.max_stored_attempts:
            self._evict_oldest_attempt()
    
    def _evict_oldest_attempt(self):
        """Evict the oldest blocked attempt (FIFO)."""
        oldest_timestamp = None
        oldest_ip = None
        oldest_index = None
        
        # Find the oldest attempt across all IPs
        for ip, attempts in self._blocked_attempts.items():
            if attempts:
                for i, attempt in enumerate(attempts):
                    if oldest_timestamp is None or attempt['timestamp'] < oldest_timestamp:
                        oldest_timestamp = attempt['timestamp']
                        oldest_ip = ip
                        oldest_index = i
        
        # Remove the oldest attempt
        if oldest_ip is not None and oldest_index is not None:
            self._blocked_attempts[oldest_ip].pop(oldest_index)
            self._total_stored_attempts -= 1
            
            # Clean up empty IP entries
            if not self._blocked_attempts[oldest_ip]:
                del self._blocked_attempts[oldest_ip]
    
    def add_ip(self, ip_address: str):
        """
        Add an IP address to the blacklist.
        
        Args:
            ip_address: IP address to blacklist
        """
        self.blacklisted_ips.add(ip_address)
    
    def remove_ip(self, ip_address: str):
        """
        Remove an IP address from the blacklist.
        
        Args:
            ip_address: IP address to remove from blacklist
        """
        self.blacklisted_ips.discard(ip_address)
    
    def add_ips(self, ip_addresses: list):
        """
        Add multiple IP addresses to the blacklist.
        
        Args:
            ip_addresses: List of IP addresses to blacklist
        """
        self.blacklisted_ips.update(ip_addresses)
    
    def clear_blacklist(self):
        """Clear all IP addresses from the blacklist."""
        self.blacklisted_ips.clear()
    
    def get_blacklisted_ips(self) -> set:
        """
        Get all blacklisted IP addresses.
        
        Returns:
            Set of blacklisted IP addresses
        """
        return self.blacklisted_ips.copy()
    
    def get_blocked_attempts(self, ip_address: str = None) -> dict:
        """
        Get blocked attempt statistics.
        
        Args:
            ip_address: Optional specific IP to get stats for
            
        Returns:
            Dictionary containing blocked attempt statistics
        """
        if ip_address:
            return {
                'ip': ip_address,
                'attempts': self._blocked_attempts.get(ip_address, [])
            }
        else:
            return self._blocked_attempts.copy()
    
    def get_storage_stats(self) -> dict:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage information
        """
        return {
            'total_stored_attempts': self._total_stored_attempts,
            'max_stored_attempts': self.max_stored_attempts,
            'unique_ips': len(self._blocked_attempts),
            'storage_usage_percent': (self._total_stored_attempts / self.max_stored_attempts) * 100
        }
    
    def clear_blocked_attempts(self, ip_address: str = None):
        """
        Clear blocked attempt records.
        
        Args:
            ip_address: Optional specific IP to clear records for
        """
        if ip_address:
            if ip_address in self._blocked_attempts:
                # Subtract the count of attempts being removed
                self._total_stored_attempts -= len(self._blocked_attempts[ip_address])
                del self._blocked_attempts[ip_address]
        else:
            self._blocked_attempts.clear()
            self._total_stored_attempts = 0
        
        # Update external tracking if provided
        if self.tracking_dict is not None:
            self.tracking_dict.clear()
            self.tracking_dict.update(self._blocked_attempts)
