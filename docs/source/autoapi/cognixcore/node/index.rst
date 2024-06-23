cognixcore.node
===============

.. py:module:: cognixcore.node


Attributes
----------

.. autoapisummary::

   cognixcore.node.NodeType


Classes
-------

.. autoapisummary::

   cognixcore.node.Node
   cognixcore.node.FrameNode
   cognixcore.node.NodeAction
   cognixcore.node.GenericNodeAction


Functions
---------

.. autoapisummary::

   cognixcore.node.node_from_identifier
   cognixcore.node.get_node_classes
   cognixcore.node.get_versioned_nodes


Module Contents
---------------

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



.. py:data:: NodeType

   A :class:`TypeVar` for describing node types in a generic way

.. py:function:: node_from_identifier(id: str, nodes: list[Node])

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



.. py:function:: get_node_classes(modname: str, to_fill: list | None = None, base_type: type = None)

   Returns a list of node types defined in the current module that are not abstract


.. py:function:: get_versioned_nodes(modname: str, to_fill: list | None = None, base_type: type = None)

   Returns a list of node types defined in the current module that are not
   abstract and their version attribute is not None.


