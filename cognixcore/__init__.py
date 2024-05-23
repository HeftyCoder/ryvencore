from .flow import *
from .config  import *
from .node import *
from .session import *
from .flow_player import *
from .info_msgs import InfoMsgs
from .rc import *
from .addons.base import AddOn
from .port import PortConfig, NodePort, NodeInput, NodeOutput
from .base import Event, NoArgsEvent
from .utils import serialize, deserialize

def set_complete_data_func(func):
    from .base import Base
    Base.complete_data_function = func
