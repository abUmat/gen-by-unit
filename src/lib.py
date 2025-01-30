from datetime import date, datetime, timedelta
from urllib.parse import urlencode
import csv
import re
import sys
sys.path.append('./packages')
from packages import requests
from packages.matplotlib import pyplot as plt
from packages.PIL import Image, ImageDraw, ImageFont
from packages.urllib3 import ssl
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
    'UnitSummary.generationsにmeasurementsから該当発電ユニットの発電量を見つけて挿入する'
    measurements.sort(key=lambda x: x.measured_at)
    for m in measurements:
        for unit_summary in unit_summaries:
            if m.plant_name == unit_summary.unit.plant_name and m.unit_name == unit_summary.unit.unit_name:
                unit_summary.generations.append(lib_inner.kwh30min_to_mw(m.measurements))

def get_hjks_outages(target_date_from: date, target_date_to: date):
    '''
    閉区間[target_date_from, target_date_to]のユニット別発電実績を発電情報公開システムから取得し,
    list[OutageDescription]を返す
    '''
    session = requests.session()

    # 呪文
    ssl_context = ssl.create_default_context()
    ssl_context.set_ciphers('DEFAULT:!aNULL:!eNULL:!MD5:!3DES:!DES:!RC4:!IDEA:!SEED:!aDSS:!SRP:!PSK')
    adapter = requests.adapters.HTTPAdapter()
    adapter.init_poolmanager(1, 1,  ssl_context=ssl_context)
    session.adapters.pop('https://', None)
    session.mount('https://', adapter)

    # csrfタグ取得のためのリクエスト
    response = session.get('https://hjks.jepx.or.jp/hjks/outages')
    response.raise_for_status()
    for row in response.text.split('\n'):
        if 'name' in row and '"_csrf"' in row:
            m = re.search(r'value="([\w-]+)"', row)
            if m:
                csrf_value = m.group(1)

    # sessionの履歴のためのリクエスト
    # 後のcsvダウンロードの時のpayloadと等しくする必要がある
    url = 'https://hjks.jepx.or.jp/hjks/outages'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {
        'startdtfrom': f'{target_date_from.strftime(const.DATE_FORMAT_SLASHED)} 00:00',
        'startdtto': f'{target_date_to.strftime(const.DATE_FORMAT_SLASHED)} 00:00',
        '_csrf': csrf_value
    }
    encoded_payload = urlencode(payload)
    response = session.post(url, data=encoded_payload, headers=headers)
    response.raise_for_status()

    # csv取得のためPOSTリクエストの送信
    payload['csv'] = 'csv'
    encoded_payload = urlencode(payload)
    response = session.post(url, data=encoded_payload, headers=headers)
    response.raise_for_status()

    # csvファイルに保存
    with open(f'{const.CSV_PATH}/output.csv', 'wb') as file:
        file.write(response.content)

    # encodingを変更とセル内の開業を削除
    with open(f'{const.CSV_PATH}/output.csv', mode='r', encoding='cp932', newline='') as infile:
        with open(f'{const.CSV_PATH}/output_modified.csv', mode='w', encoding='utf-8', newline='') as outfile:
            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            for row in reader:
                # 各セルの改行を削除
                cleaned_row = [cell.replace('\n', '').replace('\r', '').strip(',') for cell in row]
                writer.writerow(cleaned_row)

    # 末尾のカンマ削除するだけ
    with open(f'{const.CSV_PATH}/output_modified.csv') as infile:
        with open(f'{const.CSV_PATH}/output_ordered.csv', mode='w', encoding='utf-8') as outfile:
            for row in infile.readlines():
                print(row.strip().strip(','), file=outfile)

    # 返り値生成
    ret: list[model.OutageInformation] = []
    with open(f'{const.CSV_PATH}/output_ordered.csv') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i == 0: continue # header
            ret.append(model.OutageInformation(*row))
    return ret

