import datetime
import os
from types import MappingProxyType
from typing import TypedDict
from zuu.simple_dict import deep_get, deep_set, deep_pop
from hashlib import sha1

_doesNotExist = object()
    

class DiffSet(TypedDict):
    key: str
    stamp: int | None
    previous: str | None
    new: str | None


class DiffDict:
    """
    a dict that tracks changes
    """

    def __init__(
        self, data: dict = None, hashFunc: callable = sha1, stamp: bool = True,
        separator : str = "/"
    ):
        if data is None:
            data = {}
        self.__data = data
        self.__changes: list[DiffSet] = []
        self.__keysums = {}
        self.__hashFunc = hashFunc
        self.__DoStamp = stamp
        self.__useHexCheck = False
        self.__separator = separator
        self.__callbacks = []

    def prune_changes(self, keep: int = 256):
        if keep <= 0:
            self.__changes = []
        else:
            self.__changes = self.__changes[-keep:]

    def add_callback(self, callback: callable):
        self.__callbacks.append(callback)

    @property
    def changes(self):
        return MappingProxyType({
            "all" : self.__changes,
            "last" : self.__changes[-1] if self.__changes else None
        })
    

    @property
    def useHexCheck(self):
        return self.__useHexCheck

    @useHexCheck.setter
    def useHexCheck(self, value):
        self.__useHexCheck = value

    def __compare(self, key, val1, val2, hash1=_doesNotExist, hash2=_doesNotExist):
        if key in self.__keysums:
            hash1 = self.__keysums[key]

        if val1 is not _doesNotExist and hash1 is _doesNotExist:
            if isinstance(val1, (str, int, float)):
                hash1 = str(val1)
            else:
                hash1 = self.__hashFunc(str(val1).encode()).hexdigest()

        if val2 is not _doesNotExist and hash2 is _doesNotExist:
            if isinstance(val2, (str, int, float)):
                hash2 = str(val2)
            else:    
                hash2 = self.__hashFunc(str(val2).encode()).hexdigest()

        if hash1 is not _doesNotExist and hash2 is not _doesNotExist:
            if hash1 == hash2:
                return False

        # Update keysums before recording the change
        if hash1 is not _doesNotExist and val2 is _doesNotExist:
            # deletion
            self.__keysums.pop(key, None)
        elif hash2 is not _doesNotExist:
            self.__keysums[key] = hash2

        self.__changes.append(
            DiffSet(
                key=key,
                stamp=datetime.datetime.now().timestamp() if self.__DoStamp else None,
                previous=hash1 if hash1 is not _doesNotExist else None,
                new=hash2 if hash2 is not _doesNotExist else None,
            )
        )
        if len(self.__callbacks) > 0:
            for callback in self.__callbacks:
                callback(self)

        return True
    
    def updateAtKey(self, key: str):
        """
        Notify the DiffDict that an object at the given key has been modified externally.
        This will trigger a hash comparison and record a change if the object has indeed changed.
        
        Args:
            key: The key where the object was modified
            
        Raises:
            KeyError: If the key doesn't exist in the dictionary
        """
        current_value = deep_get(self.__data, key, self.__separator, _doesNotExist)
        if current_value is _doesNotExist:
            raise KeyError(f"Key '{key}' not found")
        
        # Get the stored hash and force a comparison with the current value
        # This will detect if the object has been modified externally
        old_hash = self.__keysums.get(key, _doesNotExist)
        self.__compare(key, current_value, current_value, hash1=old_hash)

    def __setitem__(self, key, value):
        # get the previous value
        previousVal = self.__data.get(key, _doesNotExist)
        if not self.__useHexCheck and previousVal == value:
            return

        # Check if the value is the same
        if self.__compare(key, previousVal, value):
            deep_set(self.__data, key, value, self.__separator)

    def pop(self, key, default=_doesNotExist):
        """
        pop value essentially removes the record and calls 
        """
        previousVal = deep_get(self.__data, key, self.__separator, _doesNotExist)
        if previousVal is _doesNotExist:
            if default is _doesNotExist:
                raise KeyError(f"Key '{key}' not found")
            return default
        self.__compare(key, previousVal, _doesNotExist)
        deep_pop(self.__data, key, self.__separator)
        return previousVal

    def __getitem__(self, key):
        res = deep_get(self.__data, key, self.__separator, _doesNotExist)
        if res is _doesNotExist:
            raise KeyError(f"Key '{key}' not found")
        return res

    def __contains__(self, key):
        return deep_get(self.__data, key, self.__separator, _doesNotExist) is not _doesNotExist
    
    def __delitem__(self, key):
        self.pop(key)

    def __len__(self):
        return len(self.__data)
    
