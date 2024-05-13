from .data import Data 
from .data.built_in import get_built_in_data_types 
from .base import Base, Event, IdentifiableGroups
from .flow import Flow
from .info_msgs import InfoMsgs
from .utils import pkg_version, pkg_path, print_err, get_mod_classes
from .node import Node
from .addons.base import AddOn

from importlib import import_module
from types import MappingProxyType
from collections.abc import Set, Mapping, Iterable


class Session(Base):
    """
    The Session is the top level interface to your project. It mainly manages flows, nodes, and add-ons and
    provides methods for serialization and deserialization of the project.
    """

    version = pkg_version()
    
    _flow_base_type = Flow
    """
    Forces the Session to accept a specific type of base Flow.
    """
    
    def __init__(
            self,
            gui: bool = False,
            load_addons: bool = False,
    ):
        Base.__init__(self)

        # events
        self.flow_created = Event[Flow]()
        self.flow_renamed = Event[Flow, str]()
        self.flow_deleted = Event[Flow]()
        
        # ATTRIBUTES
        self._addons: dict[str, AddOn] = {}
        self._addons_proxy = MappingProxyType(self._addons)
        
        self._flows: dict[str, Flow] = {}
        self._flows_proxy = MappingProxyType(self._flows)
        
        self.invis_node_types: set[type[Node]] = set()
        
        self.gui: bool = gui
        self.init_data = None

        # groups
        self._node_type_groups = IdentifiableGroups[Node]()
        self._data_type_groups = IdentifiableGroups[Data]()
        self._inst_data_groups = IdentifiableGroups[Data]()
        
        # Register Built-In Data Types
        self.register_data_types(get_built_in_data_types())
        
        # Load built-in addons
        if load_addons:
            from .addons.builtin import built_in_addons
            for addon_type in built_in_addons:
                self.register_addon(addon_type)
        
    @property
    def node_types(self):
        return self._node_type_groups.id_set
    
    @property
    def addons(self):
        return self._addons_proxy
    
    @property
    def flows(self):
        return self._flows_proxy
    
    @property
    def data_types(self):
        return self._data_type_groups.id_map
    
    @property
    def inst_data_types(self):
        """Returns a readonly dictionay (proxy) for which data types can be instantiated"""
        return self._inst_data_groups.id_map
    
    @property
    def node_groups(self):
        """Node types groupped by their id prefix. If it doesn't exist, the key is global"""
        return self._node_type_groups
    
    @property
    def data_groups(self):
        """Data types groupped by their id prefix. If it doesn't exist, the key is global"""
        return self._data_type_groups

    @property
    def inst_data_groups(self):
        """Data types that can be instantiated groupped by their id prefix."""
        return self._inst_data_groups
    
    # TODO: Think of an importing solution for external addons
    # def load_addons(self, location: str | None = None):
    #     """Loads all addons found in every module inside the given directory"""
        
    #     pkg_loc = location if location else pkg_path('addons/')
    #     addons = filter(lambda p: not p.endswith('__init__.py'), glob.glob(pkg_loc + '/*.py'))
        
    #     for path in addons:
    #         mod_name = basename(path).removesuffix('.py')
    #         self.import_mod_addons(mod_name)

    def import_mod_addons(self, mod_name: str, package_name: str | None = None):
        """Imports all addons found in a specific module using importlib import_module"""
        
        try:
            addon_mod = import_module(mod_name, package_name)
        except Exception as e:
            InfoMsgs.write(str(e))
            return
        
        def addon_class_filter(obj):
            return issubclass(obj, AddOn) and obj.__class__ != AddOn
        
        mod_addons: list[type[AddOn]] = get_mod_classes(addon_mod, filter=addon_class_filter)
        for addon_type in mod_addons:
            addon_name = addon_type.addon_name()
            if addon_name in self._addons:
                InfoMsgs.write(f"Addon with name {addon_name} has already been registerd!")
                continue
            
            addon = addon_type()
            self.register_addon(addon)
        
    def register_addon(self, addon: AddOn | type[AddOn]):
        """Registers an addon"""
        
        addon_name = addon.addon_name()
        if addon.addon_name() in self._addons:
            return
        if not isinstance(addon, AddOn):
            addon = addon()
        
        addon.register(self)
        self._addons[addon_name] = addon
        self.flow_created.sub(addon.on_flow_created, nice=-5)
        self.flow_deleted.sub(addon.on_flow_destroyed, nice=-5)
                
        for f in self._flows.values():
            addon.connect_flow_events(f)
    
    def unregister_addon(self, addon: str | AddOn):
        """Unregisters an addon"""
        addon_name = addon if isinstance(addon, str) else addon.addon_name()
        if addon_name in self._addons:
            to_remove = self._addons[addon_name]
            self.flow_created.unsub(to_remove.on_flow_created)
            self.flow_deleted.unsub(to_remove.on_flow_destroyed)
            
            for f in self._flows.values():
                to_remove.disconnect_flow_events(f)
                
            del self._addons[addon_name]

    def register_node_types(self, node_types: Iterable[type[Node]]):
        """
        Registers a list of Nodes which then become available in the flows.
        Do not attempt to place nodes in flows that haven't been registered in the session before.
        """

        for n in node_types:
            self.register_node_type(n)


    def register_node_type(self, node_class: type[Node]):
        """
        Registers a single node.
        """

        node_class._build_id()
        self._node_type_groups.add(node_class)


    def unregister_node(self, node_class: type[Node]):
        """
        Unregisters a node which will then be removed from the available list.
        Existing instances won't be affected.
        """

        self._node_type_groups.remove(node_class)
     
                
    def all_node_objects(self) -> list[Node]:
        """
        Returns a list of all node objects instantiated in any flow.
        """

        return [n for f in self._flows.values() for n in f.nodes]


    def register_data_type(self, data_type_class: type[Data]):
        """
        Registers a new :code:`Data` subclass which will then be available
        in the flows.
        """

        data_type_class._build_id()
        id = data_type_class.id()
        
        add_result = self._data_type_groups.add(data_type_class)
        if id == 'Data' or not add_result:
            print_err(
                f'Data type identifier "{id}" is already registered. '
                f'skipping. You can use the "id" function of '
                f'your Data subclass.')
            return

        if data_type_class.instantiable():
            self._inst_data_groups.add(data_type_class)
        
        # group data types
        

    def register_data_types(self, data_type_classes: Iterable[type[Data]]):
        """
        Registers a list of :code:`Data` subclasses which will then be available
        in the flows.
        """

        for d in data_type_classes:
            self.register_data_type(d)

    
    def register_data_types_by_base(self, base_type: type[Data]):
        """
        Registers :code:`Data` subclasses that belong to a base class.
        """
        
        self.register_data_type(base_type)
        for data_type in base_type.__subclasses__():
            self.register_data_type(data_type)
            
    
    def get_data_type(self, id: str) -> type[Data] | None:
        """
        Retrieves a data type with a specific id, if it exists
        """
        
        return self.data_types.get(id)
        
        
    def create_flow(self, title: str = None, data: dict = None) -> Flow | None:
        """
        Creates and returns a new flow.
        If data is provided the title parameter will be ignored.
        """

        flow = self._flow_base_type(session=self, title=title)
        if data:
            flow.load(data)
        
        # Titles should be unique
        if not self.new_flow_title_valid(flow.title):
            return None
        
        self._flows[flow.title] = flow
        self.flow_created.emit(flow)

        return flow


    def rename_flow(self, flow: Flow, title: str) -> bool:
        """
        Renames an existing flow and returns success boolean.
        """

        success = False

        if self.new_flow_title_valid(title):
            del self._flows[flow.title]
            flow.title = title
            self._flows[title] = flow
            success = True
            self.flow_renamed.emit(flow, title)

        return success


    def new_flow_title_valid(self, title: str) -> bool:
        """
        Checks whether a considered title for a new flow is valid (unique) or not.
        """

        return len(title) != 0 and title not in self._flows


    def delete_flow(self, flow: Flow):
        """
        Deletes an existing flow.
        """
        
        if flow.title not in self._flows or flow != self._flows[flow.title]:
            return False
        
        del self._flows[flow.title]
        self.flow_deleted.emit(flow)
        return True


    def _info_messenger(self):
        """
        Returns a reference to InfoMsgs to print info data.
        """

        return InfoMsgs


    def load(self, data: dict) -> list[Flow]:
        """
        Loads a project and raises an exception if required nodes are missing
        (not registered).
        """

        super().load(data)

        self.init_data = data

        # load addons
        for name, addon_data in data['addons'].items():
            if name in self._addons:
                self._addons[name].load(addon_data)
            else:
                print(f'found missing addon: {name}; attempting to load anyway')

        # load flows
        new_flows = []

        #   backward compatibility
        if 'scripts' in data:
            flows_data = {
                title: script_data['flow']
                for title, script_data in data['scripts'].items()
            }
        elif isinstance(data['flows'], list):
            flows_data = {
                f'Flow {i}': flow_data
                for i, flow_data in enumerate(data['flows'])
            }
        else:
            flows_data = data['flows']

        for title, data in flows_data.items():
            new_flows.append(self.create_flow(title=title, data=data))

        return new_flows

    def serialize(self) -> dict:
        """
        Returns the project as JSON compatible dict to be saved and
        loaded again using load()
        """

        return self.complete_data(self.data())


    def data(self) -> dict:
        """
        Serializes the project's abstract state into a JSON compatible
        dict. Pass to :code:`load()` in a new session to restore.
        Don't use this function for saving, use :code:`serialize()` in
        order to include the effects of :code:`Base.complete_data()`.
        """

        return {
            **super().data(),
            'flows': {
                f.title: f.data()
                for f in self._flows.values()
            },
            'addons': {
                name: addon.data() for name, addon in self._addons.items()
            }
        }
        
