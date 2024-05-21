from __future__ import annotations
from packaging.version import parse as parse_version
from ... import Node, AddOn, Flow
from ...base import Event
from ...info_msgs import InfoMsgs
from typing import Callable, Any
from types import MappingProxyType
from ...base import TypeMeta, TypeSerializer

ADDON_VERSION = '0.4'
# TODO: replace print_err with InfoMsgs
    
class VarType:
    """
    Holds all the information for a subscribed type to the Variables Addon.
    
    Essentially, one can define their own variable types for use with the Addon.
    Only defined variable types that are registered in the Addon are allowed to
    be used.
    """
    def __init__(self, val_type: type, type_meta: TypeMeta, type_ser: type[TypeSerializer]):
        self._type_meta = type_meta
        self._type_ser = type_ser
        self._val_type = val_type
    
    # Access to internal objects
    @property
    def type_meta(self):
        return self._type_meta
    
    @property
    def serializer(self):
        return self._type_ser
    
    @property
    def val_type(self):
        return self._val_type
    
    # Easier access to internals
    @property
    def name(self):
        return self._type_meta.type_id
    
    @property
    def package(self):
        return self._type_meta.package
    
    @property
    def identifier(self):
        return self._type_meta.identifier()
    
    def serialize(self, obj):
        return self._type_ser.serialize(obj)
    
    def deserialize(self, data: dict):
        return self._type_ser.deserialize(data)
    
    def default(self):
        return self._type_ser.default()
    
    def is_valid_val(self, val):
        return isinstance(val, self._val_type)
    
        
class Variable:
    """
    Implementation of flow variables. This implementation relies on
    registering valid data types for use utilizing the VarsAddon API.
    """

    def __init__(self, addon: VarsAddon, flow: Flow, name, val_type: type | str, data=None, val=None ):
        self._addon = addon
        self._flow = flow
        self._name = name
        
        self._var_type = self._addon.var_type(val_type)
        if not self._var_type:
            raise ValueError(f"{val_type} is not registered in the Addon!")
        
        self._value = self._var_type.default()
        
        if val:
            self.value = val 
        
        if data:
            self.value = self._var_type.deserialize(data)
    
    def __str__(self):
        return str(self.value)

    @property
    def value(self):
        """Retrieves the value of the variable"""
        return self._value
    
    @value.setter
    def value(self, val):
        """Sets the value of the variable"""
        self.set(val)
    
    @property
    def name(self):
        return self._name
    
    @property
    def addon(self):
        return self._addon
    
    @property
    def flow(self):
        return self._flow
        
    @property
    def subscriber(self):
        return self.addon.var_sub(self.flow, self.name)
    
    @property
    def var_type(self):
        return self._var_type
    
    @var_type.setter
    def var_type(self, value: VarType):
        pass
    
    def set(self, val, silent=False):
        """
        Sets the value of the variable and notifies that the value is changed.
        """
        if not self._var_type.is_valid_val(val):
            raise ValueError(f"Value must be of type {self._var_type.val_type}, but received {type(val)} instead!")
        old_val = self._value
        self._value = val
        if not silent:
            self.addon.update_subscribers(self.flow, self._name)
            self.addon.var_value_changed.emit(self, old_val)
    
    def set_val_type(self, val_type, value=None, load_from=None, silent=False):
        """
        Sets the underlying VarType using a value type, e.g. int. The value type must be
        registered in the Addon beforehand.
        """
        var_type = self._addon.var_type(val_type)
        if not var_type:
            raise ValueError(f"{val_type} is not registered in the Addon or is None!")
        self.set_var_type(var_type, value, load_from, silent)
    
    def set_var_type(self, var_type: VarType, value=None, load_from=None, silent=False):
        """Sets the VarType for this variable"""
        if not var_type:
            raise ValueError(f"{var_type} cannot be None")
        
        old_vartype = self._var_type
        self._var_type = var_type
        # do not set anything before ensuring that everything works correctly
        val = self._var_type.default()
        if value:
            val = value
        if load_from:
            val = self._var_type.deserialize(load_from)
        
        old_val = self.value
        self.set(val, True)
        if not silent:
             self.addon.update_subscribers(self.flow, self._name)
             self.addon.var_type_changed.emit(self, old_vartype)
                     
    def update_subscribers(self):
        return self.addon.update_subscribers(self.flow, self._name)
    
    def data(self):
        return {
            'name': self.name,
            'var_type': self.var_type.identifier() if self.var_type else None,
            'value': self.var_type.serialize(self._value)
        }
    
    def load(self, data: dict):
        """Loads the variable from a JSON compatible dict"""
        self._name = data['name']
        self._var_type = self.addon.var_type(data['var_type'])
        self._value = self.var_type.deserialize(data['value'])
    
    
