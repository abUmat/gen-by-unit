import requests
from datetime import date, datetime, timedelta
import const, model

def get_measurements(target_date_from: date, target_date_to: date) -> list[model.Measurements]:
    '''
    閉区間[target_date_from, target_date_to]のユニット別発電実績をOCCTOの公開システムから取得し,
    [(発電所名, ユニット名, 対象コマ開始時UNIX TIME, 発電量kWh, 更新日時UNIX TIME)]を返す
    '''

    # csv request params 呪文
    params = [
        ('areaCheckbox', '99'),
        ('hatudenHosikiCheckbox', '99'),
        ('tgtDateDateFrom', target_date_from.strftime(const.DATE_FORMAT_SLASHED)),
        ('tgtDateDateTo', target_date_to.strftime(const.DATE_FORMAT_SLASHED)),
    ]
    # search request params
    # なぜかmultipart/form-dataなのでこの形式を用いる
    form_data = [(x, (None, y)) for x, y in params]

    session = requests.session()

    # sessionの履歴のために無駄打ちリクエストを2回
    if not session.post(const.BASE_URL + const.DISCLAIMER_ENDPOINT, params={'agreed': 0}).ok: exit()
    if not session.post(const.BASE_URL + const.SEARCH_ENDPOINT, files=form_data).ok: exit()

    # csv取得
    response = session.get(const.BASE_URL + const.DOWNLOAD_ENDPOINT, params=params)
    firstloop = True # for skipping header
    ret = []
    for row in response.text.split('\n'):
        if len(row) == 0: break # last row
        if firstloop: # skip header
            firstloop = False
            continue
        _, _, plant_name, unit_name, _, dt, *measurements_s, _, updated_at = [x.strip().strip('"') for x in row.split(',')]
        measurements = [int(x) if x else 0 for x in measurements_s] # str to int

        dt = int(datetime.strptime(dt, const.DATE_FORMAT_SLASHED).timestamp())
        delta = timedelta(minutes=30).seconds
        updated_at = int(datetime.strptime(updated_at, const.DATETIME_FORMAT_SLASHED).timestamp())
        ret += [model.Measurements(plant_name, unit_name, dt + i * delta, m, updated_at) for i, m in enumerate(measurements)]
    return ret

def get_groups() -> list[model.Group]:
    '''
    groups.csvのデータをリストとして返す
    '''
    with open(const.GROUPS_CSV_PATH) as f:
        rows = f.readlines()
        rows.pop(0) # delete header
        records = [row.strip().split(',') for row in rows]
    return [model.Group(const.Area(int(area)), name) for area, name in records]

def get_plants() -> list[model.Plant]:
    '''
    groups.csvとplants.csvのデータを結合し, Plantのリストとして返す\n
    select * from plants\n
    inner join groups on plants.group_id = groups.id\n
    のイメージ
    '''
    with open(const.PLANTS_CSV_PATH) as f:
        rows = f.readlines()
        rows.pop(0) # delete header
        records = [row.strip().split(',') for row in rows]
    groups = get_groups()
    return [model.Plant(groups[int(group_id) - 1], key, name) for group_id, key, name in records]

def get_units() -> list[model.Unit]:
    '''
    units.csvとplants.csvとgroups.csvのデータを結合し, Unitのリストとして返す\n
    select * from units\n
    inner join plants on units.plant_id = plants.id\n
    inner join groups on plants.group_id = groups.id\n
    のイメージ
    '''
    with open(const.UNITS_CSV_PATH) as f:
        rows = f.readlines()
        rows.pop(0) # delete header
        records = [row.strip().split(',') for row in rows]
    plants = get_plants()
    return [model.Unit(key,
                       plants[int(plant_id) - 1],
                       const.UnitType(int(type_)),
                       name,
                       float(power))
            for plant_id, key, type_, name, power in records]

def unit_dict(units: list[model.Unit]) -> dict[tuple[str, str], model.Unit]:
    '''
    (発電所判別名, ユニット判別名)をキーにしてmodel.Unitを返す辞書を作成\n
    '''
    ret = {}
    for unit in units:
        key = unit.plant.key, unit.key
        ret[key] = unit
    return ret
