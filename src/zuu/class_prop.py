

class classproperty:
    """A decorator that converts a function into a class property."""
    
    def __init__(self, func):
        self.func = func
        self._setter = None
        
    def __get__(self, obj, owner):
        return self.func(owner)
    
    def __set__(self, obj, value):
        if self._setter is None:
            raise AttributeError("can't set attribute")
        self._setter(type(obj), value)
    
    def setter(self, func):
        """Decorator to define the setter for the class property."""
        self._setter = func
        return self
    

class AssignablePropertyMeta(type):
    """Metaclass that enables class-level assignment to go through descriptors."""
    
    def __setattr__(cls, name, value):
        # Check if the attribute exists and is an assignableClassProperty with setter
        if hasattr(cls, name):
            # Walk the MRO to find the actual class that defines this property
            for base_cls in cls.__mro__:
                attr = base_cls.__dict__.get(name)
                if isinstance(attr, assignableClassProperty) and attr._setter is not None:
                    # Found the defining class - use its setter but pass the current class
                    attr._setter(cls, value)
                    return
        # Default behavior for other attributes
        super().__setattr__(name, value)


class assignableClassProperty:
    """A decorator that converts a function into a class property with class-level assignment support."""
    
    def __init__(self, func):
        self.func = func
        self._setter = None
        self._owner_class = None  # Hidden signature to track the defining class
        
    def __set_name__(self, owner, name):
        """Called when the descriptor is assigned to a class attribute."""
        self._owner_class = owner
        self._name = name
        
    def __get__(self, obj, owner):
        return self.func(owner)
    
    def __set__(self, obj, value):
        if self._setter is None:
            raise AttributeError("can't set attribute")
        # Handle both instance and class-level setting
        if obj is None:
            # This shouldn't normally happen, but handle it just in case
            raise AttributeError("can't set attribute on None")
        self._setter(type(obj), value)
    
    def setter(self, func):
        """Decorator to define the setter for the class property."""
        self._setter = func
        return self