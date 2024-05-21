from dataclasses import dataclass
import const

@dataclass(frozen=True)
class Group:
    area: const.Area
    name: str

@dataclass(frozen=True)
class Unit:
    group: Group
    plant_key_name: str
    unit_key_name: str
    type_: const.UnitType
    name: str
    power: float

@dataclass(frozen=True)
class Measurements:
    plant_key_name: str
    unit_key_name: str
    measured_at: int
    measurements: int
    updated_at: int

class CSVParseError(Exception):
    """CSVファイルの解析中にエラーが発生した場合に使用するカスタム例外"""
    def __init__(self, message, line_number=None):
        self.message = message
        self.line_number = line_number
        super().__init__(self.message)

    def __str__(self):
        if self.line_number is not None:
            return f"{self.message} (line {self.line_number})"
        return self.message
