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
