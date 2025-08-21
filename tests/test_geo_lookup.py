import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
from zuu.geo_lookup import GeoLiteAuto


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_geoip_response():
    """Mock GeoIP2 database responses."""
    mock_country_result = Mock()
    mock_country_result.country.iso_code = "US"
    
    mock_city_result = Mock()
    mock_city_result.city.name = "New York"
    
    mock_asn_result = Mock()
    mock_asn_result.autonomous_system_number = 15169
    mock_asn_result.autonomous_system_organization = "Google LLC"
    mock_asn_result.ip_address = "8.8.8.8"
    mock_asn_result.network = "8.8.8.0/24"
    
    return {
        "country": mock_country_result,
        "city": mock_city_result,
        "asn": mock_asn_result
    }


class TestGeoLiteAutoInitialization:
    """Test initialization and configuration options."""
    
    def test_init_default_user_mode(self, temp_dir):
        """Test default USER storage mode initialization."""
        with patch('os.path.expanduser', return_value=temp_dir):
            geo = GeoLiteAuto(on_demand_db=True, on_demand_load=True)
            assert geo._GeoLiteAuto__includes == ["asn", "city", "country"]
            assert geo._GeoLiteAuto__cache_mode == "LRU"
    
    def test_init_custom_path_mode(self, temp_dir):
        """Test custom path storage mode."""
        geo = GeoLiteAuto(custom_path=temp_dir, on_demand_db=True, on_demand_load=True)
        assert geo._GeoLiteAuto__target_path == temp_dir
    
    def test_init_py_mode(self):
        """Test PY storage mode."""
        geo = GeoLiteAuto(storage_mode="PY", on_demand_db=True, on_demand_load=True)
        # Just check that it creates a reasonable path
        assert "geo_lookup_download" in geo._GeoLiteAuto__target_path
    
    def test_init_env_mode_with_var(self, temp_dir):
        """Test X_ZUU_ENV mode with environment variable set."""
        with patch.dict(os.environ, {'X_ZUU_GEOLOOKUP': temp_dir}):
            geo = GeoLiteAuto(storage_mode="X_ZUU_ENV", on_demand_db=True, on_demand_load=True)
            assert geo._GeoLiteAuto__target_path == temp_dir
    
    def test_init_env_mode_without_var(self):
        """Test X_ZUU_ENV mode without environment variable raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="X_ZUU_GEOLOOKUP environment variable is not set"):
                GeoLiteAuto(storage_mode="X_ZUU_ENV", on_demand_db=True, on_demand_load=True)
    
    def test_init_cache_modes(self, temp_dir):
        """Test different cache mode initializations."""
        cache_modes = ["LRU", "NONE", "CACHE"]
        for mode in cache_modes:
            geo = GeoLiteAuto(
                custom_path=temp_dir, 
                cache_mode=mode, 
                on_demand_db=True, 
                on_demand_load=True
            )
            assert geo._GeoLiteAuto__cache_mode == mode
    
    def test_init_custom_includes(self, temp_dir):
        """Test initialization with custom includes."""
        includes = ["country", "city"]
        geo = GeoLiteAuto(
            custom_path=temp_dir, 
            includes=includes, 
            on_demand_db=True, 
            on_demand_load=True
        )
        assert geo._GeoLiteAuto__includes == includes


class TestGeoLiteAutoDownload:
    """Test database download functionality."""
    
    @patch('requests.get')
    def test_download_success(self, mock_get, temp_dir):
        """Test successful database download."""
        mock_response = Mock()
        mock_response.content = b"fake_mmdb_content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        geo = GeoLiteAuto(custom_path=temp_dir, on_demand_db=True, on_demand_load=True)
        result = geo.country_mmdb()
        
        expected_path = os.path.join(temp_dir, "GeoLite2-Country.mmdb")
        assert result == expected_path
        assert os.path.exists(expected_path)
        
        with open(expected_path, 'rb') as f:
            assert f.read() == b"fake_mmdb_content"
    
    @patch('requests.get')
    def test_download_fallback_on_primary_failure(self, mock_get, temp_dir):
        """Test fallback URL is used when primary fails."""
        # First call fails with requests exception, second succeeds
        import requests
        mock_get.side_effect = [
            requests.RequestException("Primary URL failed"),
            Mock(content=b"fallback_content", raise_for_status=lambda: None)
        ]
        
        geo = GeoLiteAuto(custom_path=temp_dir, on_demand_db=True, on_demand_load=True)
        result = geo.asn_mmdb()
        
        expected_path = os.path.join(temp_dir, "GeoLite2-ASN.mmdb")
        assert result == expected_path
        assert os.path.exists(expected_path)
    
    def test_existing_file_not_redownloaded(self, temp_dir):
        """Test that existing files are not re-downloaded."""
        # Create existing file
        existing_file = os.path.join(temp_dir, "GeoLite2-City.mmdb")
        with open(existing_file, 'wb') as f:
            f.write(b"existing_content")
        
        with patch('requests.get') as mock_get:
            geo = GeoLiteAuto(custom_path=temp_dir, on_demand_db=True, on_demand_load=True)
            result = geo.city_mmdb()
            
            assert result == existing_file
            mock_get.assert_not_called()


class TestGeoLiteAutoLookup:
    """Test IP lookup functionality with different cache modes."""
    
    @patch('geoip2.database.Reader')
    def test_country_lookup_lru_cache(self, mock_reader, temp_dir, mock_geoip_response):
        """Test country lookup with LRU cache mode."""
        # Setup mock reader
        mock_reader_instance = Mock()
        mock_reader_instance.country.return_value = mock_geoip_response["country"]
        mock_reader.return_value = mock_reader_instance
        
        # Create fake database files
        for db_name in ["GeoLite2-Country.mmdb", "GeoLite2-City.mmdb", "GeoLite2-ASN.mmdb"]:
            with open(os.path.join(temp_dir, db_name), 'wb') as f:
                f.write(b"fake_content")
        
        geo = GeoLiteAuto(custom_path=temp_dir, cache_mode="LRU")
        
        # Test lookup
        result = geo.country("8.8.8.8")
        assert result == "US"
        
        # Test cache works (second call should use cache)
        result2 = geo.country("8.8.8.8")
        assert result2 == "US"
        assert mock_reader_instance.country.call_count == 1  # Should only be called once due to cache
    
    @patch('geoip2.database.Reader')
    def test_country_lookup_no_cache(self, mock_reader, temp_dir, mock_geoip_response):
        """Test country lookup with no cache mode."""
        mock_reader_instance = Mock()
        mock_reader_instance.country.return_value = mock_geoip_response["country"]
        mock_reader.return_value = mock_reader_instance
        
        # Create fake database files
        for db_name in ["GeoLite2-Country.mmdb", "GeoLite2-City.mmdb", "GeoLite2-ASN.mmdb"]:
            with open(os.path.join(temp_dir, db_name), 'wb') as f:
                f.write(b"fake_content")
        
        geo = GeoLiteAuto(custom_path=temp_dir, cache_mode="NONE")
        
        # Test multiple lookups
        result1 = geo.country("8.8.8.8")
        result2 = geo.country("8.8.8.8")
        
        assert result1 == "US"
        assert result2 == "US"
        assert mock_reader_instance.country.call_count == 2  # Should be called twice (no cache)
    
    @patch('geoip2.database.Reader')
    def test_asn_lookup(self, mock_reader, temp_dir, mock_geoip_response):
        """Test ASN lookup functionality."""
        mock_reader_instance = Mock()
        mock_reader_instance.asn.return_value = mock_geoip_response["asn"]
        mock_reader.return_value = mock_reader_instance
        
        # Create fake database files
        for db_name in ["GeoLite2-Country.mmdb", "GeoLite2-City.mmdb", "GeoLite2-ASN.mmdb"]:
            with open(os.path.join(temp_dir, db_name), 'wb') as f:
                f.write(b"fake_content")
        
        geo = GeoLiteAuto(custom_path=temp_dir, cache_mode="LRU")
        
        result = geo.asn("8.8.8.8")
        expected = {
            "number": 15169,
            "name": "Google LLC",
            "ip": "8.8.8.8",
            "network": "8.8.8.0/24"
        }
        assert result == expected
    
    @patch('geoip2.database.Reader')
    def test_city_lookup(self, mock_reader, temp_dir, mock_geoip_response):
        """Test city lookup functionality."""
        mock_reader_instance = Mock()
        mock_reader_instance.city.return_value = mock_geoip_response["city"]
        mock_reader.return_value = mock_reader_instance
        
        # Create fake database files
        for db_name in ["GeoLite2-Country.mmdb", "GeoLite2-City.mmdb", "GeoLite2-ASN.mmdb"]:
            with open(os.path.join(temp_dir, db_name), 'wb') as f:
                f.write(b"fake_content")
        
        geo = GeoLiteAuto(custom_path=temp_dir, cache_mode="LRU")
        
        result = geo.city("8.8.8.8")
        assert result == "New York"
    
    @patch('geoip2.database.Reader')
    def test_details_lookup(self, mock_reader, temp_dir, mock_geoip_response):
        """Test combined details lookup."""
        mock_reader_instance = Mock()
        mock_reader_instance.country.return_value = mock_geoip_response["country"]
        mock_reader_instance.city.return_value = mock_geoip_response["city"]
        mock_reader_instance.asn.return_value = mock_geoip_response["asn"]
        mock_reader.return_value = mock_reader_instance
        
        # Create fake database files
        for db_name in ["GeoLite2-Country.mmdb", "GeoLite2-City.mmdb", "GeoLite2-ASN.mmdb"]:
            with open(os.path.join(temp_dir, db_name), 'wb') as f:
                f.write(b"fake_content")
        
        geo = GeoLiteAuto(custom_path=temp_dir, cache_mode="LRU")
        
        result = geo.details("8.8.8.8")
        expected = {
            "asn": {
                "number": 15169,
                "name": "Google LLC",
                "ip": "8.8.8.8",
                "network": "8.8.8.0/24"
            },
            "city": "New York",
            "country": "US"
        }
        assert result == expected


class TestGeoLiteAutoErrorHandling:
    """Test error handling and edge cases."""
    
    def test_missing_include_raises_error(self, temp_dir):
        """Test that accessing non-included lookup raises error."""
        # Create fake database files
        for db_name in ["GeoLite2-Country.mmdb", "GeoLite2-City.mmdb", "GeoLite2-ASN.mmdb"]:
            with open(os.path.join(temp_dir, db_name), 'wb') as f:
                f.write(b"fake_content")
        
        geo = GeoLiteAuto(custom_path=temp_dir, includes=["country"], on_demand_load=True)
        
        with pytest.raises(ValueError, match="ASN lookup not included"):
            _ = geo._asn  # This should trigger the cached_property and raise error
    
    @patch('requests.get')
    def test_download_failure_both_urls(self, mock_get, temp_dir):
        """Test behavior when both primary and fallback URLs fail."""
        mock_get.side_effect = Exception("Network error")
        
        geo = GeoLiteAuto(custom_path=temp_dir, on_demand_db=True, on_demand_load=True)
        
        with pytest.raises(Exception):
            geo.country_mmdb()


class TestGeoLiteAutoCachePerformance:
    """Test cache performance and behavior."""
    
    @patch('geoip2.database.Reader')
    def test_lru_cache_eviction(self, mock_reader, temp_dir, mock_geoip_response):
        """Test that LRU cache evicts old entries when maxsize is exceeded."""
        mock_reader_instance = Mock()
        mock_reader_instance.country.return_value = mock_geoip_response["country"]
        mock_reader.return_value = mock_reader_instance
        
        # Create fake database files
        for db_name in ["GeoLite2-Country.mmdb", "GeoLite2-City.mmdb", "GeoLite2-ASN.mmdb"]:
            with open(os.path.join(temp_dir, db_name), 'wb') as f:
                f.write(b"fake_content")
        
        # Create a GeoLiteAuto with small cache for testing
        geo = GeoLiteAuto(custom_path=temp_dir, cache_mode="LRU")
        
        # The actual maxsize is 10000, so this test verifies cache is working
        # We can't easily test eviction without making 10000+ calls
        for i in range(5):
            result = geo.country(f"192.168.1.{i}")
            assert result == "US"
        
        # Verify the same IP uses cache
        initial_call_count = mock_reader_instance.country.call_count
        geo.country("192.168.1.1")  # This should hit cache
        assert mock_reader_instance.country.call_count == initial_call_count
    
    @patch('geoip2.database.Reader')
    def test_unbounded_cache_mode(self, mock_reader, temp_dir, mock_geoip_response):
        """Test unbounded cache mode behavior."""
        mock_reader_instance = Mock()
        mock_reader_instance.country.return_value = mock_geoip_response["country"]
        mock_reader.return_value = mock_reader_instance
        
        # Create fake database files
        for db_name in ["GeoLite2-Country.mmdb", "GeoLite2-City.mmdb", "GeoLite2-ASN.mmdb"]:
            with open(os.path.join(temp_dir, db_name), 'wb') as f:
                f.write(b"fake_content")
        
        geo = GeoLiteAuto(custom_path=temp_dir, cache_mode="CACHE")
        
        # Test multiple unique IPs
        for i in range(10):
            result = geo.country(f"10.0.0.{i}")
            assert result == "US"
        
        # All should be cached - calling first IP again should not trigger new lookup
        initial_call_count = mock_reader_instance.country.call_count
        geo.country("10.0.0.1")
        assert mock_reader_instance.country.call_count == initial_call_count


class TestGeoLiteAutoIntegration:
    """Integration tests that test the full workflow."""
    
    @patch('requests.get')
    @patch('geoip2.database.Reader')
    def test_full_workflow_integration(self, mock_reader, mock_get, temp_dir, mock_geoip_response):
        """Test the complete workflow from initialization to lookup."""
        # Setup download mock
        mock_response = Mock()
        mock_response.content = b"fake_mmdb_content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Setup reader mock
        mock_reader_instance = Mock()
        mock_reader_instance.country.return_value = mock_geoip_response["country"]
        mock_reader_instance.city.return_value = mock_geoip_response["city"]
        mock_reader_instance.asn.return_value = mock_geoip_response["asn"]
        mock_reader.return_value = mock_reader_instance
        
        # Initialize and use
        geo = GeoLiteAuto(custom_path=temp_dir, cache_mode="LRU")
        
        # Test all lookup types
        country_result = geo.country("8.8.8.8")
        city_result = geo.city("8.8.8.8")
        asn_result = geo.asn("8.8.8.8")
        details_result = geo.details("8.8.8.8")
        
        # Verify results
        assert country_result == "US"
        assert city_result == "New York"
        assert asn_result["number"] == 15169
        assert "country" in details_result
        assert "city" in details_result
        assert "asn" in details_result
        
        # Verify files were downloaded
        for db_name in ["GeoLite2-Country.mmdb", "GeoLite2-City.mmdb", "GeoLite2-ASN.mmdb"]:
            assert os.path.exists(os.path.join(temp_dir, db_name))
