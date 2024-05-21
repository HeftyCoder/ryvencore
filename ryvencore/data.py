
from .base import Base

class Data(Base):
    """
    Base class for data wrappers.

    This class is passed internally between nodes as a wrapper to the value of any
    output, when such output is set. At this base implementation, it does not contain
    anything particularly useful. The Data passed through the nodes is essentially
    <RAM> data of a graph <program>. Hence, it isn't saved.
    
    However, each node class may override how this wrapper is created. By overriding
    the creation of the wrapper, one can pass any kind of metadata through the nodes
    and act on it accordingly for a general purpose.
    
    This is strictly for metadata purposes and for quality of life. It's easier to handle
    a custom object rather than a None object.
    """
    
    def __init__(self, value=None):
        super().__init__()
        self.payload = value


def check_valid_data(out_data_type: type[Data], inp_data_type: type[Data]) -> bool:
    """
    Returns true if input data can accept the output data, otherwise false
    
    None type is treated as the default Data type
    """
    
    if inp_data_type is None:
        inp_data_type = Data
    if out_data_type is None:
        out_data_type = Data
    
    return issubclass(out_data_type, inp_data_type)
 

