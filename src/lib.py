import requests
import json
from datetime import date, datetime, timedelta
import sys
sys.path.append('./packages')
from packages.matplotlib import pyplot as plt
from packages.PIL import Image, ImageDraw, ImageFont
import const, model

def kwh30min_to_mw(kwh30min: float) -> float:
    'kWh/30minをMWに変換'
    return kwh30min * 2 * 1e-3

def get_request_date_param_by_time() -> date:
    '''
    現在時刻によってリクエスト日を決定する
    '''
    now = datetime.now(const.JST)
    if now.hour >= const.OCCTO_REQUEST_HOUR_TH:
        return now.date() - timedelta(days=1)
    return now.date() - timedelta(days=2)

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
    try:
        session.post(const.BASE_URL + const.DISCLAIMER_ENDPOINT, params={'agreed': 0}).raise_for_status()
    except Exception as e:
        raise e
    try:
        session.post(const.BASE_URL + const.SEARCH_ENDPOINT, files=form_data).raise_for_status()
    except Exception as e:
        raise e

    # csv取得
    try:
        response = session.get(const.BASE_URL + const.DOWNLOAD_ENDPOINT, params=params)
        response.raise_for_status()
    except Exception as e:
        raise e
    ret = []
    for i, row in enumerate(response.text.split('\n')):
        if len(row) == 0: break # last row
        if not i: # skip header
            continue
        splited = row.split(',')
        if len(splited) != 56:
            raise model.CSVParseError(f'column missing in csv file', i)

        _, _, plant_name, unit_name, _, dt, *measurements_s, _, updated_at = [x.strip().strip('"') for x in splited]

        try:
            measurements = [int(x) if x else 0 for x in measurements_s] # str to int
            dt = int(datetime.strptime(dt, const.DATE_FORMAT_SLASHED).timestamp()) # dtのunixtime
            delta = timedelta(minutes=30).seconds
            updated_at = int(datetime.strptime(updated_at, const.DATETIME_FORMAT_SLASHED).timestamp()) # updated_atのunixtime
        except Exception as e:
            raise model.CSVParseError(f'row contents is not expected: {row}', i)

        ret += [model.Measurements(plant_name=plant_name, unit_name=unit_name, measured_at=dt + i * delta, measurements=m, updated_at=updated_at) for i, m in enumerate(measurements)]
    return ret

def _load_areas() -> list[model.Area]:
    '''
    areas.jsonのデータをリストとして返す
    '''
    with open('./json_data/areas.json') as f:
        area_json_list = json.load(f)
    return [model.Area(**area) for area in area_json_list]

def _load_groups() -> list[model.Group]:
    '''
    groups.jsonのデータをリストとして返す
    '''
    with open('./json_data/groups.json') as f:
        group_json_list = json.load(f)
    return [model.Group(**group) for group in group_json_list]

def _load_units() -> list[model.Unit]:
    '''
    units.jsonのデータをリストとして返す
    '''
    with open('./json_data/units.json') as f:
        unit_json_list = json.load(f)
    return [model.Unit(**unit) for unit in unit_json_list]

def _load_unit_types() -> list[model.UnitType]:
    '''
    unit_types.jsonのデータをリストとして返す
    '''
    with open('./json_data/unit_types.json') as f:
        unit_type_json_list = json.load(f)
    return [model.UnitType(**unit_type) for unit_type in unit_type_json_list]

def _load_fuel_types() -> list[model.FuelType]:
    '''
    fuel_types.jsonのデータをリストとして返す
    '''
    with open('./json_data/fuel_types.json') as f:
        fuel_type_json_list = json.load(f)
    return [model.FuelType(**fuel_type) for fuel_type in fuel_type_json_list]

def _load_colors() -> list[model.Colors]:
    '''
    colors.jsonのデータをリストとして返す
    '''
    with open('./json_data/colors.json') as f:
        color_json_list = json.load(f)
    return [model.Colors(**color) for color in color_json_list]

def _omit_long_term_shutdown_groups(groups: list[model.Group], units: list[model.Unit]) -> list[model.Group]:
    ret: list[model.Group] = []
    for group in groups:
        for unit in units:
            if group.group_id == unit.group_id and not unit.long_term_shutdown:
                ret.append(group)
                break
    return ret

def _omit_long_term_shutdown_units(units: list[model.Unit]) -> list[model.Unit]:
    return [unit for unit in units if not unit.long_term_shutdown]

