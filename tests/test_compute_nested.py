import pytest
from src.zuu.nested_dict import compute_nested, flatten_dict


class TestComputeNested:
    
    def test_basic_functionality(self):
        """Test basic functionality with single supplementary dict"""
        keys = ['loginBtn', 'loginForm', 'loginKey', 'submitForm', 'submitBtn']
        supp_dict = {
            'loginBtn': 'loginPage',
            'loginForm': 'loginPage', 
            'loginKey': 'loginPage',
            'submitForm': 'loginPage',
            'submitBtn': 'logout'
        }
        
        result = compute_nested(keys, (supp_dict, 15))
        
        expected = {
            'loginPage': {
                'btn': 'loginBtn',
                'form': 'loginForm', 
                'key': 'loginKey',
                'submitForm': 'submitForm'
            },
            'logout': {
                'submitBtn': 'submitBtn'
            }
        }
        
        assert result == expected
    
    def test_weight_priority(self):
        """Test that higher weights take priority in token removal"""
        keys = ['loginBtn', 'loginForm']
        supp_dict = {
            'loginBtn': 'loginPage',
            'loginForm': 'loginPage'
        }
        
        # Group weight higher than keys_weight - should remove common tokens
        result_high_weight = compute_nested(keys, (supp_dict, 15), keys_weight=10)
        assert result_high_weight == {
            'loginPage': {
                'btn': 'loginBtn',
                'form': 'loginForm'
            }
        }
        
        # Keys_weight higher than group weight - should keep common tokens
        result_low_weight = compute_nested(keys, (supp_dict, 5), keys_weight=10)
        assert result_low_weight == {
            'loginPage': {
                'loginBtn': 'loginBtn',
                'loginForm': 'loginForm'
            }
        }
    
    def test_multiple_supplementary_dicts(self):
        """Test handling multiple supplementary dictionaries"""
        keys = ['userLoginBtn', 'adminLoginBtn', 'userLogoutBtn']
        
        page_dict = {
            'userLoginBtn': 'loginPage',
            'adminLoginBtn': 'loginPage',
            'userLogoutBtn': 'logoutPage'
        }
        
        role_dict = {
            'userLoginBtn': 'userRole',
            'adminLoginBtn': 'adminRole', 
            'userLogoutBtn': 'userRole'
        }
        
        result = compute_nested(keys, (page_dict, 20), (role_dict, 15), keys_weight=10)
        
        # Should create nested structure with both levels
        expected = {
            'loginPage': {
                'userRole': {
                    'btn': 'userLoginBtn'
                },
                'adminRole': {
                    'btn': 'adminLoginBtn'
                }
            },
            'logoutPage': {
                'userRole': {
                    'btn': 'userLogoutBtn'
                }
            }
        }
        
        assert result == expected
    
    def test_maxlv_restriction(self):
        """Test maxlv parameter restricts nesting levels"""
        keys = ['userLoginBtn', 'adminLoginBtn']
        
        page_dict = {
            'userLoginBtn': 'loginPage',
            'adminLoginBtn': 'loginPage'
        }
        
        role_dict = {
            'userLoginBtn': 'userRole',
            'adminLoginBtn': 'adminRole'
        }
        
        # maxlv=1 should only use first supplementary dict
        result = compute_nested(keys, (page_dict, 20), (role_dict, 15), maxlv=1, keys_weight=10)
        
        expected = {
            'loginPage': {
                'userBtn': 'userLoginBtn',
                'adminBtn': 'adminLoginBtn'
            }
        }
        
        assert result == expected
    
    def test_maxlv_zero(self):
        """Test maxlv=0 creates flat structure"""
        keys = ['loginBtn', 'submitBtn']
        supp_dict = {
            'loginBtn': 'loginPage',
            'submitBtn': 'submitPage'
        }
        
        result = compute_nested(keys, (supp_dict, 15), maxlv=0, keys_weight=10)
        
        # Should create flat structure with keys as their own groups
        expected = {
            'loginBtn': 'loginBtn',
            'submitBtn': 'submitBtn'
        }
        
        assert result == expected
    
    def test_no_common_tokens(self):
        """Test behavior when there are no common tokens between key and group"""
        keys = ['button', 'input']
        supp_dict = {
            'button': 'formPage',
            'input': 'loginPage'
        }
        
        result = compute_nested(keys, (supp_dict, 15), keys_weight=10)
        
        expected = {
            'formPage': {
                'button': 'button'
            },
            'loginPage': {
                'input': 'input'
            }
        }
        
        assert result == expected
    
    def test_complex_camel_case(self):
        """Test complex camelCase token extraction"""
        keys = ['getUserProfileDataBtn', 'setUserPreferencesForm']
        supp_dict = {
            'getUserProfileDataBtn': 'userPage',
            'setUserPreferencesForm': 'userPage'
        }
        
        result = compute_nested(keys, (supp_dict, 15), keys_weight=10)
        
        expected = {
            'userPage': {
                'getProfileDataBtn': 'getUserProfileDataBtn',
                'setPreferencesForm': 'setUserPreferencesForm'
            }
        }
        
        assert result == expected
    
    def test_empty_keys_list(self):
        """Test with empty keys list"""
        result = compute_nested([], ({}, 10))
        assert result == {}
    
    def test_missing_keys_in_dict(self):
        """Test error when keys are missing from supplementary dict"""
        keys = ['loginBtn', 'submitBtn']
        incomplete_dict = {
            'loginBtn': 'loginPage'
            # missing 'submitBtn'
        }
        
        with pytest.raises(ValueError, match="Dictionary missing keys"):
            compute_nested(keys, (incomplete_dict, 10))
    
    def test_invalid_input_types(self):
        """Test error handling for invalid input types"""
        # Test non-list keys
        with pytest.raises(TypeError, match="keys must be a list"):
            compute_nested("not_a_list", ({}, 10))
        
        # Test invalid dict tuple format
        with pytest.raises(TypeError, match="Each dict must be a tuple of"):
            compute_nested(['key'], {'not': 'tuple'})
        
        # Test invalid dict tuple content
        with pytest.raises(TypeError, match="Each dict must be a tuple of"):
            compute_nested(['key'], ({'key': 'value'}, 'not_int'))
    
    def test_three_level_nesting(self):
        """Test deep nesting with three supplementary dictionaries"""
        keys = ['userAdminLoginBtn']
        
        page_dict = {
            'userAdminLoginBtn': 'loginPage'
        }
        
        role_dict = {
            'userAdminLoginBtn': 'adminRole'
        }
        
        section_dict = {
            'userAdminLoginBtn': 'userSection'
        }
        
        result = compute_nested(
            keys, 
            (page_dict, 30), 
            (role_dict, 20), 
            (section_dict, 10), 
            keys_weight=5
        )
        
        expected = {
            'loginPage': {
                'adminRole': {
                    'userSection': {
                        'btn': 'userAdminLoginBtn'
                    }
                }
            }
        }
        
        assert result == expected
    
    def test_flatten_integration(self):
        """Test integration with flatten_dict to verify structure"""
        keys = ['userLoginBtn', 'adminLoginBtn']
        
        page_dict = {
            'userLoginBtn': 'loginPage',
            'adminLoginBtn': 'loginPage'
        }
        
        role_dict = {
            'userLoginBtn': 'userRole',
            'adminLoginBtn': 'adminRole'
        }
        
        result = compute_nested(keys, (page_dict, 20), (role_dict, 15), keys_weight=10)
        flattened = flatten_dict(result)
        
        expected_flattened = {
            'loginPage.userRole.btn': 'userLoginBtn',
            'loginPage.adminRole.btn': 'adminLoginBtn'
        }
        
        assert flattened == expected_flattened
    
    def test_weight_ordering(self):
        """Test that supplementary dicts are processed in weight order"""
        keys = ['userLoginBtn']
        
        # Lower weight dict
        dict1 = {'userLoginBtn': 'userPage'}
        
        # Higher weight dict  
        dict2 = {'userLoginBtn': 'loginSection'}
        
        # Higher weight should be processed first (outer level)
        result = compute_nested(keys, (dict1, 10), (dict2, 20), keys_weight=5)
        
        # Since "loginSection" has higher weight, it should be outer level
        # "userPage" will be inner level 
        # Common tokens will be removed based on weights
        expected = {
            'loginSection': {
                'userPage': {
                    'btn': 'userLoginBtn'  # 'user' and 'login' removed by higher weight groups
                }
            }
        }
        
        assert result == expected


if __name__ == "__main__":
    pytest.main([__file__])
