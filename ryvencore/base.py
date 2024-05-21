"""
This module defines the :code:`Base` class for most internal components,
implementing features such as a unique ID, a system for save and load,
and a very minimal event system.
"""

from bisect import insort
from collections.abc import Iterable, Set, Mapping
from typing import Generic, TypeVar, ParamSpec, Callable, Any
from types import MappingProxyType
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class TypeMeta:
    """Metadata regarding a type. Useful if we want to build packages."""
    package: str
    type_id: str
    
    def identifier(self):
        return f"{self.package}.{self.type_id}"
    
class TypeSerializer(ABC):
    """Serializes/Deserializes an object into JSON compatible dict."""
    
    @classmethod
    def serialize(cls, obj):
        """
        Serializes the type. Defaulted to simply returning the type
        
        This implementation assumes obj is already JSON compatible
        """
        return {'value': obj}
    
    @classmethod
    def deserialize(cls, data: dict):
        """Retrieves the object from the dict"""
        return data['value']
    
    @abstractmethod
    @classmethod
    def default(cls) -> Any:
        pass
    
class IDCtr:
    """
    A simple ascending integer ID counter.
    Guarantees uniqueness during lifetime or the program (not only of the Session).
    This approach is preferred over UUIDs because UUIDs need a networking context
    and require according system support which might not be available everywhere.
    """

    def __init__(self):
        self.ctr = -1

    def count(self):
        """increases the counter and returns the new count. first time is 0"""
        self.ctr += 1
        return self.ctr

    def set_count(self, cnt):
        if cnt < self.ctr:
            raise Exception("Decreasing ID counters is illegal")
        else:
            self.ctr = cnt

EP = ParamSpec('EP')

class Event(Generic[EP]):
    """
    Implements a generalization of the observer pattern, with additional
    priority support. The lower the value, the earlier the callback
    is called. The default priority is 0.
    
    Negative priorities internally to ensure
    precedence of internal observers over all user-defined ones.
    """

    def __init__(self):
        self._slots: dict[int, set] = {}
        self._ordered_slot_pos = []
        self._slot_priorities = {}
        self._one_offs = set()

    def clear(self):
        self._slots: dict[int, set] = {}
        self._ordered_slot_pos = []
        self._slot_priorities = {}
        
    def sub(self, callback: Callable[EP, None], nice=0, one_off=False):
        """
        Registers a callback function. The callback must accept compatible arguments.
        The optional :code:`nice` parameter can be used to set the priority of the
        callback. The lower the priority, the earlier the callback is called.
        :code:`nice` can range from -5 to 10.
        Users of ryvencore are not allowed to use negative priorities.
        """
        assert -5 <= nice <= 10
        assert self._slot_priorities.get(callback) is None

        cb_set = self._slots.get(nice)
        if cb_set is None:
            cb_set = self._slots[nice] = set()
            insort(self._ordered_slot_pos, nice)
            
        cb_set.add(callback)
        if one_off:
            self._one_offs.add(callback)
        self._slot_priorities[callback] = nice

    def unsub(self, callback: Callable[EP, None]):
        """
        De-registers a callback function. The function must have been added previously.
        """
        self.__unsub(callback, True)
    
    def __unsub(self, callback: Callable[EP, None], check_one_off: bool):
        """
        De-registers a function that was added. If check_one_off, attempts to remove
        it as a one_off function. This is an internal function.
        """
        nice = self._slot_priorities[callback]
        cb_set = self._slots[nice]
        cb_set.remove(callback)
        del self._slot_priorities[callback]

        if len(cb_set) == 0:
            del self._slots[nice]
            self._ordered_slot_pos.remove(nice)
        
        if check_one_off and callback in self._one_offs:
            self._one_offs.remove(callback)

    def emit(self, *args: EP.args, **kwargs: EP.kwargs):
        """
        Emits an event by calling all registered callback functions with parameters
        given by :code:`args`.
        """

        # notice we're using the ordered list to run through the events
        for nice in self._ordered_slot_pos:
            for cb in self._slots[nice]:
                cb(*args)
        
        for one_off_func in self._one_offs:
            self.__unsub(one_off_func, False)
        
        self._one_offs.clear()


class NoArgsEvent(Event[[]]):
    """Just wraps the Event[[]] for syntactic sugar. Not usefull in any other way."""
    pass


