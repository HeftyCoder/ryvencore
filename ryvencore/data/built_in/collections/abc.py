"""Defines abstract structure data types akin to collections.abc"""

from ...base import _BuiltInData
from ....utils import has_abstractmethods

from collections.abc import (
    Container,
    Hashable,
    Iterable,
    Iterator,
    Reversible,
    Generator,
    Sized,
    Collection,
    Sequence,
    MutableSequence,
    Set,
    MutableSet,
    Mapping,
    MutableMapping,
    MappingView,
    ItemsView,
    KeysView,
    ValuesView,
)

class _BaseStructureData(_BuiltInData):
    """Base class for any collection"""
    
    collection_type = None
    """Type from collections module that the payload must conform to"""
    
    @classmethod
    def instantiable(cls):
        return cls.collection_type and not has_abstractmethods(cls.collection_type)
    
    @classmethod
    def _build_identifier(cls):
        cls.identifier = f'built_in.collections.{cls.__name__}'
        
    @classmethod
    def is_valid_payload(cls, payload):
        return isinstance(payload, cls.collection_type)
    
    def __init__(self, value=None, load_from=None):
        super().__init__(value, load_from)
        
class ContainerData(_BaseStructureData):
    collection_type = Container

class HashableData(_BaseStructureData):
    collection_type = Hashable

class IterableData(_BaseStructureData):
    collection_type = Iterable

class IteratorData(IterableData):
    collection_type = Iterator

class ReversibleData(IterableData):
    collection_type = Reversible

class GeneratorData(IteratorData):
    collection_type = Generator

class SizedData(_BuiltInData):
    collection_type = Sized

class CollectionData(SizedData, IterableData, ContainerData):
    collection_type = Collection

class SequenceData(ReversibleData, CollectionData):
    collection_type = Sequence

class MutableSequenceData(SequenceData):
    collection_type = MutableSequence

class SetData_ABC(CollectionData):
    collection_type = Set

class MutableSetData(SetData_ABC):
    collection_type = MutableSet

class MappingData(CollectionData):
    collection_type = Mapping

class MutableMappingData(MappingData):
    collection_type = MutableMapping

class MappingViewData(SizedData):
    collection_type = MappingView

class ItemsViewData(MappingViewData, SetData_ABC):
    collection_type = ItemsView

class KeysViewData(MappingView, Set):
    collection_type = KeysView
    
class ValuesViewData(MappingViewData, CollectionData):
    collection_type = ValuesView

    