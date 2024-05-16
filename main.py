from datetime import date, timedelta
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import json
from collections import defaultdict
from os import makedirs
from shutil import rmtree
import lib, const

import sys
sys.path.append('./packages')
from packages import tweepy

gothic_font = fm.FontProperties(fname=const.IPA_GOTHIC_FONT_PATH)
minchou_font = fm.FontProperties(fname=const.IPA_MINCHOU_FONT_PATH)

class TweepyClient:
    def __init__(self, config_file_path: str) -> None:
        config = json.load(open(config_file_path, 'r'))
        self.client = tweepy.Client(config['twitter']['bearerToken'],
                                    config['twitter']['consumerKey'],
                                    config['twitter']['consumerSecret'],
                                    config['twitter']['accessToken'],
                                    config['twitter']['accessTokenSecret']
                                    )
        auth = tweepy.OAuthHandler(config['twitter']['consumerKey'],
                                   config['twitter']['consumerSecret'])
        auth.set_access_token(config['twitter']['accessToken'],
                              config['twitter']['accessTokenSecret'])
        self.api = tweepy.API(auth)
    def tweet(self, text: str, media_paths: list[str]=[]) -> None:
        if not media_paths:
            self.client.create_tweet(text=text)
        media = [self.api.media_upload(filename=media_path) for media_path in media_paths]
        self.client.create_tweet(text=text, media_ids=[m.media_id for m in media])

if __name__ == '__main__':
    rmtree(const.IMG_PATH, ignore_errors=True)
    makedirs(const.IMG_PATH, exist_ok=True)

    groups = lib.get_groups()
    plants = lib.get_plants()
    units = lib.get_units()
    unit_dict = lib.unit_dict(units)

    frm = to = date.today() - timedelta(days=2)
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

        # 画像枚数 切り上げる
        img_cnt_per_area = (len(target_groups) + const.GRAPH_CNT_IN_IMG - 1) // const.GRAPH_CNT_IN_IMG

        for i in range(img_cnt_per_area):
            # 画像設定
            plt.figure(figsize=const.IMG_SIZE)
            plt.subplots_adjust(left=0.03, right=0.95, bottom=0.05, top=0.93, wspace=0.4)

            # グラフ描画
            for j, group in enumerate(target_groups[i * const.GRAPH_CNT_IN_IMG: (i + 1) * const.GRAPH_CNT_IN_IMG]):
                # 画像内の場所指定
                # matplotlibでは, 1から横向きに順番付けされているが, 縦に並べたいので適当に変換する
                position = (j % const.GRAPH_ROW_CNT) * const.GRAPH_COL_CNT + j // const.GRAPH_ROW_CNT + 1
                plt.subplot(const.GRAPH_ROW_CNT, const.GRAPH_COL_CNT, position)

                plt.title(group.name, fontproperties=gothic_font)
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
                        legends += [u.name]
                plt.plot(list(zip(*generations)))
                plt.plot(list(zip(*power_limits)))
                plt.ylabel('MW')
                plt.ylim(bottom=0)

                plt.xlim((-1, 48))
                plt.xticks([0, 12, 24, 36, 47], ['00:00', '06:00', '12:00', '18:00', '24:00'])
                if legends and legends[0]:
                    plt.legend(legends,
                            loc='lower left',
                            bbox_to_anchor=(1, 0),
                            ncol=(len(legends) + const.SUBPLOT_LEGENDS_ROW_CNT - 1) // const.SUBPLOT_LEGENDS_ROW_CNT,
                            prop=gothic_font)
            # 画像保存
            plt.suptitle(area.area_name(), fontproperties=gothic_font)
            plt.savefig(f'{const.IMG_PATH}/{img_cnt:02}.png')
            plt.close()
            img_cnt += 1
    client = TweepyClient('./config.json')
    # for i in range((img_cnt + 3) // 4):
    #     inner_loop_cnt = min(4, img_cnt - i * 4) # 残りの画像が4枚未満の時はその枚数を指定する
    #     client.tweet(f'{frm.isostring()}のユニット別発電実績', [f'./img/{(i+j):02}.png' for j in range(inner_loop_cnt)])
    # rmtree(const.IMG_PATH)

