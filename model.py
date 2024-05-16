from dataclasses import dataclass
import const

@dataclass(frozen=True)
class Group:
    area: const.Area
    name: str

@dataclass(frozen=True)
class Plant:
    group: Group
    key: str
    name: str

@dataclass(frozen=True)
class Unit:
    key: str
    plant: Plant
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
