from dataclasses import dataclass
from .data.Data import Data


@dataclass
class NodePortType:
    """
    The NodePortType classes are only placeholders for the static init_input and
    init_outputs of custom Node classes.
    An instantiated Node's actual inputs and outputs will be of type NodePort (NodeInput, NodeOutput).
    """

    label: str = ''
    type_: str = 'data'
    allowed_data: Data = None
        

class NodeInputType(NodePortType):
    
    default: Data | None = None


class NodeOutputType(NodePortType):
    pass
