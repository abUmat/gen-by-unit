import json
import model

def load_areas() -> list[model.Area]:
    '''
    areas.jsonのデータをリストとして返す
    '''
    with open('./json_data/areas.json') as f:
        area_json_list = json.load(f)
    return [model.Area(**area) for area in area_json_list]

def load_groups() -> list[model.Group]:
    '''
    groups.jsonのデータをリストとして返す
    '''
    with open('./json_data/groups.json') as f:
        group_json_list = json.load(f)
    return [model.Group(**group) for group in group_json_list]

def load_units() -> list[model.Unit]:
    '''
    units.jsonのデータをリストとして返す
    '''
    with open('./json_data/units.json') as f:
        unit_json_list = json.load(f)
    return [model.Unit(**unit) for unit in unit_json_list]

def load_unit_types() -> list[model.UnitType]:
    '''
    unit_types.jsonのデータをリストとして返す
    '''
    with open('./json_data/unit_types.json') as f:
        unit_type_json_list = json.load(f)
    return [model.UnitType(**unit_type) for unit_type in unit_type_json_list]

def load_fuel_types() -> list[model.FuelType]:
    '''
    fuel_types.jsonのデータをリストとして返す
    '''
    with open('./json_data/fuel_types.json') as f:
        fuel_type_json_list = json.load(f)
    return [model.FuelType(**fuel_type) for fuel_type in fuel_type_json_list]

def load_colors() -> list[model.Colors]:
    '''
    colors.jsonのデータをリストとして返す
    '''
    with open('./json_data/colors.json') as f:
        color_json_list = json.load(f)
    return [model.Colors(**color) for color in color_json_list]

def omit_long_term_shutdown_groups(groups: list[model.Group], units: list[model.Unit]) -> list[model.Group]:
    ret: list[model.Group] = []
    for group in groups:
        for unit in units:
            if group.group_id == unit.group_id and not unit.long_term_shutdown:
                ret.append(group)
                break
    return ret

def omit_long_term_shutdown_units(units: list[model.Unit]) -> list[model.Unit]:
    return [unit for unit in units if not unit.long_term_shutdown]

def join_data(
        areas: list[model.Area],
        groups: list[model.Group],
        units: list[model.Unit],
        unit_types: list[model.UnitType],
        fuel_types: list[model.FuelType],
        colorss: list[model.Colors],
        ) -> list[model.UnitSummary]:
    '''
    データを結合し, UnitSummaryのリストとして返す
    '''
    ret: list[model.UnitSummary] = []
    for unit in units:
        unit_summary = model.UnitSummary()
        unit_summary.unit = unit
        for group in groups:
            if unit_summary.unit.group_id == group.group_id:
                unit_summary.group = group
                break
        for area in areas:
            if unit_summary.group.area_id == area.area_id:
                unit_summary.area = area
                break
        for unit_type in unit_types:
            if unit_summary.unit.unit_type_id == unit_type.unit_type_id:
                unit_summary.unit_type = unit_type
                break
        for fuel_type in fuel_types:
            if unit_summary.unit_type.fuel_type_id == fuel_type.fuel_type_id:
                unit_summary.fuel_type = fuel_type
                break
        for colors in colorss:
            if unit_summary.fuel_type.colors_id == colors.colors_id:
                unit_summary.colors = colors
                break
        ret.append(unit_summary)
    return ret

def kwh30min_to_mw(kwh30min: float) -> float:
    'kWh/30minをMWに変換'
    return kwh30min * 2 * 1e-3

def hyphen_equal(a: str, b: str) -> bool:
    'ハイフン表記ゆれでもequalと判定するため'
    if a == b: return True
    hyphens = '-', 'ー', '－'
    for i in range(len(hyphens)):
        for j in range(len(hyphens)):
            if a.replace(hyphens[i], hyphens[j]) == b:
                return True
    return False
