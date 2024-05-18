import requests
from datetime import date, datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from PIL import Image, ImageDraw, ImageFont
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
    return [model.Plant(groups[int(group_id) - 1], key) for group_id, key in records]

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

def subplot(group: model.Group,
            plants: list[model.Plant],
            units: list[model.Unit],
            gen_by_unit: dict[tuple[str, str], model.Unit],
            position: int,
            fp: FontProperties) -> None:
    '''
    groupに所属するplant, unitの発電量と認可出力をpositionで指定した位置にsubplotする\n
    fpにmatplotlib.font_manager.FontPropertiesでフォントを指定する
    '''
    # 場所指定
    plt.subplot(const.GRAPH_ROW_CNT, const.GRAPH_COL_CNT, position)

    plt.title(group.name, fontproperties=fp)

    # 発電だけに凡例をつけたいのでちょっと工夫
    # 発電 -> 認可出力の順にプロットしたいので一旦集計
    generations = []
    power_limits = []
    legends = []
    for p in plants:
        if p.group != group: continue
        for u in units:
            if u.plant != p: continue
            generations.append(gen_by_unit[u])
            # unit.powerは万kWなのでMWに変換
            power_limits.append([u.power * 1e4 * 1e-3] * 48)
            legends.append(u.name)
    for g in generations:
        plt.plot(g)
    for pl in power_limits:
        plt.plot(pl)

    plt.ylabel('MW')
    plt.ylim(bottom=0)

    plt.xlim((-1, 48))
    plt.xticks([0, 12, 24, 36, 47], ['00:00', '06:00', '12:00', '18:00', '24:00'])

    # 凡例
    if legends and legends[0]:
        plt.legend(legends,
                   loc='lower left',
                   bbox_to_anchor=(1, 0),
                   ncol=(len(legends) + const.SUBPLOT_LEGENDS_ROW_CNT - 1) // const.SUBPLOT_LEGENDS_ROW_CNT,
                   prop=fp)

def add_citation(img_path: str, font_path: str) -> None:
    '''
    グラフ画像の右下に出典を記入し上書き保存する
    '''
    img = Image.open(img_path)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, const.OCCTO_CITATION_FONT_SIZE)
    padding = 10
    corner = const.IMG_SIZE
    position = [x * 100 - padding for x in corner]
    draw.text(position, const.OCCTO_CITATION, 'black', font=font, anchor='rd')
    img.save(img_path)
