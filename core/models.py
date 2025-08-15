from dataclasses import dataclass
import math

@dataclass
class Bin:
    lower: float
    upper: float
    color_hex: str

    def contains(self, x: float, is_last: bool) -> bool:
        if math.isnan(x):
            return False
        if is_last:
            return self.lower <= x <= self.upper
        return self.lower <= x < self.upper




@dataclass
class ExactValue:
    value: float
    color_hex: str


