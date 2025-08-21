import pytest
from zuu.class_prop import classproperty, assignableClassProperty, AssignablePropertyMeta


class TestClassProperty:
    """Test the classproperty decorator functionality."""
    
    def test_basic_class_property_getter(self):
        """Test that classproperty works as a basic getter."""
        class TestClass:
            _value = "test_value"
            
            @classproperty
            def class_attr(cls):
                return cls._value
        
        assert TestClass.class_attr == "test_value"
        
        # Should work on instances too
        instance = TestClass()
        assert instance.class_attr == "test_value"
    
    def test_class_property_with_different_classes(self):
        """Test that classproperty returns different values for different classes."""
        class BaseClass:
            _name = "base"
            
            @classproperty
            def name(cls):
                return cls._name
        
        class ChildClass(BaseClass):
            _name = "child"
        
        assert BaseClass.name == "base"
        assert ChildClass.name == "child"
    
    def test_class_property_setter_basic(self):
        """Test basic setter functionality."""
        class TestClass:
            _value = "initial"
            
            @classproperty
            def class_attr(cls):
                return cls._value
            
            @class_attr.setter
            def class_attr(cls, value):
                cls._value = value
        
        assert TestClass.class_attr == "initial"
        TestClass.class_attr = "modified"
        assert TestClass.class_attr == "modified"
    
    def test_class_property_setter_on_instance(self):
        """Test that setter works when called on instance."""
        class TestClass:
            _value = "initial"
            
            @classproperty
            def class_attr(cls):
                return cls._value
            
            @class_attr.setter
            def class_attr(cls, value):
                cls._value = value
        
        instance = TestClass()
        assert instance.class_attr == "initial"
        
        instance.class_attr = "modified"
        assert instance.class_attr == "modified"
        assert TestClass.class_attr == "modified"  # Should affect the class
    
    def test_setter_without_getter_raises_error(self):
        """Test that trying to set without a setter raises AttributeError on instances."""
        class TestClass:
            @classproperty
            def readonly_attr(cls):
                return "readonly"
        
        # Class-level assignment bypasses the descriptor and replaces it
        TestClass.readonly_attr = "new_value"
        assert TestClass.readonly_attr == "new_value"
        
        # Reset the class for instance testing
        class TestClass2:
            @classproperty
            def readonly_attr(cls):
                return "readonly"
        
        # Instance-level assignment should raise AttributeError
        instance = TestClass2()
        with pytest.raises(AttributeError, match="can't set attribute"):
            instance.readonly_attr = "new_value"
    
    def test_class_property_with_complex_computation(self):
        """Test classproperty with complex getter logic."""
        class TestClass:
            _items = ["a", "b", "c"]
            
            @classproperty
            def item_count(cls):
                return len(cls._items)
            
            @classproperty
            def formatted_items(cls):
                return ", ".join(cls._items)
        
        assert TestClass.item_count == 3
        assert TestClass.formatted_items == "a, b, c"
        
        TestClass._items.append("d")
        assert TestClass.item_count == 4
        assert TestClass.formatted_items == "a, b, c, d"
    
    def test_class_property_inheritance(self):
        """Test that classproperty works properly with inheritance."""
        class ParentClass:
            _base_value = "parent"
            
            @classproperty
            def inherited_prop(cls):
                return f"{cls._base_value}_property"
        
        class ChildClass(ParentClass):
            _base_value = "child"
        
        assert ParentClass.inherited_prop == "parent_property"
        assert ChildClass.inherited_prop == "child_property"
        
        parent_instance = ParentClass()
        child_instance = ChildClass()
        
        assert parent_instance.inherited_prop == "parent_property"
        assert child_instance.inherited_prop == "child_property"
    
    def test_class_property_with_setter_inheritance(self):
        """Test that classproperty with setter works with inheritance."""
        class ParentClass:
            _value = "parent_initial"
            
            @classproperty
            def shared_prop(cls):
                return cls._value
            
            @shared_prop.setter
            def shared_prop(cls, value):
                cls._value = f"{value}_parent"
        
        class ChildClass(ParentClass):
            _value = "child_initial"
        
        assert ParentClass.shared_prop == "parent_initial"
        assert ChildClass.shared_prop == "child_initial"
        
        # Instance-level setting (goes through descriptor)
        parent_instance = ParentClass()
        parent_instance.shared_prop = "modified"
        assert ParentClass.shared_prop == "modified_parent"
        assert ChildClass.shared_prop == "child_initial"  # Should remain unchanged
        
        child_instance = ChildClass()
        child_instance.shared_prop = "child_modified"
        assert ChildClass.shared_prop == "child_modified_parent"
        assert ParentClass.shared_prop == "modified_parent"  # Should remain unchanged
    
    def test_multiple_class_properties(self):
        """Test multiple classproperty decorators on the same class."""
        class TestClass:
            _name = "test"
            _version = "1.0"
            
            @classproperty
            def name(cls):
                return cls._name
            
            @classproperty
            def version(cls):
                return cls._version
            
            @classproperty
            def full_name(cls):
                return f"{cls._name}_v{cls._version}"
        
        assert TestClass.name == "test"
        assert TestClass.version == "1.0"
        assert TestClass.full_name == "test_v1.0"
    
    def test_class_property_with_none_return(self):
        """Test classproperty that returns None."""
        class TestClass:
            @classproperty
            def none_prop(cls):
                return None
        
        assert TestClass.none_prop is None
        
        instance = TestClass()
        assert instance.none_prop is None
    
    def test_class_property_with_exception_in_getter(self):
        """Test that exceptions in getter are propagated correctly."""
        class TestClass:
            @classproperty
            def error_prop(cls):
                raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            TestClass.error_prop
        
        instance = TestClass()
        with pytest.raises(ValueError, match="Test error"):
            instance.error_prop
    
    def test_class_property_with_exception_in_setter(self):
        """Test that exceptions in setter are propagated correctly."""
        class TestClass:
            _value = "initial"
            
            @classproperty
            def error_prop(cls):
                return cls._value
            
            @error_prop.setter
            def error_prop(cls, value):
                if value == "invalid":
                    raise ValueError("Invalid value")
                cls._value = value
        
        assert TestClass.error_prop == "initial"
        
        # Test instance-level setting (goes through descriptor)
        instance = TestClass()
        instance.error_prop = "valid"
        assert TestClass.error_prop == "valid"
        
        with pytest.raises(ValueError, match="Invalid value"):
            instance.error_prop = "invalid"
    
    def test_class_property_descriptor_protocol(self):
        """Test that classproperty implements the descriptor protocol correctly."""
        class TestClass:
            _value = "descriptor_test"
            
            @classproperty
            def desc_prop(cls):
                return cls._value
        
        # Test __get__ with None obj (class access)
        descriptor = TestClass.__dict__['desc_prop']
        assert descriptor.__get__(None, TestClass) == "descriptor_test"
        
        # Test __get__ with instance obj
        instance = TestClass()
        assert descriptor.__get__(instance, TestClass) == "descriptor_test"
    
    def test_class_property_setter_chaining(self):
        """Test that setter decorator returns the original classproperty for chaining."""
        class TestClass:
            _value = "initial"
            
            @classproperty
            def chainable_prop(cls):
                return cls._value
        
        # The setter should return the original classproperty
        original_prop = TestClass.__dict__['chainable_prop']
        result = original_prop.setter(lambda cls, value: setattr(cls, '_value', value))
        
        assert isinstance(result, classproperty)
        assert result is original_prop
    
    def test_class_level_vs_instance_level_assignment(self):
        """Test the difference between class-level and instance-level assignment."""
        class TestClass:
            _value = "initial"
            
            @classproperty
            def test_prop(cls):
                return cls._value
            
            @test_prop.setter
            def test_prop(cls, value):
                cls._value = f"setter_{value}"
        
        # Initial state
        assert TestClass.test_prop == "initial"
        assert isinstance(TestClass.__dict__['test_prop'], classproperty)
        
        # Instance-level assignment (goes through setter)
        instance = TestClass()
        instance.test_prop = "instance_value"
        assert TestClass.test_prop == "setter_instance_value"
        assert isinstance(TestClass.__dict__['test_prop'], classproperty)
        
        # Reset for next test
        TestClass._value = "reset"
        
        # Class-level assignment (bypasses descriptor, replaces it)
        TestClass.test_prop = "class_direct"
        assert TestClass.test_prop == "class_direct"
        assert TestClass.__dict__['test_prop'] == "class_direct"  # No longer a descriptor
        assert TestClass._value == "reset"  # _value unchanged


