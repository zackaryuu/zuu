"""
GeoLite2 IP Geolocation Module

This module provides automatic downloading and caching of MaxMind GeoLite2 databases
for IP geolocation lookups. It supports ASN, city, and country lookups with flexible
caching strategies and storage options.

Example:
    >>> from zuu.geo_lookup import GeoLiteAuto
    >>> geo = GeoLiteAuto()
    >>> country = geo.country("8.8.8.8")  # Returns "US"
    >>> details = geo.details("8.8.8.8")  # Returns all available data
"""

from functools import cached_property, lru_cache, cache
import os
import typing
import geoip2.database as gdb
import requests

asn_url_1 = "https://git.io/GeoLite2-ASN.mmdb"
city_url_1 = "https://git.io/GeoLite2-City.mmdb"
country_url_1 = "https://git.io/GeoLite2-Country.mmdb"

asn_url_2 = "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-ASN.mmdb"
city_url_2 = "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-City.mmdb"
country_url_2 = "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-Country.mmdb"

class GeoLiteAuto:
    """
    Automatic GeoLite2 database downloader and IP geolocation lookup service.
    
    This class automatically downloads MaxMind GeoLite2 databases and provides
    high-performance IP geolocation lookups with configurable caching strategies.
    
    **Two Ways to Perform Lookups:**
    
    1. **Simplified Methods** (Recommended) - Returns processed data:
       - `geo.country(ip)` → Returns country ISO code (e.g., "US")
       - `geo.city(ip)` → Returns city name (e.g., "New York")
       - `geo.asn(ip)` → Returns ASN info dict
       
    2. **Direct Database Access** - Returns raw GeoIP2 objects:
       - `geo._country.country(ip)` → Returns full GeoIP2 country response
       - `geo._city.city(ip)` → Returns full GeoIP2 city response  
       - `geo._asn.asn(ip)` → Returns full GeoIP2 ASN response
    
    Cache Modes:
        - "LRU": LRU cache with 10,000 entries (memory-safe, default)
        - "CACHE": Unbounded cache (fast but can grow large)
        - "NONE": No caching (consistent memory, slower)
    
    Storage Modes:
        - "USER": ~/.zuu/geo_lookup (default)
        - "PY": Next to this Python file
        - "X_ZUU_ENV": Path from X_ZUU_GEOLOOKUP environment variable
        - custom_path: User-specified directory
        
    Args:
        storage_mode: Where to store downloaded databases
        custom_path: Custom storage path (overrides storage_mode)
        on_demand_db: Only download databases when first accessed
        on_demand_load: Only load database readers when first accessed
        includes: List of databases to include ["asn", "city", "country"]
        cache_mode: Caching strategy for lookups
        
    Example:
        >>> # Basic usage with defaults
        >>> geo = GeoLiteAuto()
        >>> country = geo.country("8.8.8.8")  # "US"
        >>> 
        >>> # Custom configuration
        >>> geo = GeoLiteAuto(
        ...     cache_mode="CACHE",
        ...     includes=["country", "asn"],
        ...     storage_mode="PY"
        ... )
        >>> 
        >>> # Two ways to get data:
        >>> country_code = geo.country("1.1.1.1")           # "AU" 
        >>> country_obj = geo._country.country("1.1.1.1")   # Full GeoIP2 response
        
    Raises:
        ValueError: If X_ZUU_ENV mode used without setting X_ZUU_GEOLOOKUP env var
        ValueError: If accessing lookup type not included in initialization
        requests.RequestException: If database download fails from all URLs
    """
    def __init__(
        self,
        storage_mode: typing.Literal["USER", "PY", "X_ZUU_ENV"] = "USER",
        custom_path: str = None,
        on_demand_db : bool = False,
        on_demand_load : bool = True,
        includes : list[str] = ["asn", "city", "country"],
        cache_mode : typing.Literal["LRU", "NONE", "CACHE"] = "LRU"
    ):
        """
        Initialize GeoLiteAuto with specified configuration.
        
        Args:
            storage_mode: Database storage location strategy
                - "USER": Store in user home directory (~/.zuu/geo_lookup)  
                - "PY": Store next to this Python module
                - "X_ZUU_ENV": Use X_ZUU_GEOLOOKUP environment variable
            custom_path: Override storage_mode with custom directory path
            on_demand_db: If True, download databases only when first needed
            on_demand_load: If True, load database readers only when first accessed
            includes: List of database types to include (subset of ["asn", "city", "country"])
            cache_mode: Caching strategy for IP lookups
                - "LRU": LRU cache with 10K entries (memory-safe, recommended)
                - "CACHE": Unbounded cache (faster but can use lots of memory)
                - "NONE": No caching (predictable memory usage)
                
        Raises:
            ValueError: If storage_mode is "X_ZUU_ENV" but X_ZUU_GEOLOOKUP not set
        """
        match (storage_mode, custom_path):
            case (_, str()):
                target_path = custom_path
            case ("USER", None):
                target_path = os.path.expanduser("~/.zuu/geo_lookup")
            case ("PY", None):
                script_location = os.path.dirname(os.path.abspath(__file__))
                target_path = os.path.join(script_location, "geo_lookup_download")
            case ("X_ZUU_ENV", None):
                target_path = os.environ.get("X_ZUU_GEOLOOKUP", None)
                if not target_path:
                    raise ValueError("X_ZUU_GEOLOOKUP environment variable is not set.")

        self.__includes = includes
        self.__target_path = target_path
        self.__storage_mode = storage_mode
        self.__cache_mode = cache_mode

        for include in includes:
            if not on_demand_db:
                getattr(self, f"{include}_mmdb")()

            if not on_demand_load:
                getattr(self, include)

        
    def __internal_download_db(self, filename, url, fallbackurl):
        """
        Download a GeoLite2 database file from primary or fallback URL.
        
        Args:
            filename: Name of the database file to save
            url: Primary download URL
            fallbackurl: Fallback URL if primary fails
            
        Raises:
            requests.RequestException: If both URLs fail to download
        """
        if not os.path.exists(self.__target_path):
            os.makedirs(self.__target_path, exist_ok=True)
        try:
            response = requests.get(url)
            response.raise_for_status()
            with open(os.path.join(self.__target_path, filename), "wb") as f:
                f.write(response.content)
        except requests.RequestException:
            if fallbackurl:
                response = requests.get(fallbackurl)
                response.raise_for_status()
                with open(os.path.join(self.__target_path, filename), "wb") as f:
                    f.write(response.content)

    def asn_mmdb(self):
        """
        Get path to ASN database file, downloading if necessary.
        
        Returns:
            str: Absolute path to GeoLite2-ASN.mmdb file
        """
        if not os.path.exists(os.path.join(self.__target_path, "GeoLite2-ASN.mmdb")):
            self.__internal_download_db("GeoLite2-ASN.mmdb", asn_url_1, asn_url_2)
        return os.path.join(self.__target_path, "GeoLite2-ASN.mmdb")

    @cached_property
    def _asn(self):
        """
        Get GeoIP2 ASN database reader for direct access.
        
        Use this for raw GeoIP2 response objects:
            geo._asn.asn(ip)  # Returns full ASN response object
            
        Returns:
            geoip2.database.Reader: ASN database reader
            
        Raises:
            ValueError: If "asn" not included in initialization includes
        """
        if "asn" not in self.__includes:
            raise ValueError("ASN lookup not included in the initialization includes.")
        return gdb.Reader(self.asn_mmdb())

    def city_mmdb(self):
        """
        Get path to City database file, downloading if necessary.
        
        Returns:
            str: Absolute path to GeoLite2-City.mmdb file
        """
        if not os.path.exists(os.path.join(self.__target_path, "GeoLite2-City.mmdb")):
            self.__internal_download_db("GeoLite2-City.mmdb", city_url_1, city_url_2)
        return os.path.join(self.__target_path, "GeoLite2-City.mmdb")

    @cached_property
    def _city(self):
        """
        Get GeoIP2 City database reader for direct access.
        
        Use this for raw GeoIP2 response objects:
            geo._city.city(ip)  # Returns full city response object
            
        Returns:
            geoip2.database.Reader: City database reader
            
        Raises:
            ValueError: If "city" not included in initialization includes
        """
        if "city" not in self.__includes:
            raise ValueError("City lookup not included in the initialization includes.")
        return gdb.Reader(self.city_mmdb())

    def country_mmdb(self):
        """
        Get path to Country database file, downloading if necessary.
        
        Returns:
            str: Absolute path to GeoLite2-Country.mmdb file
        """
        if not os.path.exists(os.path.join(self.__target_path, "GeoLite2-Country.mmdb")):
            self.__internal_download_db("GeoLite2-Country.mmdb", country_url_1, country_url_2)
        return os.path.join(self.__target_path, "GeoLite2-Country.mmdb")

    @cached_property
    def _country(self):
        """
        Get GeoIP2 Country database reader for direct access.
        
        Use this for raw GeoIP2 response objects:
            geo._country.country(ip)  # Returns full country response object
            
        Returns:
            geoip2.database.Reader: Country database reader
            
        Raises:
            ValueError: If "country" not included in initialization includes
        """ 
        if "country" not in self.__includes:
            raise ValueError("Country lookup not included in the initialization includes.")
        return gdb.Reader(self.country_mmdb())
    
    def __the_actual_real_country(self, ip):
        """Extract country ISO code from GeoIP2 country lookup."""
        return self._country.country(ip).country.iso_code

    def __the_actual_real_city(self, ip):
        """Extract city name from GeoIP2 city lookup."""
        return self._city.city(ip).city.name

    def __the_actual_real_asn(self, ip):
        """Extract ASN information from GeoIP2 ASN lookup."""
        result = self._asn.asn(ip)
        return {
            "number": result.autonomous_system_number,
            "name": result.autonomous_system_organization,
            "ip": result.ip_address,
            "network": result.network
        }

    @lru_cache(maxsize=10000)
    def __lru_cache_country(self, ip):
        return self.__the_actual_real_country(ip)

    @lru_cache(maxsize=10000)
    def __lru_cache_asn(self, ip):
        return self.__the_actual_real_asn(ip)

    @lru_cache(maxsize=10000)
    def __lru_cache_city(self, ip):
        return self.__the_actual_real_city(ip)

    __the_cached_country = cache(__the_actual_real_country)
    __the_cached_asn = cache(__the_actual_real_asn)
    __the_cached_city = cache(__the_actual_real_city)

    def country(self, ip):
        """
        Look up country for an IP address.
        
        Args:
            ip (str): IP address to look up (IPv4 or IPv6)
            
        Returns:
            str: Two-letter ISO country code (e.g., "US", "UK", "DE")
            
        Example:
            >>> geo.country("8.8.8.8")
            'US'
            >>> geo.country("2001:4860:4860::8888") 
            'US'
            
        Note:
            For full GeoIP2 response object, use: geo._country.country(ip)
        """
        if self.__cache_mode == "LRU":
            return self.__lru_cache_country(ip)
        elif self.__cache_mode == "NONE":
            return self.__the_actual_real_country(ip)
        elif self.__cache_mode == "CACHE":
            return self.__the_cached_country(ip)

    def asn(self, ip):
        """
        Look up ASN (Autonomous System Number) information for an IP address.
        
        Args:
            ip (str): IP address to look up (IPv4 or IPv6)
            
        Returns:
            dict: ASN information with keys:
                - number (int): ASN number (e.g., 15169)
                - name (str): Organization name (e.g., "Google LLC") 
                - ip (str): The queried IP address
                - network (str): Network range (e.g., "8.8.8.0/24")
                
        Example:
            >>> geo.asn("8.8.8.8")
            {
                'number': 15169,
                'name': 'Google LLC',
                'ip': '8.8.8.8', 
                'network': '8.8.8.0/24'
            }
            
        Note:
            For full GeoIP2 response object, use: geo._asn.asn(ip)
        """
        if self.__cache_mode == "LRU":
            return self.__lru_cache_asn(ip)
        elif self.__cache_mode == "NONE":
            return self.__the_actual_real_asn(ip)
        elif self.__cache_mode == "CACHE":
            return self.__the_cached_asn(ip)

    def city(self, ip):
        """
        Look up city name for an IP address.
        
        Args:
            ip (str): IP address to look up (IPv4 or IPv6)
            
        Returns:
            str: City name (e.g., "New York", "London") or None if not available
            
        Example:
            >>> geo.city("8.8.8.8")
            'Mountain View'
            
        Note:
            For full GeoIP2 response object, use: geo._city.city(ip)
        """
        if self.__cache_mode == "LRU":
            return self.__lru_cache_city(ip)
        elif self.__cache_mode == "NONE":
            return self.__the_actual_real_city(ip)
        elif self.__cache_mode == "CACHE":
            return self.__the_cached_city(ip)

    def details(self, ip):
        """
        Look up all available geolocation details for an IP address.
        
        Args:
            ip (str): IP address to look up (IPv4 or IPv6)
            
        Returns:
            dict: Combined results from all included lookup types.
                Keys depend on the 'includes' parameter from initialization.
                Default includes all of: 'asn', 'city', 'country'
                
        Example:
            >>> geo.details("8.8.8.8")
            {
                'asn': {
                    'number': 15169,
                    'name': 'Google LLC', 
                    'ip': '8.8.8.8',
                    'network': '8.8.8.0/24'
                },
                'city': 'Mountain View',
                'country': 'US'
            }
            
        Note:
            This method calls the individual lookup methods (country, city, asn)
            which respect the configured cache_mode setting.
        """
        r = {}
        for include in self.__includes:
            r[include] = getattr(self, include)(ip)
        return r

