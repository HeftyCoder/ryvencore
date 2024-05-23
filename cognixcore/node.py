from __future__ import annotations
import traceback

from .base import Base, Identifiable, IHaveIdentifiable, Event

from .port import default_config, PortConfig, NodeInput, NodeOutput
from .info_msgs import InfoMsgs
from .utils import serialize, deserialize
from .rc import ProgressState
from .addons.base import AddonType
from .addons.variables import VarsAddon
from .config import NodeConfig
from .utils import get_mod_classes

from abc import ABC, abstractmethod
from inspect import isclass
from beartype.door import is_bearable
from numbers import Real
from copy import copy

from typing import TYPE_CHECKING, Any, TypeVar
if TYPE_CHECKING:
    from .flow import Flow

class Node(Base, ABC):
    """
    Base class for all node blueprints. Such a blueprint is made by subclassing this class and registering that subclass
    in the session. Actual node objects are instances of it. The node's static properties are static attributes.
    Refer to python's static class attributes behavior.
    """

    id_name: str = None
    """The name of the node type. The class name will be used if left empty"""
    id_prefix: str = None,
    """The prefix of the node type."""
    legacy_ids: list[str] = []
    """Legacy ids. Must include the whole id: {prefix}.{name}"""
    
    title = ''
    """the node's title"""

    tags: list[str] = []
    """a list of tag strings, often useful for searching etc."""

    version: str = None
    """version tag, use it!"""

    init_inputs: list[PortConfig] = []
    """list of node input types determining the initial inputs"""

    init_outputs: list[PortConfig] = []
    """initial outputs list, see ``init_inputs``"""

    _inner_config_type: type[NodeConfig] | None = None
    """
    A nested class named Config can be defined to avoid setting the config_type.
    It will be used if the config_type is not defined.
    """
    
    _identifiable: Identifiable = None
    """The internal identifiable for characterizing this type"""
    
    @classmethod
    def identifiable(cls) -> Identifiable[type[Node]]:
        return cls._identifiable
    
    def __init_subclass__(cls):
        # config
        attr = getattr(cls, 'Config', None)
        if (attr and isclass(attr)):
            cls._inner_config_type = attr

        # identifiable
        id_name = cls.id_name if cls.id_name else cls.__name__
        cls._identifiable = Identifiable(
            id_name=id_name,
            id_prefix=cls.id_prefix,
            legacy_ids=cls.legacy_ids,
            info=cls
        )
            
    @classmethod
    def type_to_data(cls) -> dict[str, ]:
        return {
            'title': cls.title,
            'tags': cls.tags,
            'version': cls.version,
            'decs': cls.__doc__
        }
    #
    # INITIALIZATION
    #
    
    def __init__(self, flow: Flow, config: NodeConfig = None):
        Base.__init__(self)

        if config:
            self._config = config
        elif self._inner_config_type:
            self._config = self._inner_config_type(self)
            
        self.flow = flow
        self.session = flow.session
        
        self._inputs: list[NodeInput] = []
        self._outputs: list[NodeOutput] = []

        self.loaded = False
        self.load_data = None

        self.block_init_updates = False
        self.block_updates = False

        self._progress = None
        
        # events
        self.updated = Event[int]()
        self.updating = Event[int]()
        self.update_error = Event[Exception]()
        self.input_added = Event[Node, int, NodeInput]()
        self.input_removed = Event[Node, int, NodeInput]()
        self.output_added = Event[Node, int, NodeOutput]()
        self.output_removed = Event[Node, int, NodeOutput]()
        self.output_updated = Event[Node, int, NodeOutput, Any]()
        self.config_changed = Event[NodeConfig]()
        self.progress_updated = Event[ProgressState]()
    
    @property
    def config(self) -> NodeConfig | None:
        """Returns this node's configuration, if it exists"""
    
    @config.setter
    def config(self, value: NodeConfig):
        """Sets this node's configuration"""
        self.set_config(value, False)
    
    @property
    def vars_addon(self):
        return self.flow.session.addon(VarsAddon)
    
    def var_val(self, name: str):
        """Retrieves the value of a variable"""
        return self.vars_addon.var(self.flow, name).value
    
    def set_var_val(self, name: str, val):
        """Sets the value of a variable"""
        self.vars_addon.var(self.flow, name).value = val
        
    def set_config(self, value: NodeConfig, silent):
        if self._config == value:
            return
        self._config = value
        if not silent:
            self.config_changed.emit(self._config)
            
    def initialize(self):
        """
        Sets up the node ports.
        """
        self._setup_ports()

    def _setup_ports(self, inputs_data=None, outputs_data=None):

        if not inputs_data and not outputs_data:
            # generate initial ports

            for p_info in self.init_inputs:
                self.create_input(p_info)

            for p_info in self.init_outputs:
                self.create_output(p_info)

        else:
            # load from data
            # initial ports specifications are irrelevant then

            for inp in inputs_data:
                self.create_input(load_from=inp)

            for out in outputs_data:
                self.create_output(load_from=out)

    def after_placement(self):
        """Called from Flow when the nodes gets added."""

        self.place_event()

    def prepare_removal(self):
        """Called from Flow when the node gets removed."""

        self.remove_event()

    """
    
    ALGORITHM
    
    """

    # notice that all the below methods check whether the flow currently 'runs with an executor', which means
    # the flow is running in a special execution mode, in which case all the algorithm-related methods below are
    # handled by the according executor

    def update(self, inp=-1):  # , output_called=-1):
        """
        Activates the node, causing an ``update_event()`` if ``block_updates`` is not set.
        For performance-, simplicity-, and maintainability-reasons activation is now
        fully handed over to the operating ``FlowExecutor``, and not managed decentralized
        in Node, NodePort, and Connection anymore.
        """

        if self.block_updates:
            return

        # invoke update_event
        self.updating.emit(inp)
        self.flow.executor.update_node(self, inp)
    
    def update_port(self, port: NodeInput):
        """
        Activates the node if the given input port can be found.
        """
        
        self.update(self._inputs.index(port))

    def update_err(self, e):
        InfoMsgs.write_err('EXCEPTION in', self.title, '\n', traceback.format_exc())
        self.update_error.emit(e)

    def input(self, index: int):
        """
        Returns the data residing at the data input of given index.

        Do not call on exec inputs.
        """

        return self.flow.executor.input(self, index)

    def exec_output(self, index: int):
        """
        Executes an exec output, causing activation of all connections.

        Do not call on data outputs.
        """

        self.flow.executor.exec_output(self, index)

    def set_output(self, index: int, data):
        """
        Sets the value of a data output causing activation of all connections in data mode.
        """
        
        out = self._outputs[index]
        data_type = out.allowed_data if out.allowed_data else object
        
        assert is_bearable(data, data_type), f"Output value must be {data_type}, but it was {type(data)}"

        self.flow.executor.set_output(self, index, data)
        
        self.output_updated.emit(self, index, self._outputs[index], data)
    
    """
    
    ABSTRACTION
    
    """

    # these methods get implemented by node implementations

    @abstractmethod
    def update_event(self, inp=-1):
        """
        *ABSTRACT*

        Gets called when an input received a signal or some node requested data of an output in exec mode.
        Implement this in your node class, this is the place where the main processing of your node should happen.
        """

        pass

    def place_event(self):
        """
        *VIRTUAL*

        Called once the node object has been fully initialized and placed in the flow.
        When loading content, :code:`place_event()` is executed *before* connections are built.

        Notice that this method gets executed *every time* the node is added to the flow, which can happen
        more than once if the node was subsequently removed (e.g. due to undo/redo operations).
        """

        pass

    def remove_event(self):
        """
        *VIRTUAL*

        Called when the node is removed from the flow; useful for stopping threads and timers etc.
        """

        pass
    
    def reset(self):
        """
        VIRTUAL
        
        This is called when the node is reset. Typically happens when the GraphPlayer
        enters GraphState.Playing state. Implement any initialization here.
        """
        pass

    def start(self):
        """
        VIRTUAL
        
        Invoked when the graph player is started
        """
        pass
    
    def pause(self):
        """
        VIRTUAL
        
        Invoked when the graph player is paused
        """
    
    def stop(self):
        """
        VIRTUAL
        
        Invoked when the graph player is stopped
        """
        pass
    
    def destroy(self):
        """
        Invoked when the application exits
        
        Maybe not useful right now
        """
        pass

    def additional_data(self) -> dict:
        """
        *VIRTUAL*

        ``additional_data()``/``load_additional_data()`` is almost equivalent to
        ``get_state()``/``set_state()``,
        but it turned out to be useful for frontends to have their own dedicated version,
        so ``get_state()``/``set_state()`` stays clean for all specific node subclasses.
        """

        return {}

    def load_additional_data(self, data: dict):
        """
        *VIRTUAL*

        For loading the data returned by ``additional_data()``.
        """
        pass

    def get_state(self) -> dict:
        """
        *VIRTUAL*

        If your node is stateful, implement this method for serialization. It should return a JSON compatible
        dict that encodes your node's state. The dict will be passed to ``set_state()`` when the node is loaded.
        """
        return {}

    def set_state(self, data: dict, version):
        """
        *VIRTUAL*

        Opposite of ``get_state()``, reconstruct any custom internal state here.
        Notice, that add-ons might not yet be fully available here, but in
        ``place_event()`` the should be.
        """
        pass

    def rebuilt(self):
        """
        *VIRTUAL*

        If the node was created by loading components in the flow (see :code:`Flow.load_components()`),
        this method will be called after the node has been added to the graph and incident connections
        are established.
        """
        pass

    """
    
    API
    
    """

    #   PORTS

    def input_connected(self, inp: int):
        if len(self._inputs) <= inp:
            return False
        return self.flow.connected_output(self._inputs[inp]) is not None
    
    def output_connected(self, out: int):
        if len(self._outputs) <= out:
            return False
        return len(self.flow.connected_inputs(self._outputs[out])) > 0
    
    def create_input(self, port_info: PortConfig = None, load_from = None, insert: int = None):
        """
        Creates and adds a new input at the end or index ``insert`` if specified.
        """
        
        p_info = port_info if port_info else default_config

        inp = NodeInput(
            node=self, 
            type_=p_info.type_, 
            label_str=p_info.label, 
            default=p_info.default, 
            allowed_data=p_info.allowed_data
        )

        if load_from is not None:
            inp.load(load_from)

        if insert is not None:
            self._inputs.insert(insert, inp)
            index = insert
        else:
            self._inputs.append(inp)
            index = len(self._inputs) - 1

        self.input_added.emit(self, index, inp)

        return inp

    def rename_input(self, index: int, label: str):
        self._inputs[index].label_str = label

    def delete_input(self, index: int):
        """
        Disconnects and removes an input.
        """

        inp: NodeInput = self._inputs[index]

        # break all connections
        out = self.flow.connected_output(inp)
        if out is not None:
            self.flow.connect_nodes(out, inp)

        self._inputs.remove(inp)

        self.input_removed.emit(self, index, inp)

    def create_output(self, port_info: PortConfig = None, load_from=None, insert: int = None):
        """
        Creates and adds a new output at the end or index ``insert`` if specified.
        """

        p_info = port_info if port_info else default_config
        
        out = NodeOutput(
            node=self,
            type_=p_info.type_,
            label_str=p_info.label,
            allowed_data=p_info.allowed_data
        )

        if load_from is not None:
            out.load(load_from)

        if insert is not None:
            self._outputs.insert(insert, out)
            index = insert
        else:
            self._outputs.append(out)
            index = len(self._outputs) - 1

        self.output_added.emit(self, index, out)

        return out

    def rename_output(self, index: int, label: str):
        self._outputs[index].label_str = label

    def delete_output(self, index: int):
        """
        Disconnects and removes output.
        """

        out: NodeOutput = self._outputs[index]

        # break all connections
        for inp in self.flow.connected_inputs(out):
            self.flow.connect_nodes(out, inp)

        self._outputs.remove(out)

        self.output_removed.emit(self, index, out)

    #   VARIABLES

    def get_addon(self, addon: type[AddonType] | str) -> AddonType:
        """
        Returns an add-on registered in the session by name, or None if it wasn't found.
        """
        return self.session.addon(addon)
    
    #   PROGRESS
    
    @property
    def progress(self) -> ProgressState | None:
        """Copy of the current progress of execution in the node, or None if there's no active progress"""
        return copy(self._progress) if self._progress is not None else None
    
    @progress.setter
    def progress(self, progress_state: ProgressState | None):
        """Sets the current progress"""
        self._progress = progress_state
        self.progress_updated.emit(self._progress)
    
    def set_progress(self, progress_state: ProgressState | None, as_percentage: bool = False):
        """Sets the progress, allowing to turn it into a percentage"""
        if progress_state is not None and as_percentage:
            progress_state = progress_state.as_percentage()
        self._progress = progress_state
        self.progress_updated.emit(self._progress)
    
    def set_progress_value(self, value: Real, message: str = None, as_percentage: bool = False):
        """
        Sets the value of an existing progress
        
        Sets the message as well if it isn't None
        """
        self._progress.value = value
        if message:
            self._progress.message = message
        self.set_progress(self._progress, as_percentage)
            
    """
    
    UTILITY METHODS1
    
    """

    def is_active(self):
        for i in self._inputs:
            if i.type_ == 'exec':
                return True
        for o in self._outputs:
            if o.type_ == 'exec':
                return True
        return False

    def _inp_connected(self, index):
        return self.flow.connected_output(self._inputs[index]) is not None

    """
    
    SERIALIZATION
    
    """

    def load(self, data):
        """
        Initializes the node from the data dict returned by :code:`Node.data()`.
        Called by the flow, before the node is added to it.
        It does not crash on exception when loading user_data,
        as this is not uncommon when developing nodes.
        """
        super().load(data)

        self.load_data = data

        # setup ports
        # remove initial ports
        self._inputs = []
        self._outputs = []
        # load from data
        self._setup_ports(data['inputs'], data['outputs'])

        # config
        config_data = data.get('config')
        if self._config and config_data:
            self._config.load(config_data)
            
        # additional data
        if 'additional data' in data:
            add_data = data['additional data']
        else:   # backwards compatibility
            add_data = data
        self.load_additional_data(add_data)

        # set use state
        try:
            version = data.get('version')
            self.set_state(deserialize(data['state data']), version)
        except Exception as e:
            InfoMsgs.write_err(
                f'Exception while setting data in {self.title} node:'
                f'{e} (was this intended?)')

        self.loaded = True

    def data(self) -> dict:
        """
        Serializes the node's metadata, current configuration, and user state into
        a JSON-compatible dict, from which the node can be loaded later using
        :code:`Node.load()`.
        """

        d = {
            **super().data(),

            'identifier': self.id(),
            'version': self.version,    # this overrides the version field from Base

            'state data': serialize(self.get_state()),
            'additional data': self.additional_data(),

            'inputs': [i.data() for i in self._inputs],
            'outputs': [o.data() for o in self._outputs],
            
            'config': self._config.to_json() if self._config else None
        }

        # extend with data from addons
        for _, addon in self.session.addons.items():
            # addons can modify anything, there is no isolation enforcement
            addon.extend_node_data(self, d)

        return d
    