class TestAssignableClassProperty:
    """Test the assignableClassProperty decorator with metaclass functionality."""
    
    def test_basic_assignable_class_property(self):
        """Test basic functionality of assignableClassProperty."""
        class TestClass(metaclass=AssignablePropertyMeta):
            _value = "initial"
            
            @assignableClassProperty
            def class_attr(cls):
                return cls._value
            
            @class_attr.setter
            def class_attr(cls, value):
                cls._value = f"setter_{value}"
        
        assert TestClass.class_attr == "initial"
        
        # Instance assignment should work
        instance = TestClass()
        instance.class_attr = "instance_set"
        assert TestClass.class_attr == "setter_instance_set"
        
        # Reset for class assignment test
        TestClass._value = "reset"
        
        # Class assignment should now work through the setter
        TestClass.class_attr = "class_set"
        assert TestClass.class_attr == "setter_class_set"
        assert isinstance(TestClass.__dict__['class_attr'], assignableClassProperty)
    
    def test_assignable_without_setter(self):
        """Test that assignable property without setter still prevents setting."""
        class TestClass(metaclass=AssignablePropertyMeta):
            @assignableClassProperty
            def readonly_prop(cls):
                return "readonly"
        
        # Reading should work
        assert TestClass.readonly_prop == "readonly"
        
        # Class assignment should still replace descriptor (no setter defined)
        TestClass.readonly_prop = "replaced"
        assert TestClass.readonly_prop == "replaced"
        
        # Reset and test instance assignment
        class TestClass2(metaclass=AssignablePropertyMeta):
            @assignableClassProperty
            def readonly_prop(cls):
                return "readonly"
        
        instance = TestClass2()
        with pytest.raises(AttributeError, match="can't set attribute"):
            instance.readonly_prop = "should_fail"
    
    def test_assignable_inheritance(self):
        """Test assignable class property with inheritance."""
        class ParentClass(metaclass=AssignablePropertyMeta):
            _value = "parent_initial"
            
            @assignableClassProperty
            def inherited_prop(cls):
                return cls._value
            
            @inherited_prop.setter
            def inherited_prop(cls, value):
                cls._value = f"parent_{value}"
        
        class ChildClass(ParentClass):
            _value = "child_initial"
        
        assert ParentClass.inherited_prop == "parent_initial"
        assert ChildClass.inherited_prop == "child_initial"
        
        # Class-level assignment on parent
        ParentClass.inherited_prop = "modified"
        assert ParentClass.inherited_prop == "parent_modified"
        assert ChildClass.inherited_prop == "child_initial"  # Unchanged
        
        # Class-level assignment on child  
        ChildClass.inherited_prop = "child_modified"
        # Now with proper MRO handling, the setter should be called correctly
        # The setter gets the ChildClass and formats the value as "parent_child_modified"
        assert ChildClass.inherited_prop == "parent_child_modified"  
        assert ParentClass.inherited_prop == "parent_modified"  # Unchanged
    
    def test_mixed_properties(self):
        """Test class with both regular and assignable class properties."""
        class TestClass(metaclass=AssignablePropertyMeta):
            _regular_value = "regular_initial"
            _assignable_value = "assignable_initial"
            
            @classproperty
            def regular_prop(cls):
                return cls._regular_value
            
            @assignableClassProperty  
            def assignable_prop(cls):
                return cls._assignable_value
            
            @assignable_prop.setter
            def assignable_prop(cls, value):
                cls._assignable_value = f"set_{value}"
        
        # Both should work for getting
        assert TestClass.regular_prop == "regular_initial"
        assert TestClass.assignable_prop == "assignable_initial"
        
        # Regular property class assignment replaces descriptor
        TestClass.regular_prop = "regular_replaced"
        assert TestClass.regular_prop == "regular_replaced"
        
        # Assignable property class assignment goes through setter
        TestClass.assignable_prop = "assignable_set"
        assert TestClass.assignable_prop == "set_assignable_set"
        assert isinstance(TestClass.__dict__['assignable_prop'], assignableClassProperty)
