import requests
from datetime import date, timedelta
import const

if __name__ == '__main__':
    plants = []
    plant_ids = {}
    units = []
    params = [
        ('areaCheckbox', '99'),
        ('hatudenHosikiCheckbox', '99'),
        ('tgtDateDateFrom', (date.today() - timedelta(days=2)).strftime('%Y/%m/%d')),
        ('tgtDateDateTo', (date.today() - timedelta(days=2)).strftime('%Y/%m/%d')),
    ]
    form_data = [(x, (None, y)) for x, y in params]

    session = requests.session()
    if not session.post(const.BASE_URL + const.DISCLAIMER_ENDPOINT, params={'agreed': 0}).ok: exit()
    if not session.post(const.BASE_URL + const.SEARCH_ENDPOINT, files=form_data).ok: exit()

    response = session.get(const.BASE_URL + const.DOWNLOAD_ENDPOINT, params=params)
    firstloop = True
    ret = []
    for raw_row in response.text.split('\n'):
        if len(raw_row) == 0: break
        if firstloop:
            firstloop = False
            continue
        row = [x.strip('"') for x in raw_row.split(',')]
        if row[1] == '北海道':
            area = const.Area.HOKKAIDO
        elif row[1] == '東北':
            area = const.Area.TOHOKU
        elif row[1] == '東京':
            area = const.Area.TOKYO
        elif row[1] == '中部':
            area = const.Area.CHUBU
        elif row[1] == '北陸':
            area = const.Area.HOKURIKU
        elif row[1] == '関西':
            area = const.Area.KANSAI
        elif row[1] == '中国':
            area = const.Area.CHUGOKU
        elif row[1] == '四国':
            area = const.Area.SHIKOKU
        elif row[1] == '九州':
            area = const.Area.KYUSHU
        elif row[1] == '沖縄':
            area = const.Area.OKINAWA
        else:
            print(row)
            exit()
        plant_name = row[2]
        plant = (area.value, plant_name)
        if plant not in plant_ids.keys():
            plants.append(plant)
            plant_ids[plant] = len(plants)

        plant_id = plant_ids[plant]
        unit_name = row[3]
        if row[4] == '原子力':
            unit_type = const.UnitType.NUCLEAR
        elif row[4] == '水力':
            unit_type = const.UnitType.HYDRO
        elif row[4] == '火力（石炭）':
            unit_type = const.UnitType.COAL
        elif row[4] == '火力（ガス）':
            unit_type = const.UnitType.LNG
        elif row[4] == '火力（石油）':
            unit_type = const.UnitType.OIL
        elif row[4] == '地熱':
            unit_type = const.UnitType.GEOTHERMAL
        elif row[4] == '風力':
            unit_type = const.UnitType.WIND
        elif row[4] == '太陽光・太陽熱':
            unit_type = const.UnitType.SOLAR
        elif row[4] == 'その他' or row[4] == '':
            unit_type = const.UnitType.OTHER
        else:
            print(row)
            exit()
        unit = (plant_id, unit_type.value, unit_name)
        units.append(unit)
    with open('./plant_data/plants.csv', 'w') as f:
        print('area,name', file=f)
        print('\n'.join(','.join(map(str, plant)) for plant in plants), file=f)
    with open('./plant_data/units.csv', 'w') as f:
        print('plant_id,type,name', file=f)
        print('\n'.join(','.join(map(str, unit)) for unit in units), file=f)
