cognixcore.session
==================

.. py:module:: cognixcore.session


Classes
-------

.. autoapisummary::

   cognixcore.session.Session


Module Contents
---------------

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



