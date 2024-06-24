.. _tutorial:

Tutorial
========

Welcome to the :mod:`cognixcore` tutorial. Creating nodes and using them is
quite simple, as you will see.

.. include:: start example.rst

Now that we've covered the most basic aspects of the library, such as defining nodes, ports and the :code:`update_event`,
lets dive in the various functionalities and gotchas of :code:`cognixcore`. Most of the sections below are also detailed
in the concrete API documentation.

Initializations
---------------

This section briefly explains the initializations and de-initializations that may occur for a node.

__init__
^^^^^^^^

As is typical with every Python class, the :meth:`cognixcore.Node.__init__` constructor is called upon
instantiation of a :code:`Node`. This constructor is only called once.

place_event
^^^^^^^^^^^

The :meth:`cognixcore.Node.place_event` method is invoked whenever a :code:`Node` is placed inside a flow.
Essentially, this defines what should happen when someone "drops" or "creates" a node inside a :code:`Flow`.

.. warning::

   This event might be deprecated in the near future in favor of the :meth:`cognixcore.Node.init` method.

init
^^^^

The :meth:`cognixcore.Node.init` method is defined as an initialization point for a node, but not only at
construction time. Currently, it is invoked whenever a :code:`Flow` is evaluated through a :class:`cognixcore.GraphPlayer`,
right before the :code:`update_event`. More on the :code:`GraphPlayer` later.

stop
^^^^

The :meth:`cognixcore.Node.stop` method is invoked whenever a :code:`Flow` has finished evaluating through a :code:`GraphPlayer`. 

.. include:: executor_graph_player.rst

Frame Node
----------

The :class:`cognixcore.FrameNode` is a special type of node that in conjuction with a :code:`GraphPlayer`. A frame node is evaluated once per "frame". A frame in a :code:`GraphPlayer` denotes an execution step where the player needs to update all its frame nodes, through the approach
described previously. Lets see a basic example.

.. literalinclude:: examples/executors.py
   :language: python
   :linenos:
   :lines: 14-53

We begin by defining a :code:`FrameNode`. This node has only one output. We then implement its :meth:`cognixcore.FrameNode.frame_update` method. This method will be called one per frame, generating
a random number and outputting it through its port. We then create a session, register our node and
instantiate it, along with the :code:`AddNode` from our first example. We then connect the nodes and
play the flow. If we want the current flow of execution to not be stopped, we should pass :code:`True` to the :code:`on_other_thread` parameter, as shown.

Quality of Life
---------------

The above sections include the main functionalities of the :code:`cognixcore` library. In this section, we'll focus on  some QoL utilities that work out of the box with the CogniX Editor.

Loading/saving
^^^^^^^^^^^^^^

The nodes support state saving and loading through the :meth:`cognixcore.Node.load` and :meth:`cognixcore.Node.data` methods. Additionally, there are similar methods that can be found for the :code:`Session` and :code:`Flow`, however these should rarely be overriden.

Progress State
^^^^^^^^^^^^^^

The :class:`cognixcore.ProgressState` is a class that helps with setting the state of a node. In the context of simply scripting, this doesn't do much. However, it exists as an out of the box solution for any kind of GUI library that needs to define ongoing progress for a node. For example, the CogniX Editor automatically utilizes this to set a GUI that reacts to progress changes.

Loggers
^^^^^^^

Each node and flow have a logger through the :mode:`cognixcore.addons.logging` module, based on Python's `logging <https://docs.python.org/3/library/logging.html>`_ module. This can be accessed through their respective properties (:attr:`cognixcore.Node.logger` and :attr:`cognixcore.Flow.logger`).

Variables
^^^^^^^^^

Each node has access to a :class:`cognixcore.addons.variables.VarsAddon` for reading and setting the
state of dynamic variables. Refer to the documentation for further details.

Node Actions
^^^^^^^^^^^^

A node can define actions through the :class:`cognixcore.NodeAction` and the :meth:`cognixcore.Node.add_action` and :meth:`cognixcore.Node.add_generic_action` methods. In doing so, a context menu is populated for a node's GUI with the actions defined in the CogniX Editor. You would typically define the actions in the :code:`__init__` method of a node.

Dynamic ports

The static :attr:`cognixcore.Node.init_inputs` and :attr:`cognixcore.Node.init_outputs` initialization lists only work when a node is instantiated but not loaded through data. A node instance supports adding or removing ports dynamically at runtime. This is done through the following methods:

- :meth:`cognixcore.Node.create_input`
- :meth:`cognixcore.Node.delete_output`
- :meth:`cognixcore.Node.create_output`
- :meth:`cognixcore.Node.delete_output`


Node Configuration
^^^^^^^^^^^^^^^^^^

A node can have a configuration attached to it. This is done by either defining an internal to the node class explicitly named :code:`Config` or by setting the :attr:`cognixcore.Node.inner_config_type` type to a specific node config. The base class for a configuration is the :class:`cognixcore.NodeConfig` class.

Configuration by Traits
#######################

The standard implementation for a node configuration is the :class:`cognixcore.config.traits.NodeTraitsConfig` class. It utilizes the `Traits <https://docs.enthought.com/traits/traits_tutorial/introduction.html>`_ and `Traits UI <https://docs.enthought.com/traitsui/>` for out of the box data validation and 