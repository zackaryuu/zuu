"""
Advanced Flask rate limiting handler with LRU and concurrent connection management.

Extends SimpleRateLimit with LRU behavior and concurrent connection limits.
"""

import time
from collections import OrderedDict
from dataclasses import dataclass
from flask import request
from .flask_simple_ratelimit import SimpleRateLimit
from .flask import get_client_ip


@dataclass
class FlaskRateLimit(SimpleRateLimit):
    """
    Advanced rate limiting handler that extends SimpleRateLimit.

    Adds LRU behavior, concurrent connection limits, and weight-based calculations.
    """

    max_allowed_concurrent: int = 100
    keep_alive_interval: str = "5 minutes"
    weight_calculator: callable = None

    def __post_init__(self):
        """Initialize after dataclass creation."""
        super().__post_init__()

        # LRU tracking - OrderedDict maintains insertion/access order
        self._lru_access = OrderedDict()

        # Concurrent connections tracking - client_ip -> connection info
        self._active_connections = {}

        # Parse keep alive interval to seconds
        self._keep_alive_seconds = self._parse_time_period(self.keep_alive_interval)

    def limit(self, method_name, max_requests=None, per=None, weight=1):
        """
        Enhanced decorator factory with LRU and concurrent connection management.

        Args:
            method_name: Name of the method/endpoint to rate limit
            max_requests: Optional override for max requests
            per: Optional override for time period
            weight: Weight for this request (default: 1)

        Returns:
            Decorator function
        """

        def decorator(func):
            from functools import wraps

            @wraps(func)
            def wrapper(*args, **kwargs):
                client_ip = get_client_ip(request)

                # Calculate request weight
                request_weight = self._calculate_weight(client_ip, method_name, weight)

                # Check concurrent connections limit first
                if not self._check_concurrent_limit(client_ip, request_weight):
                    if self.rate_limit_handler:
                        return self.rate_limit_handler(
                            method_name,
                            0,  # No rate limit exceeded, but concurrent limit hit
                            "concurrent",
                            client_ip,
                            {"reason": "concurrent_limit", "weight": request_weight},
                        )
                    else:
                        return None

                # Update LRU access
                self._update_lru_access(client_ip, method_name)

                # Standard rate limiting check (from parent class)
                if method_name in self.method_limits:
                    method_config = self.method_limits[method_name]
                    method_max_requests = max_requests or method_config.get(
                        "max_requests", self.default_max_requests
                    )
                    method_per = per or method_config.get("per", self.default_per)
                else:
                    method_max_requests = max_requests or self.default_max_requests
                    method_per = per or self.default_per

                window_seconds = self._parse_time_period(method_per)

                if self._is_rate_limited(
                    client_ip,
                    method_name,
                    method_max_requests,
                    window_seconds,
                    request_weight,
                ):
                    if self.rate_limit_handler:
                        return self.rate_limit_handler(
                            method_name,
                            method_max_requests,
                            method_per,
                            client_ip,
                            {"reason": "rate_limit", "weight": request_weight},
                        )
                    else:
                        return None

                # Register active connection
                self._register_connection(client_ip, method_name, request_weight)

                # Record the request with weight
                self._record_request(method_name, client_ip, request_weight)

                try:
                    # Execute the function
                    result = func(*args, **kwargs)
                    return result
                finally:
                    # Always unregister connection when done
                    self._unregister_connection(client_ip, method_name)

            return wrapper

        return decorator

    def _calculate_weight(
        self, client_ip: str, method_name: str, base_weight: int
    ) -> int:
        """
        Calculate request weight using custom calculator if provided.

        Args:
            client_ip: Client's IP address
            method_name: Name of the method being accessed
            base_weight: Base weight for the request

        Returns:
            Calculated weight
        """
        if self.weight_calculator:
            return self.weight_calculator(client_ip, method_name, base_weight, request)
        return base_weight

    def _check_concurrent_limit(self, client_ip: str, weight: int) -> bool:
        """
        Check if allowing this connection would exceed concurrent limits.

        Args:
            client_ip: Client's IP address
            weight: Weight of the request

        Returns:
            True if connection allowed, False otherwise
        """
        # Clean up expired connections first
        self._cleanup_expired_connections()

        # Calculate current total weight
        current_weight = sum(
            conn["weight"] for conn in self._active_connections.values()
        )

        # Check if adding this request would exceed limit
        return (current_weight + weight) <= self.max_allowed_concurrent

    def _register_connection(self, client_ip: str, method_name: str, weight: int):
        """
        Register an active connection.

        Args:
            client_ip: Client's IP address
            method_name: Name of the method being accessed
            weight: Weight of the connection
        """
        connection_key = f"{client_ip}:{method_name}:{time.time()}"
        self._active_connections[connection_key] = {
            "client_ip": client_ip,
            "method_name": method_name,
            "weight": weight,
            "start_time": time.time(),
        }

    def _unregister_connection(self, client_ip: str, method_name: str):
        """
        Unregister an active connection.

        Args:
            client_ip: Client's IP address
            method_name: Name of the method being accessed
        """
        # Find and remove the most recent connection for this client/method
        to_remove = None
        latest_time = 0

        for key, conn in self._active_connections.items():
            if (
                conn["client_ip"] == client_ip
                and conn["method_name"] == method_name
                and conn["start_time"] > latest_time
            ):
                to_remove = key
                latest_time = conn["start_time"]

        if to_remove:
            del self._active_connections[to_remove]

    def _cleanup_expired_connections(self):
        """Clean up connections that exceed keep_alive_interval."""
        current_time = time.time()
        expired_keys = []

        for key, conn in self._active_connections.items():
            if current_time - conn["start_time"] > self._keep_alive_seconds:
                expired_keys.append(key)

        for key in expired_keys:
            del self._active_connections[key]

    def _update_lru_access(self, client_ip: str, method_name: str):
        """
        Update LRU access tracking.

        Args:
            client_ip: Client's IP address
            method_name: Name of the method being accessed
        """
        access_key = f"{client_ip}:{method_name}"

        # Remove if exists (to update order)
        if access_key in self._lru_access:
            del self._lru_access[access_key]

        # Add to end (most recent)
        self._lru_access[access_key] = {
            "client_ip": client_ip,
            "method_name": method_name,
            "last_access": time.time(),
        }

    def _is_rate_limited(
        self,
        client_ip: str,
        method_name: str,
        max_requests: int,
        window_seconds: int,
        weight: int,
    ) -> bool:
        """
        Enhanced rate limiting check that considers weight.

        Args:
            client_ip: Client's IP address
            method_name: Name of the method being accessed
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            weight: Weight of the request

        Returns:
            True if rate limited, False otherwise
        """
        # Use parent class rate limiting logic but record weighted requests
        current_time = time.time()

        # Initialize tracking for method if not exists
        if method_name not in self._internal_tracking:
            self._internal_tracking[method_name] = {}

        # Initialize tracking for client if not exists
        if client_ip not in self._internal_tracking[method_name]:
            self._internal_tracking[method_name][client_ip] = []

        # Get request data for this client and method
        request_data = self._internal_tracking[method_name][client_ip]

        # Remove old requests outside the window
        cutoff_time = current_time - window_seconds
        request_data[:] = [
            req for req in request_data if req.get("timestamp", req) > cutoff_time
        ]

        # Calculate total weight in current window
        total_weight = sum(
            req.get("weight", 1) if isinstance(req, dict) else 1 for req in request_data
        )

        # Check if adding this request's weight would exceed limit
        return (total_weight + weight) > max_requests

    def _record_request(self, method_name: str, client_ip: str, weight: int = 1):
        """
        Enhanced request recording with weight tracking.

        Args:
            method_name: Name of the method being accessed
            client_ip: Client's IP address
            weight: Weight of the request
        """
        current_time = time.time()
        request_record = {"timestamp": current_time, "weight": weight}
        self._internal_tracking[method_name][client_ip].append(request_record)

    def get_lru_stats(self) -> dict:
        """
        Get LRU access statistics.

        Returns:
            Dictionary with LRU information
        """
        return {
            "total_tracked": len(self._lru_access),
            "least_recent": list(self._lru_access.keys())[:5],  # First 5 (oldest)
            "most_recent": list(self._lru_access.keys())[-5:],  # Last 5 (newest)
        }

    def get_concurrent_stats(self) -> dict:
        """
        Get concurrent connection statistics.

        Returns:
            Dictionary with concurrent connection information
        """
        self._cleanup_expired_connections()

        current_weight = sum(
            conn["weight"] for conn in self._active_connections.values()
        )

        return {
            "active_connections": len(self._active_connections),
            "current_weight": current_weight,
            "max_allowed_concurrent": self.max_allowed_concurrent,
            "weight_utilization_percent": (current_weight / self.max_allowed_concurrent)
            * 100,
            "keep_alive_seconds": self._keep_alive_seconds,
        }

    def evict_lru(self, count: int = 1):
        """
        Evict least recently used entries from tracking.

        Args:
            count: Number of LRU entries to evict
        """
        for _ in range(min(count, len(self._lru_access))):
            if self._lru_access:
                # Remove oldest (first) entry
                oldest_key, oldest_data = self._lru_access.popitem(last=False)

                # Also remove from rate limiting tracking
                client_ip = oldest_data["client_ip"]
                method_name = oldest_data["method_name"]

                if (
                    method_name in self._internal_tracking
                    and client_ip in self._internal_tracking[method_name]
                ):
                    # Clear this client's tracking for this method
                    self._internal_tracking[method_name][client_ip] = []

    def get_remaining(
        self,
        client_ip: str,
        method_name: str,
        max_requests: int = None,
        per: str = None,
    ) -> int:
        """
        Get remaining requests for a client and method.

        Args:
            client_ip: Client's IP address
            method_name: Name of the method being accessed
            max_requests: Override max requests (uses method config if None)
            per: Override time period (uses method config if None)

        Returns:
            Number of remaining requests (considering weight)
        """
        # Determine limits for this method
        if method_name in self.method_limits:
            method_config = self.method_limits[method_name]
            method_max_requests = max_requests or method_config.get(
                "max_requests", self.default_max_requests
            )
            method_per = per or method_config.get("per", self.default_per)
        else:
            method_max_requests = max_requests or self.default_max_requests
            method_per = per or self.default_per

        window_seconds = self._parse_time_period(method_per)
        current_time = time.time()

        # Get current usage in window
        if (
            method_name not in self._internal_tracking
            or client_ip not in self._internal_tracking[method_name]
        ):
            return method_max_requests

        request_data = self._internal_tracking[method_name][client_ip]
        cutoff_time = current_time - window_seconds

        # Filter to current window and calculate total weight used
        current_requests = [
            req for req in request_data if req.get("timestamp", req) > cutoff_time
        ]
        total_weight_used = sum(
            req.get("weight", 1) if isinstance(req, dict) else 1
            for req in current_requests
        )

        remaining = method_max_requests - total_weight_used
        return max(0, remaining)

    def get_nextreset(self, client_ip: str, method_name: str, per: str = None) -> int:
        """
        Get timestamp when rate limit window resets for a client and method.

        Args:
            client_ip: Client's IP address
            method_name: Name of the method being accessed
            per: Override time period (uses method config if None)

        Returns:
            Unix timestamp when the window resets (0 if no requests in current window)
        """
        # Determine time period for this method
        if method_name in self.method_limits:
            method_config = self.method_limits[method_name]
            method_per = per or method_config.get("per", self.default_per)
        else:
            method_per = per or self.default_per

        window_seconds = self._parse_time_period(method_per)

        # Get oldest request in current window
        if (
            method_name not in self._internal_tracking
            or client_ip not in self._internal_tracking[method_name]
        ):
            return 0

        request_data = self._internal_tracking[method_name][client_ip]
        if not request_data:
            return 0

        current_time = time.time()
        cutoff_time = current_time - window_seconds

        # Find oldest request still in the window
        oldest_in_window = None
        for req in request_data:
            req_time = req.get("timestamp", req) if isinstance(req, dict) else req
            if req_time > cutoff_time:
                if oldest_in_window is None or req_time < oldest_in_window:
                    oldest_in_window = req_time

        if oldest_in_window is None:
            return 0

        # Reset time is when the oldest request ages out
        reset_time = oldest_in_window + window_seconds
        return int(reset_time)

    def get_maxattempts(self, method_name: str, max_requests: int = None) -> int:
        """
        Get maximum attempts allowed for a method.

        Args:
            method_name: Name of the method being accessed
            max_requests: Override max requests (uses method config if None)

        Returns:
            Maximum attempts allowed in the time window
        """
        if method_name in self.method_limits:
            method_config = self.method_limits[method_name]
            return max_requests or method_config.get(
                "max_requests", self.default_max_requests
            )
        else:
            return max_requests or self.default_max_requests

    def get_rate_limit_headers(
        self,
        client_ip: str,
        method_name: str,
        max_requests: int = None,
        per: str = None,
        include_concurrent_details: bool = False
    ) -> dict:
        """
        Get all rate limit headers for easy response integration.

        Args:
            client_ip: Client's IP address
            method_name: Name of the method being accessed
            max_requests: Override max requests (uses method config if None)
            per: Override time period (uses method config if None)

        Returns:
            Dictionary of headers to add to response
        """
        remaining = self.get_remaining(client_ip, method_name, max_requests, per)
        reset_time = self.get_nextreset(client_ip, method_name, per)
        max_attempts = self.get_maxattempts(method_name, max_requests)

        

        headers = {
            "X-RateLimit-Limit": str(max_attempts),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
        }

        if include_concurrent_details:
            # Get current concurrent connection info
            concurrent_stats = self.get_concurrent_stats()
            headers.update({
                "X-RateLimit-Concurrent-Active": str(concurrent_stats["active_connections"]),
                "X-RateLimit-Concurrent-Weight": str(concurrent_stats["current_weight"]),
                "X-RateLimit-Concurrent-Max": str(concurrent_stats["max_allowed_concurrent"]),
                "X-RateLimit-Concurrent-Utilization": f"{concurrent_stats['weight_utilization_percent']:.2f}%",
            })

        # Add retry-after header if rate limited
        if remaining <= 0 and reset_time > 0:
            retry_after = max(1, reset_time - int(time.time()))
            headers["Retry-After"] = str(retry_after)

        return headers
