from dataclasses import dataclass
import const

@dataclass
class Group:
    area: const.Area
    name: str

@dataclass
class Plant:
    group: Group
    key: str
    name: str

@dataclass
class Unit:
    id_: int
    key: str
    plant: Plant
    type_: const.UnitType
    name: str
    power: float

@dataclass
class Measurements:
    plant_key_name: str
    unit_key_name: str
    measured_at: int
    measurements: int
    updated_at: int