def insert_outage_description_to_unit_summary(unit_summaries: list[model.UnitSummary], outage_informations: list[model.OutageInformation]):
    'UnitSummary.shutdown_descriptionにoutage_descriptionsから該当発電ユニットの停止情報を見つけて挿入する'
    outage_informations.sort(key=lambda x: x.updated_at)
    for outage_information in outage_informations:
        for unit_summary in unit_summaries:
            if lib_inner.hyphen_equal(unit_summary.unit.plant_name, outage_information.plant_name) and lib_inner.hyphen_equal(unit_summary.unit.unit_name, outage_information.unit_name):
                unit_summary.outage_description = outage_information.shutdown_type_name
                if outage_information.shutdown_type_name != '計画外停止':
                    unit_summary.outage_description += '　'
                unit_summary.outage_description += f':{outage_information.shutdown_detail} {outage_information.stopped_at}～{outage_information.will_restarted_at}'

def create_area_graphs(
        area: model.Area,
        groups: list[model.Group],
        unit_summaries: list[model.UnitSummary],
        frm: date,
        img_cnt: int,
        ) -> tuple[str, list[str], int]:
    groups_in_selected_area = [g for g in groups if g.area_id == area.area_id]

    # エリアの画像枚数 切り上げる
    img_cnt_per_area = (len(groups_in_selected_area) + const.GRAPH_CNT_IN_IMG - 1) // const.GRAPH_CNT_IN_IMG

    # ツイート内容
    text = f'{area.name} {frm.isoformat()}のユニット別発電実績'
    images = [[f'{const.IMG_PATH}/{img_cnt + i:02}.png' for i in range(img_cnt_per_area)]]


    for i in range(img_cnt_per_area):
        path = f'{const.IMG_PATH}/{img_cnt:02}.png'
        # 画像設定
        fig, axes = plt.subplots(4, 3, figsize=const.IMG_SIZE)
        fig.subplots_adjust(left=0.03, right=0.92, bottom=0.05, top=0.90, wspace=0.45, hspace=0.3)

        # グラフ描画
        groups_in_img = groups_in_selected_area[i * const.GRAPH_CNT_IN_IMG: (i + 1) * const.GRAPH_CNT_IN_IMG]

        for j in range(const.GRAPH_COL_CNT * const.GRAPH_ROW_CNT):
            ax = axes[j % const.GRAPH_ROW_CNT][j // const.GRAPH_ROW_CNT]
            if j < len(groups_in_img):
                group = groups_in_img[j]
                subplot(ax, group, unit_summaries, const.IPA_GOTHIC_FONT_PATH)
            else:
                fig.delaxes(ax)

        # 画像保存
        fig.suptitle(area.name, fontproperties={'fname': const.IPA_GOTHIC_FONT_PATH}, fontsize=const.GRAPH_SUPTITLE_FONT_SIZE)
        fig.savefig(path)
        plt.close(fig)

        add_citation(path, const.IPA_GOTHIC_FONT_PATH)
        img_cnt += 1

    return text, images, img_cnt

def subplot(ax: plt.Axes,
            group: model.Group,
            unit_summaries: list[model.UnitSummary],
            font_path: str) -> None:
    '''
    groupに所属するunitの発電量と認可出力をpositionで指定した位置にsubplotする
    '''
    # 場所指定
    ax.set_title(label=group.name, fontproperties={'fname': font_path}, fontsize=const.GRAPH_TITLE_FONT_SIZE)

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
    ax.stackplot(range(48), generations, labels=labels, colors=colors, edgecolor='black')
    ax.plot([power_limit] * 48, '-.', color='grey')

    ax.set_ylabel('MW')
    ax.set_ylim(bottom=0, top=power_limit*1.05)

    ax.set_xlim((-1, 48))
    ax.set_xticks([0, 12, 24, 36, 47])
    ax.set_xticklabels(['00:00', '06:00', '12:00', '18:00', '24:00'])

    # 凡例の順番を上から1号機, 2号機となるようにする
    h, l = ax.get_legend_handles_labels()
    # 凡例
    ax.legend(h[::-1],
              l[::-1],
              loc='lower left',
              bbox_to_anchor=(1, 0),
              prop={'fname': font_path})

    pos = 0.85
    for unit_summary in unit_summaries:
        if unit_summary.group.group_id != group.group_id: continue
        if unit_summary.outage_description != '':
            text = unit_summary.unit.name.replace('\n', '') + ':' + unit_summary.outage_description
            ax.text(
                0.01,
                pos,
                text,
                ha='left',
                transform=ax.transAxes,
                color='red',
                fontproperties={'fname': font_path},
                fontsize=const.GRAPH_TEXT_FONT_SIZE
            )
            pos -= 0.08


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
