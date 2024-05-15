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

def select_all_plants() -> list[model.Plant]:
    '''
    plants.csvのデータをリストとして返す
    '''
    with open(const.PLANTS_CSV_PATH) as f:
        rows = f.readlines()
        rows.pop(0) # delete header
        records = [row.strip().split(',') for row in rows]
    return [model.Plant(name, const.Area(int(area))) for area, name in records]

def select_all_units() -> dict[tuple[str, str], model.Unit]:
    '''
    units.csvのデータとplants.csvのデータを結合し, key: (plant_name, unit_name), value: Unitのdictを返す
    '''
    with open(const.UNITS_CSV_PATH) as f:
        rows = f.readlines()
        rows.pop(0) # delete header
        records = [row.strip().split(',') for row in rows]
    plants = select_all_plants()
    return {(plants[int(plant_id) - 1].name, name): model.Unit(i, plants[int(plant_id) - 1], const.UnitType(int(type_)), name, float(power)) for i, (plant_id, type_, name, power) in enumerate(records)}
