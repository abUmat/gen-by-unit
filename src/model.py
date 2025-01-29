from dataclasses import dataclass

@dataclass(frozen=True)
class Area:
    area_id: int
    name: str

@dataclass(frozen=True)
class Group:
    area_id: int
    group_id: int
    name: str

@dataclass(frozen=True)
class Unit:
    group_id: int
    unit_type_id: int
    plant_name: str
    unit_name: str
    name: str
    power: float
    long_term_shutdown: bool = False

@dataclass(frozen=True)
class UnitType:
    unit_type_id: int
    fuel_type_id: int
    name: str

@dataclass(frozen=True)
class FuelType:
    fuel_type_id: int
    colors_id: int
    name: str

@dataclass(frozen=True)
class Colors:
    colors_id: int
    name: str
    color_codes: list[str]

@dataclass
class UnitSummary:
    area: Area
    group: Group
    unit: Unit
    unit_type: UnitType
    fuel_type: FuelType
    colors: Colors
    generations: list[float]
    def __init__(self):
        self.area = None
        self.group = None
        self.unit = None
        self.unit_type = None
        self.fuel_type = None
        self.colors = None
        self.generations = []

@dataclass(frozen=True)
class Measurements:
    plant_name: str
    unit_name: str
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
