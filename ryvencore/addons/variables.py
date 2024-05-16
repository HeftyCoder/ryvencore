from __future__ import annotations
from packaging.version import parse as parse_version
from .. import Node, Data, AddOn, Flow
from ..base import Event
from ..info_msgs import InfoMsgs
from typing import Callable, Any

ADDON_VERSION = '0.4'
# TODO: replace print_err with InfoMsgs


class Variable:
    """
    Implementation of flow variables.
    A Variable can currently only hold pickle serializable data.
    Storing other data will break save&load.
    """

    def __init__(self, addon: VarsAddon, flow: Flow, name='', val=None, load_from=None, data_type: type[Data] = None):
        self.addon = addon
        self.flow = flow
        self._name = name
        self.data = None
        
        self.data_type = None
        d_type = data_type if data_type else Data
        self.set_data_type(d_type, val, load_from, True)

    @property
    def name(self):
        return self._name
    
    @property
    def subscriber(self):
        return self.addon.var_sub(self.flow, self.name)
    
    def get(self):
        """
        Returns the value of the variable
        """
        return self.data.payload
    
    def set(self, val, silent=False):
        """
        Sets the value of the variable
        """
        old_val = self.data.payload
        self.data.payload = val
        if not silent:
            self.addon.update_subscribers(self.flow, self._name)
            self.addon.var_value_changed.emit(self, old_val)

    def val_str(self):
        return str(self.data.payload)
    
    def set_data_type(self, data_type: type[Data], value=None, load_from=None, silent=False):
        """
        Sets the datatype for this variable
        
        The value will be defaulted if it doesn't conform to the payload type of the data type.
        """
        if not issubclass(data_type, Data):
            raise ValueError(f'{data_type} is not of type {Data}')
        
        if self.data_type == data_type:
            return False
        
        old_type = self.data_type
        self.data_type = data_type
        if self.data_type.is_valid_payload(value):
            self.data = self.data_type(value=value, load_from=load_from)
        else:
            self.data = self.data_type(load_from=load_from)
        
        if not silent:
            self.addon.update_subscribers(self.flow, self._name)
            self.addon.var_type_changed.emit(self, old_type)
        return True
    
    def update_subscribers(self):
        return self.addon.update_subscribers(self.flow, self._name)
    
    def serialize(self):
        return self.data.data()


class VarSubscriber:
    """Simple class to handle subscriptions for a variable"""
    
    def __init__(self, var: Variable):
        self.variable = var
        self.subscriptions: list[tuple[Node, Callable[[Variable], None]]] = []
        """The subscriptions are a callback that is a method on a node"""


class VarsAddon(AddOn):
    """
    This addon provides a simple variable system.

    It provides an API to create Variable objects which can wrap any Python object.

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

        # dict[Flow, dict[var_name, subscriber]]
        self.flow_variables: dict[Flow, dict[str, VarSubscriber]] = {}
        
        # nodes can be removed and re-added, so we need to keep track of the broken
        # subscriptions when nodes get removed, because they might get re-added
        # in which case we need to re-establish their subscriptions
        # dict[Node, dict[variable_name, callback_name]]
        self.removed_subscriptions: dict[Node, dict[str, str]] = {}

        # state data of variables that need to be recreated once their flow is
        # available, see :code:`on_flow_created()`
        self.flow_vars__pending: dict[int, dict] = {}

        # events
        self._var_created = Event[Variable]()
        self._var_deleted = Event[Variable, VarSubscriber]()
        self._var_renamed = Event[Variable, str]()
        self._var_value_changed = Event[Variable, Any]()
        self._var_type_changed = Event[Variable, Any]()
        self._var_data_loaded = Event[Variable]()
    
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
            return None
        
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
            # print_err(f'Variable {name} does not exist.')
            return False

        v_sub = self.flow_variables[flow][name]
        del self.flow_variables[flow][name]
        
        if not silent:
            self._var_deleted.emit(v_sub.variable, v_sub)
        return True

    def change_var_value(self, flow: Flow, name: str, value=None, silent=False):
        """Changes a variables value"""
        if not self.var_exists(flow, name):
            return False
        v = self.var(flow, name)
        try:
            v.set(value, silent)
            return True
        except:
            return False
    
    def change_var_type(self, flow: Flow, name: str, d_type: type[Data], value=None, data: dict = None, silent=False):
        """Changes a variables data type"""
        
        if not self.var_exists(flow, name):
            return False
        
        v = self.var(flow, name)
        try:
            result = v.set_data_type(d_type, value, data)
            return result
        except:
            return False
    
    def set_var_from_data(self, flow: Flow, name: str, data: dict, silent=False):
        """Loads a variable's value with serialized data"""
        
        if not self.var_exists(flow, name):
            return False
        
        v = self.var(flow, name)
        v.data.load(data)
        
        if not silent:
            self._var_data_loaded.emit(v)
        return True
    
    def var_exists(self, flow, name: str) -> bool:
        return flow in self.flow_variables and name in self.flow_variables[flow]

    def var(self, flow, name: str) -> Variable | None:
        """
        Returns the variable with the given name or None if it doesn't exist.
        """
        if not self.var_exists(flow, name):
            # print_err(f'Variable {name} does not exist.')
            return None

        return self.flow_variables[flow][name].variable

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
                name: v_sub.variable.serialize()
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