class Base:
    """
    Base class for all abstract components. It provides:

    Functionality for ID counting:
        - an automatic :code:`GLOBAL_ID` unique during the lifetime of the program
        - a :code:`PREV_GLOBAL_ID` for re-identification after save & load,
          automatically set in :code:`load()`

    Serialization:
        - the :code:`data()` method gets reimplemented by subclasses to serialize
        - the :code:`load()` method gets reimplemented by subclasses to deserialize
        - the static attribute :code:`Base.complete_data_function` can be set to
          a function which extends the serialization process by supplementing the
          data dict with additional information, which is useful in many
          contexts, e.g. a frontend does not need to implement separate save & load
          functions for its GUI components
    """

    # static attributes

    _global_id_ctr = IDCtr()

    # TODO: this produces a memory leak, because the objects are never removed
    #  from the dict. It shouldn't be a problem as long as PREF_GLOBAL_ID is
    #  only used for loading, but I'd be happy to avoid this if possible
    _prev_id_objs = {}

    @classmethod
    def obj_from_prev_id(cls, prev_id: int):
        """returns the object with the given previous id"""
        return cls._prev_id_objs.get(prev_id)

    complete_data_function = lambda data: data

    @staticmethod
    def complete_data(data: dict):
        """
        Invokes the customizable :code:`complete_data_function` function
        on the dict returned by :code:`data`. This does not happen automatically
        on :code:`data()` because it is not always necessary (and might only be
        necessary once, not for each component individually).
        """
        return Base.complete_data_function(data)


    # optional version which, if set, will be stored in :code:`data()`
    version: str = None

    # non-static

    def __init__(self):
        self.global_id = self._global_id_ctr.count()

        # the following attributes are set in :code:`load()`
        self.prev_global_id = None
        self.prev_version = None

    def data(self) -> dict:
        """
        Convert the object to a JSON compatible dict.
        Reserved field names are 'GID' and 'version'.
        """
        return {
            'GID': self.global_id,

            # version optional
            **({'version': self.version}
               if self.version is not None
               else {})
        }

    def load(self, data: dict):
        """
        Recreate the object state from the data dict returned by :code:`data()`.

        Convention: don't call this method in the constructor, invoke it manually
        from outside, if other components can depend on it (and be notified of its
        creation).
        Reason: If another component `X` depends on this one (and
        gets notified when this one is created), `X` should be notified *before*
        it gets notified of creation or loading of subcomponents created during
        this load. (E.g. add-ons need to know the flow before nodes are loaded.)
        """

        if data is not None:
            self.prev_global_id = data['GID']
            self._prev_id_objs[self.prev_global_id] = self
            self.prev_version = data.get('version')


class Identifiable:
    """
    A **class whose definition** can be identified by a unique string.
    
    Essentially, sub-classes must implement the below fields to provide uniqueness per sub-class.
    If none of the fields are given, then the ID of the class is its name, which in general is unique.
    (We might need to change this approach to be <module>.<name> for guaranteed uniqueness)
    """
    
    id_prefix: str = None
    """becomes the first part of the identifier if set; can be useful for grouping identifiables"""
    
    id_name: str = None
    """becomes the last part of the identifier if set; otherwise the class name is used"""
    
    _id: str = None
    """unique node identifier string which is set by _build_identifier"""
    
    legacy_ids: list[str] = []
    """a list of compatible identifiers, useful when you change the class name (and hence the identifier) to provide 
    backward compatibility to load old projects that rely on the old identifier"""
    
    @classmethod
    def id(cls):
        """Returns the id of this identifiable. Useful only after _build_identifier is called."""
        return cls._id

    @classmethod
    def name(cls):
        """Returns the name of this identifiable. It is either the id_name or the __name__"""
        return cls.id_name if cls.id_name else cls.__name__
    
    @classmethod
    def _build_id(cls):
        """
        Sets the __id to be <identifier_prefix>.<name> depending on if they are set.
        If the name is not set the class name is used.
        
        This must result in a unique string
        """

        prefix = f'{cls.id_prefix}.' if cls.id_prefix else ''
        cls._id = f'{prefix}{cls.name()}'
        
        # notice we do not touch the legacy_identifiers


IdType = TypeVar('IdType', bound=Identifiable)  

def find_identifiable(id: str, to_search: Iterable[type[IdType]]):

    for nc in to_search:
        if nc.id() == id:
            return nc
    else:  # couldn't find a identifiable with this identifier => search in legacy_ids
        for nc in to_search:
            if id in nc.legacy_ids:
                return nc
        else:
            raise Exception(
                f'could not find Identifiable class with id: \'{id}\'. '
                f'if you changed your node\'s class name, make sure to add the old '
                f'identifier to the legacy_ids list attribute to provide '
                f'backwards compatibility.'
            )
            

