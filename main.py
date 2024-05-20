from datetime import datetime, timedelta, timezone
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from collections import defaultdict
from os import makedirs
from shutil import rmtree
import lib, const, tweepy_client

JST = timezone(timedelta(hours=+9), 'JST')

def setup():
    rmtree(const.IMG_PATH, ignore_errors=True)
    makedirs(const.IMG_PATH, exist_ok=True)

if __name__ == '__main__':
    setup()
    groups = lib.get_groups()
    units = lib.get_units()
    unit_dict = lib.unit_dict(units)

    frm = to = datetime.now(JST).date() - timedelta(days=2)
    measurements = lib.get_measurements(frm, to)
    # 測定日時の順で発電量をソート
    measurements.sort(key=lambda x: x.measured_at)

    # ユニットごとに48コマ発電を入れる
    gen_by_unit = defaultdict(list)
    for m in measurements:
        u = unit_dict[(m.plant_key_name, m.unit_key_name)]
        # mはkWh/30minなのでMWに変換
        gen_by_unit[u].append(m.measurements * 2 * 1e-3)

    img_cnt = 0

    for area in const.Area:
        target_groups = [g for g in groups if g.area == area]

        # 今回ループのエリアの画像枚数 切り上げる
        img_cnt_per_area = (len(target_groups) + const.GRAPH_CNT_IN_IMG - 1) // const.GRAPH_CNT_IN_IMG

        for i in range(img_cnt_per_area):
            path = f'{const.IMG_PATH}/{img_cnt:02}.png'
            # 画像設定
            plt.figure(figsize=const.IMG_SIZE)
            plt.subplots_adjust(left=0.03, right=0.92, bottom=0.05, top=0.90, wspace=0.45, hspace=0.3)

            # グラフ描画
            for j, group in enumerate(target_groups[i * const.GRAPH_CNT_IN_IMG: (i + 1) * const.GRAPH_CNT_IN_IMG]):
                # 画像内の場所指定 matplotlibでは, 左上から横向きに順番付けされているが, 縦に並べたいので適当に変換する
                position = (j % const.GRAPH_ROW_CNT) * const.GRAPH_COL_CNT + j // const.GRAPH_ROW_CNT + 1

                lib.subplot(group, units, gen_by_unit, position, const.IPA_GOTHIC_FONT_PATH)
            # 画像保存
            plt.suptitle(area.to_str(), fontproperties=fm.FontProperties(fname=const.IPA_GOTHIC_FONT_PATH), fontsize=const.GRAPH_SUPTITLE_FONT_SIZE)
            plt.savefig(path)
            plt.close()
            lib.add_citation(path, const.IPA_GOTHIC_FONT_PATH)
            img_cnt += 1

    # tweet
    text_s = [f'{frm.isoformat()}のユニット別発電実績']
    images = [f'{const.IMG_PATH}/{i:02}.png' for i in range(img_cnt)] # 全画像のパス
    media_paths_s = [images[i: i + const.TWITTER_MEDIA_CNT_PER_TWEET] for i in range(0, img_cnt, const.TWITTER_MEDIA_CNT_PER_TWEET)] # 4枚ごとのリストに変換
    client = tweepy_client.TweepyClient(const.TWITTER_API_CONFIG_FILE_PATH)
    # client.tweet_many(text_s, media_paths_s)
