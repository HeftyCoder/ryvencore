"""
This module defines two core typs,  :code:`Data` and :code:`DataMetaInfo`
"""

from ..base import Base, Identifiable
from ..utils import serialize, deserialize, print_err

class Data(Base, Identifiable):
    """
    Base class for data wrappers.

    This class is passed internally between nodes as a wrapper to the value of any
    output, when such output is set. At this base implementation, it does not contain
    anything particularly useful.
    
    However, each node class may override how this wrapper is created. By overriding
    the creation of the wrapper, one can pass any kind of metadata through the nodes
    and act on it accordingly.
    """
    
    @classmethod
    def instantiable(cls):
        """
        *VIRTUAL
        
        This method returns whether the Data type can be instantiated.
        Some data types are meant to work only as identifiers for type
        checking (e.g. the classes in collections.abc)
        
        This can be useful for e.g. the Variables addon.
        
        The default for the base Data is True
        """
        return True
    
    @classmethod
    def is_valid_payload(cls, payload):
        """
        *VIRTUAL
        
        Returns if the given payload can be accepted.
        """
        return True
    
    def __init__(self, value=None, load_from=None):
        super().__init__()

        if load_from is not None:
            self.load(load_from)
        else:
            self.payload = value
                
    def __str__(self):
        return f'<{self.__class__.__name__}({self.payload}) object, GID: {self.global_id}>'

    @property
    def payload(self):
        return self._payload

    @payload.setter
    def payload(self, value):
        if not self.is_valid_payload(value):
            raise TypeError(f'Type of {type(value)} cannot be accepted by {self.__class__}')
        self._payload = value

    def get_data(self):
        """
        *VIRTUAL*

        Transform the data object to any serializable representation.
        The simple approach taken for the base Data class is to serialize into a :code:`pickle` serializable object.
        Preferably, a JSON compatible form should be returned.
        
        Override this to change how data is serialized.
        **Do not** use this function to access the payload, use :code:`payload` instead.
        """
        
        return serialize(self.payload)     

    def set_data(self, data):
        """
        *VIRTUAL*

        Deserialize the data object from the serialized data created in :code:`get_data()`.
        
        The naive implementation of the base Data class is to serialize into a :code:`pickle` serializable object.
        Preferably, data should be in a JSON compatible form.
        
        Override this to change how data is de-serialized.
        """
        self.payload = deserialize(data)

    def data(self) -> dict:
        return {
            **super().data(),
            'identifier': self.id(),
            'serialized': self.get_data()
        }

    def load(self, data: dict):
        super().load(data)

        if data['identifier'] != self.id() and data['identifier'] not in self.legacy_ids:
            # this should not happen when loading a Flow, because the flow checks
            print_err(f'WARNING: Data identifier {data["identifier"]} '
                      f'is not compatible with {self.id()}. Skipping.'
                      f'Did you forget to add it to legacy_identifiers?')
            return

        self.set_data(data['serialized'])

# build identifier for Data
Data._build_id()


class _BuiltInData(Data):
    """Identifier type for built-in data types"""
    
    id_prefix = 'built_in'
    
    @classmethod
    def instantiable(cls):
        return False

_BuiltInData._build_id()


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
 

