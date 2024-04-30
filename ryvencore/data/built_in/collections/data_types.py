"""Defines implemented structure data types found in Python's Standard Library"""

from .abc import (
    MutableSequenceData,
    SequenceData,
    MappingData,
    MutableMappingData,
    MutableSetData,
    SetData_ABC,
)
from collections import OrderedDict, deque

class ListData(MutableSequenceData):
    collection_type = list
    
    def __init__(self, value: list = [], load_from=None):
        super().__init__(value, load_from)

class TupleData(SequenceData):
    collection_type = tuple
    
    def __init__(self, value:tuple = (), load_from=None):
        super().__init__(value, load_from)

class DictData(MutableMappingData):
    collection_type = dict
    
    def __init__(self, value: dict = {}, load_from=None):
        super().__init__(value, load_from)

class OrderedDictData(MutableMappingData):
    collection_type = OrderedDict
    
    def __init__(self, value: OrderedDict = OrderedDict(), load_from=None):
        super().__init__(value, load_from)

class SetData(MutableSetData):
    collection_type = set
    
    def __init__(self, value: set = set(), load_from=None):
        super().__init__(value, load_from)

class FrozenSetData(SetData_ABC):
    collection_type = frozenset

    def __init__(self, value: frozenset = frozenset(), load_from=None):
        super().__init__(value, load_from)
        
class QueueData(MutableSequenceData):
    collection_type = deque
    
    def __init__(self, value: deque = deque(), load_from=None):
        super().__init__(value, load_from)