def _join_data(
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

def _unit_dict(units: list[model.UnitSummary]) -> dict[tuple[str, str], model.UnitSummary]:
    '''
    (発電所判別名, ユニット判別名)をキーにしてmodel.Unitを返す辞書を作成\n
    '''
    ret = {}
    for unit in units:
        key = unit.unit.plant_name, unit.unit.unit_name
        ret[key] = unit
    return ret

def load_data() -> tuple[list[model.Area], list[model.Group], list[model.UnitSummary], dict[tuple[str, str], model.UnitSummary]]:
    areas = _load_areas()
    groups = _omit_long_term_shutdown_groups(_load_groups(), _load_units())
    units = _omit_long_term_shutdown_units(_load_units())
    unit_types = _load_unit_types()
    fuel_types = _load_fuel_types()
    colorss = _load_colors()
    unit_summaries = _join_data(areas, groups, units, unit_types, fuel_types, colorss)
    unit_dict = _unit_dict(unit_summaries)
    return areas, groups, unit_summaries, unit_dict

def create_area_graphs(
        area: model.Area,
        groups: list[model.Group],
        unit_summaries: list[model.UnitSummary],
        gen_by_unit: dict[model.UnitSummary, list[float]],
        frm: date,
        img_cnt: int,
        ) -> tuple[str, list[str], int]:
    target_groups = [g for g in groups if g.area_id == area.area_id]

    # 今回ループのエリアの画像枚数 切り上げる
    img_cnt_per_area = (len(target_groups) + const.GRAPH_CNT_IN_IMG - 1) // const.GRAPH_CNT_IN_IMG

    # ツイート内容
    text = f'{area.name} {frm.isoformat()}のユニット別発電実績'
    images = [[f'{const.IMG_PATH}/{img_cnt + i:02}.png' for i in range(img_cnt_per_area)]]

    for i in range(img_cnt_per_area):
        path = f'{const.IMG_PATH}/{img_cnt:02}.png'
        # 画像設定
        plt.figure(figsize=const.IMG_SIZE)
        plt.subplots_adjust(left=0.03, right=0.92, bottom=0.05, top=0.90, wspace=0.45, hspace=0.3)

        # グラフ描画
        for j, group in enumerate(target_groups[i * const.GRAPH_CNT_IN_IMG: (i + 1) * const.GRAPH_CNT_IN_IMG]):
            # 画像内の場所指定 matplotlibでは, 左上から横向きに順番付けされているが, 縦に並べたいので適当に変換する
            position = (j % const.GRAPH_ROW_CNT) * const.GRAPH_COL_CNT + j // const.GRAPH_ROW_CNT + 1

            subplot(group, unit_summaries, gen_by_unit, position, const.IPA_GOTHIC_FONT_PATH)

        # 画像保存
        plt.suptitle(area.name, fontproperties={'fname': const.IPA_GOTHIC_FONT_PATH}, fontsize=const.GRAPH_SUPTITLE_FONT_SIZE)
        plt.savefig(path)
        plt.close()

        add_citation(path, const.IPA_GOTHIC_FONT_PATH)
        img_cnt += 1

    return text, images, img_cnt

def subplot(group: model.Group,
            units: list[model.UnitSummary],
            gen_by_unit: dict[model.Unit, list[float]],
            position: int,
            font_path: str) -> None:
    '''
    groupに所属するunitの発電量と認可出力をpositionで指定した位置にsubplotする
    '''
    # 場所指定
    plt.subplot(const.GRAPH_ROW_CNT, const.GRAPH_COL_CNT, position)

    plt.title(label=group.name, fontproperties={'fname': font_path}, fontsize=const.GRAPH_TITLE_FONT_SIZE)

    # 発電と認可出力の集計
    generations = []
    power_limit = 0
    labels = []
    colors = []
    for u in units:
        if u.group.group_id != group.group_id: continue
        generations.append(gen_by_unit.get(u, [0] * 48))
        # unit.powerは万kWなのでMWに変換
        power_limit += u.unit.power * 1e4 * 1e-3
        labels.append(f'{u.unit.name}{":" if u.unit.name else ""}{u.unit_type.name}')
        # color 燃料別 かぶらないように
        for c in u.colors.color_codes:
            if c not in colors:
                colors.append(c)
                break
        else:
            raise Exception('The number of colors is not sufficient.')

    # 上から1号機, 2号機の順に積みあがってほしいので逆転させる
    generations.reverse()
    labels.reverse()
    colors.reverse()
    plt.stackplot(range(48), generations, labels=labels, colors=colors, edgecolor='black')
    plt.plot([power_limit] * 48, '-.', color='grey')

    plt.ylabel('MW')
    plt.ylim(bottom=0)

    plt.xlim((-1, 48))
    plt.xticks([0, 12, 24, 36, 47], ['00:00', '06:00', '12:00', '18:00', '24:00'])

    # 凡例の順番を上から1号機, 2号機となるようにする
    h, l = plt.gca().get_legend_handles_labels()
    # 凡例
    plt.legend(h[::-1],
               l[::-1],
               loc='lower left',
               bbox_to_anchor=(1, 0),
               prop={'fname': font_path})

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