class VarSubscriber:
    """Simple class to handle subscriptions for a variable"""
    
    def __init__(self, var: Variable):
        self.variable = var
        self.subscriptions: list[tuple[Node, Callable[[Variable], None]]] = []
        """The subscriptions are a callback that is a method on a node"""


class VarsAddon(AddOn):
    """
    This addon provides a simple variable system.

    It provides an API to create Variable objects which can wrap any Python object,
    provided the object's type has been registered in the Addon beforehand.

    Nodes can subscribe to variable names with a callback that is executed once a
    variable with that name changes or is created. The callback must be a method of
    the node, so the subscription can be re-established on loading.

    This way nodes can react to changes of data and non-trivial data-flow is introduced,
    meaning that data dependencies are determined also by variable subscriptions and not
    purely by the edges in the graph anymore. This can be useful, but it can also prevent
    optimization. Variables are flow-local.

    >>> import ryvencore as rc
    >>>
    >>> class MyNode(rc.Node):
    ...     init_outputs = []
    ...
    ...     def __init__(self, params):
    ...         super().__init__(params)
    ...
    ...         self.Vars = self.get_addon('Variables')
    ...         self.var_val = None
    ...
    ...     def place_event(self):
    ...         self.Vars.subscribe(self, 'var1', self.var1_changed)
    ...         self.var_val = self.Vars.var(self.flow, 'var1').get()
    ...
    ...     def var1_changed(self, val):
    ...         print('var1 changed!')
    ...         self.var_val = val
    >>>
    >>> s = rc.Session()
    >>> s.register_node_type(MyNode)
    >>> f = s.create_flow('main')
    >>>
    >>> Vars = s.addons['Variables']
    >>> v = Vars.create_var(f, 'var1', None)
    >>>
    >>> n1 = f.create_node(MyNode)
    >>> v.set(42)
    var1 changed!
    >>> print(n1.var_val)
    42
    """

    _name = 'Variables'
    version = ADDON_VERSION

    def __init__(self):
        AddOn.__init__(self)

        self.flow_variables: dict[Flow, dict[str, VarSubscriber]] = {}
        
        # nodes can be removed and re-added, so we need to keep track of the broken
        # subscriptions when nodes get removed, because they might get re-added
        # in which case we need to re-establish their subscriptions
        # dict[Node, dict[variable_name, callback_name]]
        self.removed_subscriptions: dict[Node, dict[str, str]] = {}

        # state data of variables that need to be recreated once their flow is
        # available, see :code:`on_flow_created()`
        self.flow_vars__pending: dict[int, dict] = {}
        
        # subscribed types that can be variables
        self._var_types: dict[type, VarType] = {}
        self._var_types_proxy = MappingProxyType(self._var_types)
        self._var_type_ids: dict[str, VarType] = {}
        self._var_type_ids_proxy = MappingProxyType(self._var_type_ids_proxy)
        
        # events
        self._var_created = Event[Variable]()
        self._var_deleted = Event[Variable, VarSubscriber]()
        self._var_renamed = Event[Variable, str]()
        self._var_value_changed = Event[Variable, Any]()
        self._var_type_changed = Event[Variable, Any]()
        self._var_data_loaded = Event[Variable]()
    
    @property
    def var_types(self):
        return self._var_types_proxy
    
    @property
    def var_type_ids(self):
        return self._var_type_ids_proxy
    
    @property
    def var_created(self):
        """
        Event emitted when a variable is created
        
        args: Variable
        """
        return self._var_created 
    
    @property
    def var_deleted(self):
        """
        Event emitted when a variable is deleted
        
        args: Variable
        """
        return self._var_deleted
    
    @property
    def var_value_changed(self):
        """
        Event emitted when a variable's value changes
        
        args: Variable, old_value
        """
        return self._var_value_changed
    
    @property
    def var_type_changed(self):
        """
        Event emitted when a variable's data type is changed
        
        args: Variable, data_type: Data
        """
        
        return self._var_type_changed
        
    @property
    def var_renamed(self):
        """
        Event emitted when a variable's name is changed
        
        args: Variable, old_name: 
        """
        return self._var_renamed
    
    @property
    def var_data_loaded(self):
        """
        Event emitted when a variable has changed due to data loading
        
        args: Variable
        """
        return self._var_data_loaded
    
    def var_type(self, id: type | str):
        if isinstance(id, type):
            return self._var_types.get(id)
        elif isinstance(id, str):
            return self._var_type_ids.get(id)
        return None
    
    def register_var_type(self, t: type, type_id: str, package: str, serializer: type[TypeSerializer]):
        """
        A function that registers various data types to be valid variables.
        
        This could be used in the future to import a whole range of data types for variables
        automatically. However, it is left up to the user.
        """
        type_meta = TypeMeta(package, type_id)
        if t in self._var_types:
            raise KeyError(f"{t} with id {type_meta.identifier()} already registered!")
        
        var_type = VarType(t, type_meta, serializer)
        self._var_types[t] = var_type
        self._var_type_ids[type_meta.identifier()] = var_type
        
    """
    flow management
    """

    def on_flow_created(self, flow):
        self.flow_variables[flow] = {}
        if flow.prev_global_id in self.flow_vars__pending:
            for name, data in self.flow_vars__pending[flow.prev_global_id].items():
                self.create_var(flow, name, load_from=data)
            del self.flow_vars__pending[flow.prev_global_id]
        
    def on_flow_deleted(self, flow):
        del self.flow_variables[flow]

    """
    subscription management
    """

    def on_node_added(self, node):
        """
        Reconstruction of subscriptions.
        """

        # if node had subscriptions previously (so it was removed)
        if node in self.removed_subscriptions:
            for name, cb_name in self.removed_subscriptions[node].items():
                self.subscribe(node, name, getattr(node, cb_name))
            del self.removed_subscriptions[node]

        # otherwise, check if it has load data and reconstruct subscriptions
        elif node.load_data and 'Variables' in node.load_data:
            for name, cb_name in node.load_data['Variables']['subscriptions'].items():
                self.subscribe(node, name, getattr(node, cb_name))

    def on_node_removed(self, node):
        """
        Remove all subscriptions of the node.
        """

        # store subscription in removed_subscriptions
        # because the node might get re-added later
        self.removed_subscriptions[node] = {}

        for name, v_sub in self.flow_variables[node.flow].items():
            for (n, cb) in v_sub.subscriptions:
                if n == node:
                    self.removed_subscriptions[node][name] = cb.__name__
                    self.unsubscribe(node, name, cb)

    """
    variables api
    """

    def var_name_valid(self, flow, name: str) -> bool:
        """
        Checks if :code:`name` is a valid variable identifier and hasn't been take yet.
        """

        return name.isidentifier() and not self.var_exists(flow, name)

    def rename_var(self, flow: Flow, old_name: str, new_name: str, silent=False) -> bool:
        """Renames the variable if it exists"""
        
        if not self.var_exists(flow, old_name) or not new_name.isidentifier():
            return False
        
        v_sub = self.flow_variables[flow][old_name]
        del self.flow_variables[flow][old_name]
        
        v_sub.variable._name = new_name
        self.flow_variables[flow][new_name] = v_sub
        
        if not silent:
            self._var_renamed.emit(v_sub.variable, old_name)
        return True
    
    def add_var(self, flow: Flow, var_sub: VarSubscriber):
        """Forcibly adds a var. Helpful for undo"""
        self.flow_variables[flow][var_sub.variable.name] = var_sub
    
    def remove_var(self, flow: Flow, var: Variable):
        """Forcibly removes a var if it exists. Helpful for undo"""
        if self.var_exists(flow, var.name):
            del self.flow_variables[flow][var.name]
        
    def create_var(self, flow: Flow, name: str, val=None, load_from=None, silent=False) -> Variable | None:
        """
        Creates and returns a new variable and None if the name isn't valid.
        """

        if not self.var_name_valid(flow, name):
            raise ValueError(f"Name: <{name}> already exists or is not a proper python identifier")
        
        v = Variable(self, flow, name, val, load_from)
        v_sub = VarSubscriber(v)
        
        self.flow_variables[flow][name] = v_sub
        
        if not silent:
            self._var_created.emit(v)
        return v

    def delete_var(self, flow: Flow, name: str, silent=False):
        """
        Deletes a variable and causes subscription update. Subscriptions are preserved.
        """
        if not self.var_exists(flow, name):
            raise KeyError(f"Variable <{name}> doesn't exist!")

        v_sub = self.flow_variables[flow][name]
        del self.flow_variables[flow][name]
        
        if not silent:
            self._var_deleted.emit(v_sub.variable, v_sub)

    def change_var_value(self, flow: Flow, name: str, value=None, silent=False):
        """Changes a variables value"""
        v = self.var(flow, name)
        v.set(value, silent)
    
    def change_val_type(self, flow: Flow, name: str, val_type: type, value=None, data: dict = None, silent=False):
        """Changes a variables underlying variable type based on a value type"""
        v = self.var(flow, name)
        v.set_val_type(val_type, value, data, silent)
    
    def set_var_from_data(self, flow: Flow, name: str, data: dict, silent=False):
        """Loads a variable's value with serialized data"""
        v = self.var(flow, name)
        v.load(data)
        
        if not silent:
            self._var_data_loaded.emit(v)
    
    def var_exists(self, flow, name: str) -> bool:
        return flow in self.flow_variables and name in self.flow_variables[flow]

    def var(self, flow, name: str) -> Variable:
        """Returns the variable with the given name."""
        return self.flow_variables[flow][name].variable
    
    def get_var(self, flow, name: str) -> Variable | None:
        """Returns the variable with the given name or None."""
        if not self.var_exists(flow, name):
            return None
        return self.var(flow, name)
    
    def var_sub(self, flow, name: str) -> VarSubscriber | None:
        """Returns the wrapper that holds the variable and its subscribers"""
        if self.var_exists(flow, name):
            return self.flow_variables[flow][name]
    
    def update_subscribers(self, flow, name: str):
        """
        Called when a Variable object changes or when the var is created or deleted.
        """

        v_sub = self.flow_variables[flow][name]
        v = v_sub.variable
        
        for (node, cb) in v_sub.subscriptions:
            cb(v)

    def subscribe(self, node: Node, name: str, callback):
        """
        Subscribe to a variable. ``callback`` must be a method of the node.
        """
        if not self.var_exists(node.flow, name):
            # print_err(f'Variable {name} does not exist.')
            return

        self.flow_variables[node.flow][name].subscriptions.append((node, callback))

    def unsubscribe(self, node: Node, name: str, callback):
        """
        Unsubscribe from a variable.
        """
        if not self.var_exists(node.flow, name):
            # print_err(f'Variable {name} does not exist.')
            return

        self.flow_variables[node.flow][name].subscriptions.remove((node, callback))

    """
    serialization
    """

    def extend_node_data(self, node, data: dict):
        """
        Extends the node data with the variable subscriptions.
        """

        if self.flow_variables.get(node.flow) == {}:
            return

        data['Variables'] = {
            'subscriptions': {
                name: cb.__name__
                for name, v_sub in self.flow_variables[node.flow].items()
                for (n, cb) in v_sub.subscriptions
                if node == n
            }
        }

    def get_state(self) -> dict:
        """"""
        
        return {
            f.global_id: {
                name: v_sub.variable.data()
                for name, v_sub in self.flow_variables[f].items()
            }
            for f in self.flow_variables.keys()
        }

    def set_state(self, state: dict, version: str):
        """"""

        if parse_version(version) < parse_version('0.4'):
            
            InfoMsgs.write_err('Variables addon state version too old, skipping')
            return

        # JSON converts int keys to strings, so we need to convert them back
        state = {
            int(flow_id): flow_vars
            for flow_id, flow_vars in state.items()
        }

        self.flow_vars__pending = state

