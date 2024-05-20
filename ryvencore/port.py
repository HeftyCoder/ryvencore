from typing import TYPE_CHECKING

from .base import Base
from .utils import serialize, deserialize

from .rc import PortObjPos, ConnValidType
from .data import Data, check_valid_data
from dataclasses import dataclass
if TYPE_CHECKING:
    from .node import Node

@dataclass
class PortConfig:
    """
    The PortConfig class is a placeholder for the static init_input and
    init_outputs of custom Node classes.
    An instantiated Node's actual inputs and outputs will be of type NodePort (NodeInput, NodeOutput).
    """
    
    label: str = ''
    type_: str = 'data'
    allowed_data: Data = None
    default: Data | None = None

default_config = PortConfig()
"""An instance of a default port configuration"""
 
class NodePort(Base):
    """Base class for inputs and outputs of nodes"""

    def __init__(self, node, io_pos: PortObjPos, type_: str, label_str: str, allowed_data: type[Data] | None = None):
        Base.__init__(self)

        self.node: Node = node
        self.io_pos = io_pos
        self.type_ = type_
        self.label_str = label_str
        self.load_data = None
        self.allowed_data = allowed_data

    def load(self, data: dict):
        
        self.load_data = data
        self.type_ = data['port_type']
        self.label_str = data['label']
        # allowed data - backwards compatibility
        data_id = data.get('allowed_data')
        if data_id is not None:
            self.allowed_data = self.node.session.get_data_type(data_id)
        
    def data(self) -> dict:
        
        return {
            **super().data(),
            'port_type': self.type_,
            'label': self.label_str,
            'allowed_data': self.allowed_data.identifier if self.allowed_data is not None else None
        }


class NodeInput(NodePort):

    def __init__(self, node, type_: str, label_str: str = '', default: Data | None = None, allowed_data: type[Data] | None = None):
        super().__init__(node, PortObjPos.INPUT, type_, label_str, allowed_data)

        self.default = default

    def load(self, data: dict):
        super().load(data)

        self.default = Data(load_from=data['default']) if 'default' in data else None

    def data(self) -> dict:
        
        default = {'default': self.default.data()} if self.default is not None else {}

        return {
            **super().data(),
            **default,
        }

class NodeOutput(NodePort):
    def __init__(self, node, type_: str, label_str: str = '', allowed_data: type[Data] | None = None):
        super().__init__(node, PortObjPos.OUTPUT, type_, label_str, allowed_data)

        self.val: Data | None = None


def check_valid_conn(out: NodeOutput, inp: NodeInput) -> ConnValidType:
    """
    Checks if a connection is valid between two node ports.

    Returns:
        An enum representing the check result
    """
    
    if out.node == inp.node:
        return ConnValidType.SAME_NODE
    
    if out.io_pos == inp.io_pos:
        return ConnValidType.SAME_IO
    
    if out.io_pos != PortObjPos.OUTPUT:
        return ConnValidType.IO_MISSMATCH
    
    if out.type_ != inp.type_:
        return ConnValidType.DIFF_ALG_TYPE
    
    if not check_valid_data(out.allowed_data, inp.allowed_data):
        return ConnValidType.DATA_MISSMATCH
    
    return ConnValidType.VALID

def check_valid_conn_tuple(connection: tuple[NodeOutput, NodeInput]):
    out, inp = connection
    return check_valid_conn(out, inp)
    