"""Defines basic numeric data types"""

from ..base import _BuiltInData
from numbers import Number, Complex, Real, Rational, Integral
from fractions import Fraction
from ...utils import has_abstractmethods

class NumberData(_BuiltInData):
    """Base data class for numbers"""
    
    id_prefix = f'{_BuiltInData.id_prefix}.numbers'
    
    number_type = Number
    """Type from numbers module that the payload must conform to"""
    
    fallback_type = None
    """Fallback type to attempt instantiation if the value is not of number_type"""
    
    @classmethod
    def instantiable(cls):
        return (
            cls.fallback_type and 
            issubclass(cls.fallback_type, cls.number_type) and
            not has_abstractmethods(cls.fallback_type)
        )
        
    @classmethod
    def is_valid_payload(cls, payload):
        return isinstance(payload, cls.number_type)
    
    def __init__(self, value: number_type = None, load_from=None):
        
        # make sure that a default value will be provided
        if value:
            number = value
        elif self.fallback_type:
            number = self.fallback_type()
        else:
            number = 0
        super().__init__(number, load_from)
    
    @property
    def payload(self) -> number_type:
        return self._payload
    
    @payload.setter
    def payload(self, value: number_type):
        
        if self.is_valid_payload(value):
            self._payload = value
        elif self.fallback_type:
            # attempt to cast to the given type, might raise an error
            self._payload = self.fallback_type(value)
    
    def get_data(self):
        return self._payload

    def set_data(self, data: number_type):
        self.payload = data
         
class ComplexData(NumberData):
    number_type = Complex
    fallback_type = complex
    
    def __init__(self, value: Complex = complex(), load_from=None):
        super().__init__(value, load_from)
    
    @property
    def payload(self) -> Complex:
        return self._payload
    
    # Complex isn't JSON serializable by default
    
    def get_data(self):
        
        return {
            'real': self.payload.real,
            'imag': self.payload.imag,
        }
    
    def set_data(self, data: dict):
        self._payload = complex(real=data['real'], imag=data['imag'])
    
class RealData(ComplexData):
    number_type = Real
    fallback_type = float
    
    def __init__(self, value: Real = float(), load_from=None):
        super().__init__(value, load_from)
    
class RationalData(RealData):
    number_type = Rational
    fallback_type = Fraction
    
    def __init__(self, value: Rational = Fraction(), load_from=None):
        super().__init__(value, load_from)
    
    @property
    def payload(self) -> Rational:
        return self._payload
    
    # Rational isn't JSON serializable by default
    def get_data(self) -> dict:
        return {
            'num': self.payload.numerator,
            'denom': self.payload.denominator
        }
    
    def set_data(self, data: dict):
        self._payload = Fraction(numerator=data['num'], denominator=data['denom'])
    
class IntegerData(RationalData):
    number_type = Integral
    fallback_type = int 
    
    def __init__(self, value: Integral = int(), load_from=None):
        super().__init__(value, load_from)
