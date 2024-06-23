cognixcore
==========

.. py:module:: cognixcore

.. autoapi-nested-parse::

   Gathers all the most important classes and utilities under a unified namespace/package



Subpackages
-----------

.. toctree::
   :maxdepth: 1

   /autoapi/cognixcore/addons/index
   /autoapi/cognixcore/config/index
   /autoapi/cognixcore/networking/index


Submodules
----------

.. toctree::
   :maxdepth: 1

   /autoapi/cognixcore/base/index
   /autoapi/cognixcore/flow/index
   /autoapi/cognixcore/flow_executor/index
   /autoapi/cognixcore/flow_player/index
   /autoapi/cognixcore/info_msgs/index
   /autoapi/cognixcore/models/index
   /autoapi/cognixcore/node/index
   /autoapi/cognixcore/port/index
   /autoapi/cognixcore/rc/index
   /autoapi/cognixcore/serializers/index
   /autoapi/cognixcore/session/index
   /autoapi/cognixcore/utils/index


Attributes
----------

.. autoapisummary::

   cognixcore.EP
   cognixcore.InfoType
   cognixcore.NodeType
   cognixcore.AddonType


Classes
-------

.. autoapisummary::

   cognixcore.TypeMeta
   cognixcore.TypeSerializer
   cognixcore.BasicSerializer
   cognixcore.Event
   cognixcore.NoArgsEvent
   cognixcore.Base
   cognixcore.Identifiable
   cognixcore.IHaveIdentifiable
   cognixcore.IdentifiableGroups
   cognixcore.Flow
   cognixcore.Node
   cognixcore.FrameNode
   cognixcore.NodeAction
   cognixcore.GenericNodeAction
   cognixcore.NodeConfig
   cognixcore.NodeTraitsConfig
   cognixcore.Session
   cognixcore.FlowExecutor
   cognixcore.ManualFlow
   cognixcore.DataFlowNaive
   cognixcore.DataFlowOptimized
   cognixcore.ExecFlowNaive
   cognixcore.GraphState
   cognixcore.GraphTime
   cognixcore.GraphActionResponse
   cognixcore.GraphStateEvent
   cognixcore.GraphEvents
   cognixcore.GraphPlayer
   cognixcore.FlowPlayer
   cognixcore.InfoMsgs
   cognixcore.ConnectionInfo
   cognixcore.ConnValidType
   cognixcore.ProgressState
   cognixcore.AddOn
   cognixcore.PortConfig
   cognixcore.NodePort
   cognixcore.NodeInput
   cognixcore.NodeOutput


Functions
---------

.. autoapisummary::

   cognixcore.find_identifiable
   cognixcore.node_from_identifier
   cognixcore.serialize
   cognixcore.deserialize
   cognixcore.set_complete_data_func


Package Contents
----------------

.. py:class:: TypeMeta

   Metadata regarding a type. Useful if we want to build packages.


   .. py:attribute:: package
      :type:  str


   .. py:attribute:: type_id
      :type:  str


   .. py:method:: identifier()


.. py:class:: TypeSerializer

   Bases: :py:obj:`abc.ABC`


   Serializes/Deserializes an object into JSON compatible form.


   .. py:method:: serialize(obj)
      :abstractmethod:


      Serializes the object



   .. py:method:: deserialize(data)
      :abstractmethod:


      Deserializes the object from the data



   .. py:method:: default()
      :abstractmethod:


      Retrieves a default value for this type



.. py:class:: BasicSerializer(default_obj_type: type)

   Bases: :py:obj:`TypeSerializer`


   This default implementation simply returns the object as is. Useful
   for types that are already JSON compatible.


   .. py:method:: serialize(obj)

      Serializes the object



   .. py:method:: deserialize(data)

      Deserializes the object from the data



   .. py:method:: default()

      Retrieves a default value for this type



.. py:data:: EP

   A Parameter Spec for the :class:`Event` class. For Generic purposes.

.. py:class:: Event

   Bases: :py:obj:`Generic`\ [\ :py:obj:`EP`\ ]


   Implements a generalization of the observer pattern, with additional
   priority support. The lower the value, the earlier the callback
   is called. The default priority is 0.

   Negative priorities internally to ensure
   precedence of internal observers over all user-defined ones.


   .. py:method:: clear()


   .. py:method:: sub(callback: Callable[EP, None], nice=0, one_off=False)

      Registers a callback function. The callback must accept compatible arguments.
      The optional :code:`nice` parameter can be used to set the priority of the
      callback. The lower the priority, the earlier the callback is called.
      :code:`nice` can range from -5 to 10. The :code:`one_off` parameter indicates
      that the callback will be removed once it has been invoked.

      Negative priorities indicate internal functions. Users should not set these.



   .. py:method:: unsub(callback: Callable[EP, None])

      De-registers a callback function. The function must have been added previously.



   .. py:method:: emit(*args: EP, **kwargs: EP)

      Emits an event by calling all registered callback functions with parameters
      given by :code:`args`.



.. py:class:: NoArgsEvent

   Bases: :py:obj:`Event`\ [\ [\ ]\ ]


   Just wraps the Event[[]] for syntactic sugar. Not usefull in any other way.


.. py:class:: Base

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


   .. py:method:: obj_from_prev_id(prev_id: int)
      :classmethod:


      returns the object with the given previous id



   .. py:attribute:: complete_data_function


   .. py:method:: complete_data(data: dict)
      :staticmethod:


      Invokes the customizable :code:`complete_data_function` function
      on the dict returned by :code:`data`. This does not happen automatically
      on :code:`data()` because it is not always necessary (and might only be
      necessary once, not for each component individually).



   .. py:attribute:: version
      :type:  str
      :value: None



   .. py:method:: data() -> dict

      Convert the object to a JSON compatible dict.
      Reserved field names are 'GID' and 'version'.



   .. py:method:: load(data: dict)

      Recreate the object state from the data dict returned by :code:`data()`.

      Convention: don't call this method in the constructor, invoke it manually
      from outside, if other components can depend on it (and be notified of its
      creation).
      Reason: If another component `X` depends on this one (and
      gets notified when this one is created), `X` should be notified *before*
      it gets notified of creation or loading of subcomponents created during
      this load. (E.g. add-ons need to know the flow before nodes are loaded.)



