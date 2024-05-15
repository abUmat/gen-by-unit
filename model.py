from dataclasses import dataclass
import const

@dataclass
class Plant:
    name: str
    area: const.Area

@dataclass
class Unit:
    id_: int
    plant: Plant
    type_: const.UnitType
    name: str
    power: float

@dataclass
class Measurements:
    plant_name: str
    unit_name: str
    measured_at: int
    measurements: int
    updated_at: int