class IdentifiableGroups(Generic[IdType]):
    """
    Groups identifiables by their id prefix and id name. Identifiables with no prefix are groupped under 'global'
    
    Also holds structures for getting an identifiable by its name
    """
    NO_PREFIX_ROOT = 'global'
    
    def __init__(self, ids: Iterable[type[IdType]] = []):
        
        self.__id_set = set[type[IdType]]()
        
        self.__id_dict = dict[str, type[IdType]]()
        self.__id_dict_proxy = MappingProxyType(self.__id_dict)
        
        self.__id_groups: dict[str, dict[str, type[IdType]]] = {
            'global': {}
        }
        self._groups_proxy = MappingProxyType(self.__id_groups)
        
        # init
        for item in ids:
            if not item.id_prefix:
                group = self.__id_groups['global']
            else:
                if not item.id_prefix in self.__id_groups:
                    self.__id_groups[item.id_prefix] = group = {}
                else:
                    group = self.__id_groups[item.id_prefix]
        
            group[item.name()] = item
        
        # events
        self.group_added = Event[str]()
        self.group_removed = Event[str]()
        self.id_added = Event[type[IdType]]()
        self.id_removed = Event[type[IdType]]()
    
    
    def __str__(self) -> str:
        return self.__id_groups.__str__()
    
    @property
    def id_set(self):
        """A set containing all the Identifiables"""
        return self.__id_set
    
    @property
    def id_map(self):
        """A map with layout {id: identifiable}"""
        return self.__id_dict_proxy
    
    @property
    def groups(self):
        """The identifiable groupped by their prefixes"""
        return self._groups_proxy
    
    def add(self, id: IdType):
        """Adds an identifiable to its group. Creates the group if it doesn't exist"""
        
        if id.id() in self.__id_dict:
            return False
        
        if not id.id_prefix:
            group = self.__id_groups['global']
        elif id.id_prefix in self.__id_groups:
            group = self.__id_groups[id.id_prefix]
        else:
            self.__id_groups[id.id_prefix] = group = {}
            self.group_added.emit(id.id_prefix)
        
        group[id.name()] = id
        self.__id_set.add(id)
        self.__id_dict[id.id()] = id
        self.id_added.emit(id)
        
        return True
    
    def remove(self, id: IdType):
        """Removes an identifiable from its group. Deletes the group if it's empty"""
        
        id_in_dict = self.__id_dict.get(id.id())
        if not id_in_dict:
            return False
        
        if not id.id_prefix:
            del self.__id_groups['global'][id.name()]
        else:
            del self.__id_groups[id.id_prefix][id.name()]
            if not self.__id_groups[id.id_prefix]:
                del self.__id_groups[id.id_prefix]
                
                self.group_removed.emit(id.id_prefix)
        
        self.__id_set.remove(id_in_dict)
        del self.__id_dict[id.id()]
        
        self.id_removed.emit(id_in_dict)
          
    def group(self, group_id: str) -> None | Mapping[str, type[IdType]]:
        """Retrieves a specific group. group_id must exist as a valid group."""
        
        if not group_id in self.__id_groups:
            return None
        return MappingProxyType(self.__id_groups[group_id])
    
    def remove_group(self, group_id: str, emit_id_removed=False) -> bool:
        """Removes a group. group_id must exist as a valid group"""
        
        group = self.__id_groups.get(group_id)
        if not group:
            return False
        
        for id in group.values():
            self.__id_set.remove(id)
            del self.__id_dict[id.id()]
            if emit_id_removed:
                self.id_removed.emit(id)
        
        del self.__id_groups[group_id]
        self.group_removed.emit(group_id)
        return True
    
    def groups_from_path(self, path: str):
        """
        Retrieves all groups whose prefix contains the path
        
        Useful for "imitating" sub-groups
        """
        
        return {
            id: group 
            for id, group in self.__id_dict.items()
            if path.startswith(id)
        }
    
    def remove_groups_from_path(self, path: str):
        """
        Removes all groups whos prefix contains the path
        
        Useful for "imitating" sub-groups
        """
        
        to_remove = self.groups_from_path(path)
        for id in to_remove.keys():
            self.remove_group(id)    
        
        
        

    
    