.. py:data:: InfoType

   TypeVar for specifying an Identifiable's info, if it exists

.. py:class:: Identifiable(id_name: str, id_prefix: str | None = None, legacy_ids: list[str] = [], info: InfoType | None = None)

   Bases: :py:obj:`Generic`\ [\ :py:obj:`InfoType`\ ]


   A **container** that provides metadata useful for grouping.


   .. py:method:: __str__() -> str

      Return str(self).



   .. py:property:: id
      :type: str

      The id of this identifiable. A combination of the prefix (if used) and the name.


   .. py:property:: name
      :type: str

      The name of this identifiable.


   .. py:property:: prefix
      :type: str | None

      The prefix of this identifable


   .. py:property:: info
      The info of an identifiable


.. py:class:: IHaveIdentifiable

   If an object has identifiable information, it must conform to this contract


   .. py:property:: identifiable
      :type: Identifiable



.. py:function:: find_identifiable(id: str, to_search: collections.abc.Iterable[Identifiable[InfoType]])

   Searches for a :class:`Identifiable` with a given id.


.. py:class:: IdentifiableGroups(ids: collections.abc.Iterable[Identifiable[InfoType]] = [])

   Bases: :py:obj:`Generic`\ [\ :py:obj:`InfoType`\ ]


   Groups identifiables by their prefix and name. Identifiables with no prefix are groupped under 'global'

   Also holds structures for getting an identifiable by its name.


   .. py:attribute:: NO_PREFIX_ROOT
      :value: 'global'



   .. py:method:: __str__() -> str

      Return str(self).



   .. py:property:: id_set
      :type: set[Identifiable[InfoType]]

      A set containing all the Identifiables


   .. py:property:: id_map
      :type: collections.abc.Mapping[str, Identifiable[InfoType]]

      identifiable}

      :type: A map with layout {id


   .. py:property:: groups
      :type: collections.abc.Mapping[str, collections.abc.Mapping[str, Identifiable[InfoType]]]

      The identifiable groupped by their prefixes


   .. py:method:: rename(new_name: str, old_name: str, group: str)


   .. py:method:: add(id: Identifiable[InfoType]) -> bool

      Adds an identifiable to its group. Creates the group if it doesn't exist



   .. py:method:: remove(id: Identifiable[InfoType])

      Removes an identifiable from its group. Deletes the group if it's empty



   .. py:method:: group(group_id: str) -> None | collections.abc.Mapping[str, Identifiable[InfoType]]

      Retrieves a specific group. group_id must exist as a valid group.



   .. py:method:: group_infos(group_id: str) -> set[Self]


   .. py:method:: remove_group(group_id: str, emit_id_removed=False) -> bool

      Removes a group. group_id must exist as a valid group



   .. py:method:: groups_from_path(path: str)

      Retrieves all groups whose prefix contains the path

      Useful for "imitating" sub-groups



   .. py:method:: remove_groups_from_path(path: str)

      Removes all groups whos prefix contains the path

      Useful for "imitating" sub-groups



.. py:class:: Flow(session: cognixcore.session.Session, title: str)

   Bases: :py:obj:`cognixcore.base.Base`


   Manages all abstract flow components (nodes, edges, executors, etc.)
   and exposes methods for modification.


   .. py:property:: algorithm_mode
      :type: cognixcore.rc.FlowAlg

      The current algorithm mode of the flow as an enum.

      One-to-one with an executor type.


   .. py:property:: executor
      :type: cognixcore.flow_executor.FlowExecutor

      Returns the current executor of the Flow


   .. py:property:: logger
      :type: logging.Logger

      Returns the logger of the flow, based on the logging addon.


   .. py:property:: player
      :type: cognixcore.flow_player.GraphPlayer

      A player that can evaluate the flow as if it were a python program.


   .. py:method:: load(data: dict)

      Loading a flow from data as previously returned by ``Flow.data()``.



   .. py:method:: load_components(nodes_data, conns_data)

      Loading nodes and their connections from data as previously returned
      by :code:`Flow.data()`. This method will call :code:`Node.rebuilt()` after
      connections are established on all nodes.
      Returns the new nodes and connections.



   .. py:method:: create_node(node_class: type[cognixcore.node.NodeType], data=None, silent=False) -> cognixcore.node.NodeType

      Creates, adds and returns a new node object



   .. py:method:: add_node(node: cognixcore.node.Node, silent=False)

      Places the node object in the graph, Stores it, and causes the node's
      ``Node.place_event()`` to be executed. ``Flow.create_node()`` automatically
      adds the node already, so no need to call this manually.



   .. py:method:: remove_node(node: cognixcore.node.Node, silent=False)

      Removes a node from the flow without deleting it. Can be added again
      with ``Flow.add_node()``.



   .. py:method:: add_node_input(node: cognixcore.node.Node, inp: cognixcore.port.NodeInput, _call_flow_changed=True)

      updates internal data structures



   .. py:method:: add_node_output(node: cognixcore.node.Node, out: cognixcore.port.NodeOutput, _call_flow_changed=True)

      updates internal data structures.



   .. py:method:: remove_node_input(node: cognixcore.node.Node, inp: cognixcore.port.NodeInput, _call_flow_changed=True)

      updates internal data structures.



   .. py:method:: remove_node_output(node: cognixcore.node.Node, out: cognixcore.port.NodeOutput, _call_flow_changed=True)

      updates internal data structures.



   .. py:method:: connection_info(c: tuple[cognixcore.port.NodeOutput, cognixcore.port.NodeInput])

      Returns information about a connection without the ports



   .. py:method:: check_connection_validity(c: tuple[cognixcore.port.NodeOutput, cognixcore.port.NodeInput]) -> cognixcore.rc.ConnValidType

      Checks whether a considered connect action is legal.

      Does not check if the ports are connected or disconnected



   .. py:method:: can_ports_connect(c: tuple[cognixcore.port.NodeOutput, cognixcore.port.NodeInput]) -> cognixcore.rc.ConnValidType

      Same as :code:`Flow.check_connection_validity()`

      Also checks if nodes already connected or if input is connected to another output



   .. py:method:: can_ports_disconnect(c: tuple[cognixcore.port.NodeOutput, cognixcore.port.NodeInput]) -> cognixcore.rc.ConnValidType

      Same as :code:`Flow.check_connection_validity()`

      Also checks if nodes already disconnected



   .. py:method:: connect_from_info(conn: cognixcore.rc.ConnectionInfo, silent=False)


   .. py:method:: connect_nodes(out: cognixcore.node.Node, out_i: int, inp: cognixcore.node.Node, inp_i: int, silent=False)


   .. py:method:: connect_ports(out: cognixcore.port.NodeOutput | int, inp: cognixcore.port.NodeInput | int, silent=False) -> tuple[cognixcore.port.NodeOutput, cognixcore.port.NodeInput] | None

      Connects two node ports. Returns the connection if successful, None otherwise.



   .. py:method:: disconnect_from_info(conn: cognixcore.rc.ConnectionInfo, silent=False)


   .. py:method:: disconnect_nodes(out: cognixcore.node.Node, out_i: int, inp: cognixcore.node.Node, inp_i: int, silent=False)


   .. py:method:: disconnect_ports(out: cognixcore.port.NodeOutput, inp: cognixcore.port.NodeInput, silent=False)

      Disconnects two node ports.



   .. py:method:: add_connection(c: tuple[cognixcore.port.NodeOutput, cognixcore.port.NodeInput], silent=False)

      Adds an edge between two node ports.



   .. py:method:: remove_connection(c: tuple[cognixcore.port.NodeOutput, cognixcore.port.NodeInput], silent=False)

      Removes an edge.



   .. py:method:: connected_inputs(out: cognixcore.port.NodeOutput) -> list[cognixcore.port.NodeInput]

      Returns a list of all connected inputs to the given output port.



   .. py:method:: connected_output(inp: cognixcore.port.NodeInput) -> cognixcore.port.NodeOutput | None

      Returns the connected output port to the given input port, or
      :code:`None` if it is not connected.



   .. py:method:: set_executor(executor: cognixcore.flow_executor.FlowExecutor, silent=False)

      Sets the flow executor



   .. py:method:: set_algorithm_mode(mode: cognixcore.rc.FlowAlg | str, silent=False)

      Sets the algorithm mode of the flow, possible string values
      are 'manual', 'data', 'data opt', and 'exec'.

      Internally sets the corresponding executor.



   .. py:method:: data() -> dict

      Serializes the flow: returns a JSON compatible dict containing all
      data of the flow.



.. py:class:: Node(flow: cognixcore.flow.Flow, config: cognixcore.config.NodeConfig = None)

   Bases: :py:obj:`cognixcore.base.Base`, :py:obj:`abc.ABC`


   Base class for all node blueprints. Such a blueprint is made by subclassing this class and registering that subclass
   in the session. Actual node objects are instances of it. The node's static properties are static attributes.
   Refer to python's static class attributes behavior.


   .. py:attribute:: id_name
      :type:  str
      :value: None


      The name of the node type. The class name will be used if left empty


   .. py:attribute:: id_prefix
      :type:  str
      :value: (None,)


      The prefix of the node type.


   .. py:attribute:: legacy_ids
      :type:  list[str]
      :value: []


      {prefix}.{name}

      :type: Legacy ids. Must include the whole id


   .. py:attribute:: title
      :value: ''


      the node's title


   .. py:attribute:: tags
      :type:  list[str]
      :value: []


      a list of tag strings, often useful for searching etc.


   .. py:attribute:: version
      :type:  str
      :value: None


      version tag, use it! In the context of CogniX, all usable
      nodes must have a version, otherwise they're hidden. This
      applies only in Cognix, not in cognixcore.


   .. py:attribute:: init_inputs
      :type:  list[cognixcore.port.PortConfig]
      :value: []


      list of node input types determining the initial inputs


   .. py:attribute:: init_outputs
      :type:  list[cognixcore.port.PortConfig]
      :value: []


      initial outputs list, see ``init_inputs``


   .. py:method:: build_identifiable()
      :classmethod:


      Builds the internal identifiable that helps group nodes.



   .. py:method:: id()
      :classmethod:


      Shortcut for Node.identifiale.id()



   .. py:method:: identifiable() -> cognixcore.base.Identifiable[type[Node]]
      :classmethod:



   .. py:method:: __init_subclass__()
      :classmethod:



   .. py:method:: type_to_data() -> dict[str]
      :classmethod:



   .. py:property:: num_inputs
      The number of input ports.


   .. py:property:: num_outputs
      The number of output ports


   .. py:property:: actions
      :type: cognixcore.base.IdentifiableGroups[NodeAction]

      The actions of this node.


   .. py:property:: config
      :type: cognixcore.config.NodeConfig | None

      Returns this node's configuration, if it exists


   .. py:property:: player
      :type: cognixcore.flow_player.GraphPlayer

      A player that for the evaluation of the node.


   .. py:property:: logger
      :type: logging.Logger | None

      The logger associated with this node, if it exists.


   .. py:property:: vars_addon
      The variables addon associated with the flow that the node is currently in.


   .. py:method:: var_val(name: str)

      Retrieves the value of a variable



   .. py:method:: var_val_get(name: str) -> Any | None

      Retrieves the value of a variable. Returns None if it doesn't exist.



   .. py:method:: set_var_val(name: str, val)

      Sets the value of a variable



   .. py:method:: set_config(value: cognixcore.config.NodeConfig, silent)


   .. py:method:: add_action(name: str, action: NodeAction, group: str = None) -> NodeAction

      Adds an action and groups it under a group



   .. py:method:: add_generic_action(name: str, invoke: Callable[[], None], update: Callable[[], None] = None, group: str = None)


   .. py:method:: after_placement()

      Called from Flow when the nodes gets added.



   .. py:method:: prepare_removal()

      Called from Flow when the node gets removed.



   .. py:method:: update(inp=-1)

      Activates the node, causing an ``update_event()`` if ``block_updates`` is not set.
      For performance-, simplicity-, and maintainability-reasons activation is now
      fully handed over to the operating ``FlowExecutor``, and not managed decentralized
      in Node, NodePort, and Connection anymore.



   .. py:method:: update_port(port: cognixcore.port.NodeInput)

      Activates the node if the given input port can be found.



   .. py:method:: update_err(e)


   .. py:method:: input(index: int) -> Any

      Returns the data residing at the data input of given index.

      Do not call on exec inputs.



   .. py:method:: exec_output(index: int)

      Executes an exec output, causing activation of all connections.

      Do not call on data outputs.



   .. py:method:: set_output(index: int, data)

      Sets the value of a data output causing activation of all connections in data mode.



   .. py:method:: update_event(inp=-1)
      :abstractmethod:


      *ABSTRACT*

      Gets called when an input received a signal or some node requested data of an output in exec mode.
      Implement this in your node class, this is the place where the main processing of your node should happen.



   .. py:method:: place_event()

      *VIRTUAL*

      Called once the node object has been fully initialized and placed in the flow.
      When loading content, :code:`place_event()` is executed *before* connections are built.

      Notice that this method gets executed *every time* the node is added to the flow, which can happen
      more than once if the node was subsequently removed (e.g. due to undo/redo operations).



   .. py:method:: remove_event()

      *VIRTUAL*

      Called when the node is removed from the flow; useful for stopping threads and timers etc.



   .. py:method:: init()

      VIRTUAL

      Invoked when the a flow player has started. In a later revision,
      will be invoked when placed inside a flow in interactive mode.



   .. py:method:: pause()

      VIRTUAL

      Invoked when the graph player is paused



   .. py:method:: stop()

      VIRTUAL

      Invoked when the graph player is stopped



   .. py:method:: destroy()

      Invoked when the application exits

      Maybe not useful right now



   .. py:method:: additional_data() -> dict

      *VIRTUAL*

      ``additional_data()``/``load_additional_data()`` is almost equivalent to
      ``get_state()``/``set_state()``,
      but it turned out to be useful for frontends to have their own dedicated version,
      so ``get_state()``/``set_state()`` stays clean for all specific node subclasses.



   .. py:method:: load_additional_data(data: dict)

      *VIRTUAL*

      For loading the data returned by ``additional_data()``.



   .. py:method:: get_state() -> dict

      *VIRTUAL*

      If your node is stateful, implement this method for serialization. It should return a JSON compatible
      dict that encodes your node's state. The dict will be passed to ``set_state()`` when the node is loaded.



   .. py:method:: set_state(data: dict, version)

      *VIRTUAL*

      Opposite of ``get_state()``, reconstruct any custom internal state here.
      Notice, that add-ons might not yet be fully available here, but in
      ``place_event()`` the should be.



   .. py:method:: rebuilt()

      *VIRTUAL*

      If the node was created by loading components in the flow (see :code:`Flow.load_components()`),
      this method will be called after the node has been added to the graph and incident connections
      are established.



   .. py:method:: any_port_connected()


   .. py:method:: any_input_connected()


   .. py:method:: any_output_connected()


   .. py:method:: input_connected(inp: int | cognixcore.port.NodeInput)


   .. py:method:: output_connected(out: int | cognixcore.port.NodeOutput)


   .. py:method:: create_input(port_info: cognixcore.port.PortConfig = None, load_from=None, insert: int = None)

      Creates and adds a new input at the end or index ``insert`` if specified.



   .. py:method:: rename_input(index: int, label: str)


   .. py:method:: delete_input(index: int)

      Disconnects and removes an input.



   .. py:method:: create_output(port_info: cognixcore.port.PortConfig = None, load_from=None, insert: int = None)

      Creates and adds a new output at the end or index ``insert`` if specified.



   .. py:method:: rename_output(index: int, label: str)


   .. py:method:: delete_output(index: int)

      Disconnects and removes output.



   .. py:method:: get_addon(addon: type[cognixcore.addons.AddonType] | str) -> cognixcore.addons.AddonType

      Returns an add-on registered in the session by name, or None if it wasn't found.



   .. py:property:: progress
      :type: cognixcore.rc.ProgressState | None

      Copy of the current progress of execution in the node, or None if there's no active progress


   .. py:method:: set_progress(progress_state: cognixcore.rc.ProgressState | None, as_percentage: bool = False)

      Sets the progress, allowing to turn it into a percentage



   .. py:method:: set_progress_value(value: numbers.Real, message: str = None, as_percentage: bool = False)

      Sets the value of an existing progress

      Sets the message as well if it isn't None



   .. py:method:: set_progress_msg(message: str)


   .. py:method:: is_active()


   .. py:method:: load(data)

      Initializes the node from the data dict returned by :code:`Node.data()`.
      Called by the flow, before the node is added to it.
      It does not crash on exception when loading user_data,
      as this is not uncommon when developing nodes.



   .. py:method:: data() -> dict

      Serializes the node's metadata, current configuration, and user state into
      a JSON-compatible dict, from which the node can be loaded later using
      :code:`Node.load()`.



.. py:class:: FrameNode(params)

   Bases: :py:obj:`Node`


   A node which updates every frame, where frame is defined by a :class:`cognixcore.flow_player.GraphPlayer`.


   .. py:property:: is_finished


   .. py:method:: update_event(inp=-1)

      *ABSTRACT*

      Gets called when an input received a signal or some node requested data of an output in exec mode.
      Implement this in your node class, this is the place where the main processing of your node should happen.



   .. py:method:: frame_update()

      Wraps the frame_update_event with internal calls.



   .. py:method:: frame_update_event()
      :abstractmethod:


      Called on every frame. Data might have been passed from other nodes



.. py:class:: NodeAction(node: Node)

   Bases: :py:obj:`abc.ABC`


   A wrapper for defining an action that can happen for the node

   Useful for defining actions that can then be directly translated
   to a context menu.


   .. py:class:: Status

      Bases: :py:obj:`enum.IntEnum`


      Enum where members are also (and must be) ints


      .. py:attribute:: ENABLED
         :value: 0



      .. py:attribute:: DISABLED
         :value: 1



      .. py:attribute:: HIDDEN
         :value: 2




   .. py:property:: status


   .. py:method:: invoke()
      :abstractmethod:


      The action is invoked!



   .. py:method:: update()
      :abstractmethod:


      Update attributes of the action before it is invoked



.. py:class:: GenericNodeAction(node: Node, invoke: Callable[[], None], update: Callable[[], None] | None)

   Bases: :py:obj:`NodeAction`


   A generic node action that takes another method and wraps it


   .. py:method:: update()

      Update attributes of the action before it is invoked



   .. py:method:: invoke()

      The action is invoked!



.. py:data:: NodeType

   A :class:`TypeVar` for describing node types in a generic way

.. py:function:: node_from_identifier(id: str, nodes: list[Node])

.. py:class:: NodeConfig(node: cognixcore.node.Node = None)

   An interface representing a node's configuration


   .. py:property:: node
      :type: cognixcore.node.Node

      A property returning the node of this configuration


   .. py:method:: add_changed_event(e: Callable[[Any], None])

      Adds an event to be called when a parameter of the config changes. The
      event must be a function with a single parameter.



   .. py:method:: remove_changed_event(e: Callable[[Any], None])

      Removes any change event previously added.



   .. py:method:: allow_change_events()

      Allows the invocation of change events.



   .. py:method:: block_change_events()

      Blocks the invocation of change events.



   .. py:method:: to_json(indent=1) -> str
      :abstractmethod:


      Returns JSON representation of the object as a string



   .. py:method:: load(data: dict)
      :abstractmethod:


      Loads the configuration from a JSON compatible dict



   .. py:method:: data() -> dict
      :abstractmethod:


      Serializes this configuartion to a JSON compatible dict.



.. py:class:: NodeTraitsConfig(node: cognixcore.node.Node = None, *args, **kwargs)

   Bases: :py:obj:`cognixcore.config._abc.NodeConfig`, :py:obj:`traits.api.HasTraits`


   An implementation of a Node Configuration using the traits library


   .. py:method:: obs_exprs()
      :classmethod:



   .. py:method:: serializable_traits()
      :classmethod:


      Returns the serializable traits of this class



   .. py:method:: find_trait_exprs(exp_type: type[str | traits.observation.expression.ObserverExpression] = ObserverExpression)
      :classmethod:


      Finds all the observer expressions available for this node, for
      traits that are not an event, are visible and do not have the
      dont_save metadata atrribute set to True.



   .. py:method:: __init_subclass__(**kwargs)
      :classmethod:



   .. py:attribute:: traits_view
      :value: None



   .. py:method:: is_duplicate_notif(ev: traits.observation.events.TraitChangeEvent | traits.observation.events.ListChangeEvent | traits.observation.events.SetChangeEvent | traits.observation.events.DictChangeEvent) -> bool

      In some cases, a change notification can be invoked when the
      trait hasn't changed value.



   .. py:method:: allow_notifications()

      Allows the invocation of events when a trait changes



   .. py:method:: block_notifications()

      Blocks the invocation of events when a trait changes



   .. py:method:: load(data: dict)

      Loads the configuration from its serialized form.
      This is a recursive operation that includes nested
      configurations and configurations inside lists, dicts,
      sets and tuples.



   .. py:method:: data() -> dict

      Creates a JSON compatible dict with the data
      needed to reconstruct this traits config.

      This is a recursive operation.



   .. py:method:: to_json(indent=1) -> str

      Returns JSON representation of the object as a string



   .. py:method:: serializable_traits() -> dict[str, Any]

      Returns the traits that should be serialized.

      To avoid having a trait serialized, you can set
      its visible metadata attribute to False - :code:`visible=False`



   .. py:method:: inspected_traits() -> dict[str, traits.api.CTrait]

      Returns the traits that should be inspected in case
      of a GUI implementation.



.. py:class:: Session(gui: bool = False, load_optional_addons: bool = False)

   Bases: :py:obj:`cognixcore.base.Base`


   The Session is the top level interface to your project. It mainly manages flows, nodes, and add-ons and
   provides methods for serialization and deserialization of the project.


   .. py:attribute:: version


   .. py:property:: vars_addon


   .. py:property:: logg_addon


   .. py:property:: logger
      :type: logging.Logger



   .. py:property:: node_types


   .. py:property:: addons


   .. py:property:: flows


   .. py:property:: node_groups
      The identifiables of Node types groupped by their id prefix. If it doesn't exist, the key is global


   .. py:property:: rest_api


   .. py:method:: graph_player(title: str)

      A proxy to the graph players dictionary contained in the session



   .. py:method:: import_mod_addons(mod_name: str, package_name: str | None = None)

      Imports all addons found in a specific module using importlib import_module



   .. py:method:: addon(t: type[cognixcore.addons._base.AddonType] | str) -> cognixcore.addons._base.AddonType


   .. py:method:: register_addon(addon: cognixcore.addons._base.AddOn | type[cognixcore.addons._base.AddOn])

      Registers an addon



   .. py:method:: unregister_addon(addon: str | cognixcore.addons._base.AddOn)

      Unregisters an addon



   .. py:method:: register_node_types(node_types: collections.abc.Iterable[type[cognixcore.node.Node]])

      Registers a list of Nodes which then become available in the flows.
      Do not attempt to place nodes in flows that haven't been registered in the session before.



   .. py:method:: register_node_type(node_class: type[cognixcore.node.Node])

      Registers a single node.



   .. py:method:: unregister_node_type(node_class: type[cognixcore.node.Node])

      Unregisters a node which will then be removed from the available list.
      Existing instances won't be affected.



   .. py:method:: all_node_objects() -> list[cognixcore.node.Node]

      Returns a list of all node objects instantiated in any flow.



   .. py:method:: create_flow(title: str = None, data: dict = None, player_type: type[cognixcore.flow_player.GraphPlayer] = None, frames=30) -> cognixcore.flow.Flow | None

      Creates and returns a new flow.
      If data is provided the title parameter will be ignored.



   .. py:method:: rename_flow(flow: cognixcore.flow.Flow, title: str) -> bool

      Renames an existing flow and returns success boolean.



   .. py:method:: new_flow_title_valid(title: str) -> bool

      Checks whether a considered title for a new flow is valid (unique) or not.



   .. py:method:: delete_flow(flow: cognixcore.flow.Flow)

      Deletes an existing flow.



   .. py:method:: play_flow(flow_name: str, on_other_thread=False, callback: Callable[[cognixcore.flow_player.GraphActionResponse, str], None] = None)

      Plays the flow through the graph player



   .. py:method:: pause_flow(flow_name: str, callback: Callable[[cognixcore.flow_player.GraphActionResponse, str], None] = None)

      Pauses the graph player



   .. py:method:: resume_flow(flow_name: str, callback: Callable[[cognixcore.flow_player.GraphActionResponse, str], None] = None)


   .. py:method:: stop_flow(flow_name: str, callback: Callable[[cognixcore.flow_player.GraphActionResponse, str], None] = None)

      Stops the graph player



   .. py:method:: shutdown()


   .. py:method:: load(data: dict) -> list[cognixcore.flow.Flow]

      Loads a project and raises an exception if required nodes are missing
      (not registered).



   .. py:method:: serialize() -> dict

      Returns the project as JSON compatible dict to be saved and
      loaded again using load()



   .. py:method:: data() -> dict

      Serializes the project's abstract state into a JSON compatible
      dict. Pass to :code:`load()` in a new session to restore.
      Don't use this function for saving, use :code:`serialize()` in
      order to include the effects of :code:`Base.complete_data()`.



.. py:class:: FlowExecutor(flow: cognixcore.flow.Flow)

   Base class for special flow execution algorithms.


   .. py:property:: graph


   .. py:property:: graph_rev


   .. py:method:: update_node(node: cognixcore.flow.Node, inp: int)


   .. py:method:: input(node: cognixcore.flow.Node, index: int) -> Any


   .. py:method:: set_output(node: cognixcore.flow.Node, index: int, val)


   .. py:method:: exec_output(node: cognixcore.flow.Node, index: int)


   .. py:method:: conn_added(out: cognixcore.port.NodeOutput, inp: cognixcore.port.NodeInput, silent=False)


   .. py:method:: conn_removed(out: cognixcore.port.NodeOutput, inp: cognixcore.port.NodeInput, silent=False)


.. py:class:: ManualFlow(flow: cognixcore.flow.Flow)

   Bases: :py:obj:`FlowExecutor`


   An executor that doesn't propagate any data between nodes. Doesn't
   handle the exec_output.

   To be used for manual and/or external evaluation of the whole flow graph.


   .. py:method:: update_node(node: cognixcore.flow.Node, inp: int)


   .. py:method:: input(node: cognixcore.flow.Node, index: int)


   .. py:method:: set_output(node: cognixcore.flow.Node, index: int, data)


   .. py:method:: should_input_update(inp: cognixcore.port.NodeInput) -> bool


   .. py:method:: has_updated_outputs(node: cognixcore.flow.Node) -> bool


   .. py:method:: clear_updates()


.. py:class:: DataFlowNaive(flow: cognixcore.flow.Flow)

   Bases: :py:obj:`FlowExecutor`


   The naive implementation of data-flow execution. Naive meaning setting a node output
   leads to an immediate update in all successors consecutively. No runtime optimization
   if performed, and some types of graphs can run really slow here, especially if they
   include "diamonds".

   Assumptions for the graph:
   - no non-terminating feedback loops


   .. py:method:: update_node(node: cognixcore.flow.Node, inp: int)


   .. py:method:: input(node: cognixcore.flow.Node, index: int)


   .. py:method:: set_output(node: cognixcore.flow.Node, index: int, data)


   .. py:method:: exec_output(node: cognixcore.flow.Node, index: int)


   .. py:method:: conn_added(out: cognixcore.port.NodeOutput, inp: cognixcore.port.NodeInput, silent=False)


   .. py:method:: conn_removed(out, inp, silent=False)


.. py:class:: DataFlowOptimized(flow)

   Bases: :py:obj:`DataFlowNaive`


   *(see also documentation in Flow)*

   A special flow executor which implements some node functions to optimise flow execution.
   Whenever a new execution is invoked somewhere (some node or output is updated), it
   analyses the graph's connected component (of successors) where the execution was invoked
   and creates a few data structures to reverse engineer how many input
   updates every node possibly receives in this execution. A node's outputs are
   propagated once no input can still receive new data from a predecessor node.
   Therefore, while a node gets updated every time an input receives some data,
   every OUTPUT is only updated ONCE.
   This implies that every connection is activated at most once in an execution.
   This can result in asymptotic speedup in large data flows compared to normal data flow
   execution where any two executed branches which merge again in the future result in two
   complete executions of everything that comes after the merge, which quickly produces
   exponential performance issues.


   .. py:method:: update_node(node: cognixcore.flow.Node, inp=-1)


   .. py:method:: set_output(node: cognixcore.flow.Node, index: int, data)


   .. py:method:: exec_output(node, index)


   .. py:method:: start_execution(root_node: cognixcore.flow.Node = None, root_output: cognixcore.port.NodeOutput = None)


   .. py:method:: stop_execution()


   .. py:method:: generate_waiting_count(root_node=None, root_output=None)


   .. py:method:: invoke_node_update_event(node, inp)


   .. py:method:: decrease_wait(node)

      decreases the wait count of the node;
      if the count reaches zero, which means there is no other input waiting for data,
      the output values get propagated



   .. py:method:: propagate_outputs(node: cognixcore.flow.Node)

      propagates all outputs of node



   .. py:method:: propagate_output(out)

      pushes an output's value to successors if it has been changed in the execution



.. py:class:: ExecFlowNaive(flow)

   Bases: :py:obj:`FlowExecutor`


   ...


   .. py:method:: update_node(node: cognixcore.flow.Node, inp: int)


   .. py:method:: input(node: cognixcore.flow.Node, index: int)


   .. py:method:: set_output(node: cognixcore.flow.Node, index: int, data)


   .. py:method:: exec_output(node: cognixcore.flow.Node, index)


.. py:class:: GraphState(*args, **kwds)

   Bases: :py:obj:`enum.Enum`


   Enum that represents a graph player's state.


   .. py:attribute:: PLAYING


   .. py:attribute:: PAUSED


   .. py:attribute:: STOPPED


.. py:class:: GraphTime

   A class that wraps all time related information for a graph player.
   (fps, delta_time, time, etc)

   This class only makes sense if the graph has frame nodes.


   .. py:property:: frames
      The frame-rate this player will attempt to follow.


   .. py:property:: frame_count
      Frame count since time has started. Incremented at the start of each frame


   .. py:property:: time
      Time (seconds) since the player has started.


   .. py:property:: delta_time
      Interval (seconds) between the current frame and the last.


   .. py:method:: frame_dur()

      Frame duration the player will attempt to uphold.



   .. py:method:: avg_fps() -> float

      The average frames per second since the start of time.



   .. py:method:: current_fps() -> float

      The current frames per second



   .. py:method:: reset()


.. py:class:: GraphActionResponse

   Bases: :py:obj:`enum.IntEnum`


   An enum indicating a response to an action for a graph requested on the Session


   .. py:attribute:: NO_GRAPH

      No graph found to play


   .. py:attribute:: NOT_ALLOWED

      The action requested (play, pause, stop) is being invoked already


   .. py:attribute:: SUCCESS

      The action was succesful


.. py:class:: GraphStateEvent(old_state: GraphState, new_state: GraphState)

   Represents a change event


   .. py:method:: __str__()

      Return str(self).



.. py:class:: GraphEvents

   All the events that a graph player may have, associated with the
   :class:`GraphState` states.


   .. py:method:: sub_state_changed(func: Callable[[GraphStateEvent], None], nice=0, one_off=False)


   .. py:method:: unsub_state_changed(func: Callable[[GraphStateEvent], None])


   .. py:method:: sub_event(e_type: GraphState | str, func, nice=0, one_off=False)


   .. py:method:: unsub_event(e_type: GraphState | str, func)


   .. py:method:: reset()

      Resets the all the events.



.. py:class:: GraphPlayer(frames: int = 5)

   Bases: :py:obj:`abc.ABC`


   A graph player is a class that handles the processing and evaluating
   of a flow of nodes like it would a python program.


   .. py:property:: flow
      :type: cognixcore.flow.Flow

      The flow for this player.


   .. py:property:: graph_time
      :type: GraphTime

      Time information for this player


   .. py:property:: delta_time
      :type: float

      Convenience method for returning delta-time


   .. py:property:: graph_events
      :type: GraphEvents

      Events for this graph


   .. py:method:: set_frames(value: int)


   .. py:property:: state
      The state of the player.


   .. py:method:: play()
      :abstractmethod:


      Plays or evaluates the graph.



   .. py:method:: pause()
      :abstractmethod:


      Pauses the graph if it had any real-time elements (FrameNodes).



   .. py:method:: resume()
      :abstractmethod:


      Resumes the graph if it was paused.



   .. py:method:: stop()
      :abstractmethod:


      Stops the graph.



.. py:class:: FlowPlayer(frames: int = 30)

   Bases: :py:obj:`GraphPlayer`


   The default implementation of a Graph Player in CogniX


   .. py:property:: flow
      The flow for this player.


   .. py:method:: play()

      Plays or evaluates the graph.



   .. py:method:: pause()

      Pauses the graph if it had any real-time elements (FrameNodes).



   .. py:method:: resume()

      Resumes the graph if it was paused.



   .. py:method:: stop()

      Stops the graph.



.. py:class:: InfoMsgs

   A few handy static methods for writing different kinds of messages to the output console only if info msgs are
   enabled.


   .. py:attribute:: enabled
      :value: False



   .. py:attribute:: enabled_errors
      :value: False



   .. py:attribute:: traceback_enabled
      :value: False



   .. py:method:: enable(traceback=False)
      :staticmethod:



   .. py:method:: enable_errors(traceback=True)
      :staticmethod:



   .. py:method:: disable()
      :staticmethod:



   .. py:method:: write(*args)
      :staticmethod:



   .. py:method:: write_err(*args)
      :staticmethod:



.. py:class:: ConnectionInfo

   Characterizes a connection without the ports


   .. py:attribute:: node_out
      :type:  cognixcore.node.Node
      :value: None



   .. py:attribute:: out_i
      :type:  int
      :value: 0



   .. py:attribute:: node_inp
      :type:  cognixcore.node.Node
      :value: None



   .. py:attribute:: inp__i
      :type:  int
      :value: 0



   .. py:property:: out_port


   .. py:property:: inp_port


.. py:class:: ConnValidType

   Bases: :py:obj:`enum.IntEnum`


   Result from a connection validity test between two node ports


   .. py:attribute:: VALID

      Valid Connection


   .. py:attribute:: SAME_NODE

      Invalid Connection due to same node


   .. py:attribute:: SAME_IO

      Invalid Connection due to both ports being input or output


   .. py:attribute:: IO_MISSMATCH

      Invalid Connection due to output being an input and vice-versa


   .. py:attribute:: DIFF_ALG_TYPE

      Invalid Connection due to different algorithm types (data or exec)


   .. py:attribute:: DATA_MISSMATCH

      Invalid Connection due to input / output Data type checking


   .. py:attribute:: INPUT_TAKEN

      Invalid Connection due to input being connected to another output


   .. py:attribute:: ALREADY_CONNECTED

      Invalid Connect check

      Optional Check - A connect action was attempted but nodes were already connected!


   .. py:attribute:: ALREADY_DISCONNECTED

      Invalid Disconnect check

      Optional Check - A disconnect action was attemped on disconnected ports!


   .. py:method:: get_error_message(conn_valid_type: ConnValidType, out: cognixcore.port.NodeOutput, inp: cognixcore.port.NodeInput) -> str
      :classmethod:


      An error message for the various ConnValidType types



.. py:class:: ProgressState(max_value: numbers.Real = 1, value: numbers.Real = 0, message: str = '')

   Represents a progress state / bar.

   A negative value indicates indefinite progress


   .. py:method:: INDEFINITE_PROGRESS()
      :classmethod:



   .. py:method:: __str__() -> str

      Return str(self).



   .. py:property:: max_value
      :type: numbers.Real

      Max value of the progress.


   .. py:property:: value
      :type: numbers.Real

      Current value of the progress. A negative value indicates indefinite progress


   .. py:method:: is_indefinite() -> bool

      Returns true if there is indefinite progress



   .. py:method:: percentage() -> numbers.Real


   .. py:method:: as_percentage() -> ProgressState

      Returns a new progress state so that max_value = 1



.. py:data:: AddonType

   A :code:`TypeVar` referencing the :class:`AddOn` type for generic use

.. py:class:: AddOn

   Bases: :py:obj:`cognixcore.base.Base`


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


   .. py:attribute:: version
      :value: ''



   .. py:method:: addon_name()
      :classmethod:



   .. py:method:: register(session: cognixcore.session.Session)

      Called when the add-on is registered to a session.



   .. py:method:: unregister()

      Called when the add-on is unregistered from a session.



   .. py:method:: connect_flow_events(flow: cognixcore.flow.Flow)

      Connects flow events to the add-on. There are events for
      when a node is created, added, removed or created from data.



   .. py:method:: disconnect_flow_events(flow: cognixcore.flow.Flow)

      Disconnects flow events to the add-on



   .. py:method:: on_loaded()

      *VIRTUAL*

      Called when an addon is loaded from data. This is invoked
      after the flows and nodes have been loaded.



   .. py:method:: on_flow_created(flow: cognixcore.flow.Flow)

      *VIRTUAL*

      Called when a flow is created.



   .. py:method:: on_flow_destroyed(flow: cognixcore.flow.Flow)

      *VIRTUAL*

      Called when a flow is destroyed.



   .. py:method:: on_flow_renamed(flow: cognixcore.flow.Flow)

      *VIRTUAL*

      Called when a flow is renamed



   .. py:method:: on_node_created(node: cognixcore.node.Node)

      *VIRTUAL*

      Called when a node is created and fully initialized
      (:code:`Node.load()` has already been called, if necessary),
      but not yet added to the flow. Therefore, this is a good place
      to initialize the node with add-on-specific data.

      This happens only once per node, whereas it can be added and
      removed multiple times, see :code:`AddOn.on_node_added()` and
      :code:`AddOn.on_node_removed()`.



   .. py:method:: on_nodes_loaded(nodes: collections.abc.Sequence[cognixcore.node.Node])

      *VIRTUAL*

      Called when a node is loaded and fully initialized
      from data. The node has been added to the flow, however
      the :code:`Node.place_event()` has not been called yet.



   .. py:method:: on_node_added(node: cognixcore.node.Node)

      *VIRTUAL*

      Called when a node is added to a flow.



   .. py:method:: on_node_removed(node: cognixcore.node.Node)

      *VIRTUAL*

      Called when a node is removed from a flow.



   .. py:method:: extend_node_data(node: cognixcore.node.Node, data: dict)

      *VIRTUAL*

      Invoked whenever any node is serialized. This method can be
      used to extend the node's data dict with additional
      add-on.related data.



   .. py:method:: get_state() -> dict

      *VIRTUAL*

      Return the state of the add-on as JSON-compatible a dict.
      This dict will be extended by :code:`AddOn.complete_data()`.



   .. py:method:: set_state(state: dict, version: str)

      *VIRTUAL*

      Set the state of the add-on from the dict generated in
      :code:`AddOn.get_state()`. Addons are loaded after the
      Flows.



   .. py:method:: data() -> dict

      Supplements the data dict with additional data.



   .. py:method:: load(data: dict)

      Loads the data dict generated in :code:`AddOn.data()`.



.. py:class:: PortConfig

   The PortConfig class is a configuration class for creating ports. It's mainly used for the static init_input
   and init_outputs of custom Node classes, but can also be used for dynamically creating ports for Nodes.
   An instantiated Node's actual inputs and outputs will be of type :class:`NodePort` (:class:`NodeInput`, :class:`NodeOutput`).


   .. py:attribute:: label
      :type:  str
      :value: ''



   .. py:attribute:: type_
      :type:  str
      :value: 'data'



   .. py:attribute:: allowed_data
      :type:  Any
      :value: None



   .. py:attribute:: default
      :type:  Any
      :value: None



.. py:class:: NodePort(node, io_pos: cognixcore.rc.PortObjPos, type_: str, label_str: str, allowed_data: type | None = None)

   Bases: :py:obj:`cognixcore.base.Base`


   Base class for inputs and outputs of nodes


   .. py:method:: load(data: dict)

      Recreate the object state from the data dict returned by :code:`data()`.

      Convention: don't call this method in the constructor, invoke it manually
      from outside, if other components can depend on it (and be notified of its
      creation).
      Reason: If another component `X` depends on this one (and
      gets notified when this one is created), `X` should be notified *before*
      it gets notified of creation or loading of subcomponents created during
      this load. (E.g. add-ons need to know the flow before nodes are loaded.)



   .. py:method:: data() -> dict

      Convert the object to a JSON compatible dict.
      Reserved field names are 'GID' and 'version'.



.. py:class:: NodeInput(node, type_: str, label_str: str = '', default=None, allowed_data: type | None = None)

   Bases: :py:obj:`NodePort`


   A port that is an input


   .. py:method:: load(data: dict)

      Recreate the object state from the data dict returned by :code:`data()`.

      Convention: don't call this method in the constructor, invoke it manually
      from outside, if other components can depend on it (and be notified of its
      creation).
      Reason: If another component `X` depends on this one (and
      gets notified when this one is created), `X` should be notified *before*
      it gets notified of creation or loading of subcomponents created during
      this load. (E.g. add-ons need to know the flow before nodes are loaded.)



   .. py:method:: data() -> dict

      Convert the object to a JSON compatible dict.
      Reserved field names are 'GID' and 'version'.



.. py:class:: NodeOutput(node, type_: str, label_str: str = '', allowed_data: type | None = None)

   Bases: :py:obj:`NodePort`


   A port that is an output


.. py:function:: serialize(data) -> str

.. py:function:: deserialize(data)

.. py:function:: set_complete_data_func(func)

