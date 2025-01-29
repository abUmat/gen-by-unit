import requests
from datetime import date, datetime, timedelta
import sys
sys.path.append('./packages')
from packages.matplotlib import pyplot as plt
from packages.PIL import Image, ImageDraw, ImageFont
import const, model, lib_inner

def load_model() -> tuple[list[model.Area], list[model.Group], list[model.UnitSummary]]:
    areas = lib_inner.load_areas()
    groups = lib_inner.omit_long_term_shutdown_groups(lib_inner.load_groups(), lib_inner.load_units())
    units = lib_inner.omit_long_term_shutdown_units(lib_inner.load_units())
    unit_types = lib_inner.load_unit_types()
    fuel_types = lib_inner.load_fuel_types()
    colorss = lib_inner.load_colors()
    unit_summaries = lib_inner.join_data(areas, groups, units, unit_types, fuel_types, colorss)
    return areas, groups, unit_summaries

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

def insert_generations_to_unit_summary(unit_summaries: list[model.UnitSummary], measurements: list[model.Measurements]):
    measurements.sort(key=lambda x: x.measured_at)
    for m in measurements:
        for unit_summary in unit_summaries:
            if m.plant_name == unit_summary.unit.plant_name and m.unit_name == unit_summary.unit.unit_name:
                unit_summary.generations.append(lib_inner.kwh30min_to_mw(m.measurements))

def create_area_graphs(
        area: model.Area,
        groups: list[model.Group],
        unit_summaries: list[model.UnitSummary],
        frm: date,
        img_cnt: int,
        ) -> tuple[str, list[str], int]:
    target_groups = [g for g in groups if g.area_id == area.area_id]

    # エリアの画像枚数 切り上げる
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

            subplot(group, unit_summaries, position, const.IPA_GOTHIC_FONT_PATH)

        # 画像保存
        plt.suptitle(area.name, fontproperties={'fname': const.IPA_GOTHIC_FONT_PATH}, fontsize=const.GRAPH_SUPTITLE_FONT_SIZE)
        plt.savefig(path)
        plt.close()

        add_citation(path, const.IPA_GOTHIC_FONT_PATH)
        img_cnt += 1

    return text, images, img_cnt

def subplot(group: model.Group,
            unit_summaries: list[model.UnitSummary],
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
    for unit_summary in unit_summaries:
        if unit_summary.group.group_id != group.group_id: continue
        if unit_summary.generations == []:
            generations.append([0] * 48)
        else:
            generations.append(unit_summary.generations[::])
        # unit.powerは万kWなのでMWに変換
        power_limit += unit_summary.unit.power * 1e4 * 1e-3
        labels.append(f'{unit_summary.unit.name}{":" if unit_summary.unit.name else ""}{unit_summary.unit_type.name}')
        # color 燃料別 かぶらないように
        for c in unit_summary.colors.color_codes:
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