NodeType = TypeVar('NodeType', bound=Node)
 
def node_from_identifier(id: str, nodes: list[Node]):

    for nc in nodes:
        if nc.id() == id:
            return nc
    else:  # couldn't find a node with this identifier => search in legacy_ids
        for nc in nodes:
            if id in nc.legacy_ids:
                return nc
        else:
            raise Exception(
                f'could not find node class with id: \'{id}\'. '
                f'if you changed your node\'s class name, make sure to add the old '
                f'identifier to the legacy_ids list attribute to provide '
                f'backwards compatibility.'
            )


class FrameNode(Node):
    """A node which updates every frame of the Cognix Application."""
    
    def __init__(self, params):
        super().__init__(params)
        # Setting this will stop the node from updating
        self._is_finished = False
    
    @property
    def is_finished(self):
        return self._is_finished
    
    # implement so it doesn't throw exception
    def update_event(self, inp=-1):
        pass
    
    # Frame Updates
    def frame_update(self):
        """Wraps the frame_update_event with internal calls."""
        if self.frame_update_event():
            self.updating.emit(-1)
    
    @abstractmethod
    def frame_update_event(self) -> bool:
        """Called on every frame. Data might have been passed from other nodes"""
        pass
    
    def reset(self):
        self._is_finished = False
        return super().reset()

def get_node_classes(modname: str, to_fill: list | None = None, base_type: type = None):
    """Returns a list of node types defined in the current mode"""
    
    def filter_nodes(obj):
        return issubclass(obj, Node) and not obj.__abstractmethods__
        
    return get_mod_classes(modname, to_fill, filter_nodes)

