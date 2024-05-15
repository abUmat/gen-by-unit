from datetime import date, timedelta
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import json
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
    makedirs(const.IMG_PATH, exist_ok=True)
    units = lib.select_all_units()

    # units.csvの順でグラフを作成するのでその順にタイトルをソート
    titles = [(unit.plant.name, unit.name) for unit in sorted(units.values(), key=lambda x: x.id_)]

    frm = to = date.today() - timedelta(days=2)
    measurements = lib.get_measurements(frm, to)

    # units.csvの順, その中で測定日時の順で発電量をソート
    measurements.sort(key=lambda x: (units[x.plant_name, x.unit_name].id_, x.measured_at))

    # ユニットごとに48コマ(発電, 認定出力)を入れる二次元配列
    values = [[] for _ in range(len(units))]
    for m in measurements:
        unit = units[(m.plant_name, m.unit_name)]
        # mはkWh/30min, unit.powerは万kWなのでMWに変換
        values[unit.id_ - 1].append((m.measurements * 2 * 1e-3, unit.power * 1e4 * 1e-3))

    # 画像枚数 切り上げる
    img_cnt = (len(values) + const.GRAPH_CNT_IN_IMG - 1) // const.GRAPH_CNT_IN_IMG

    for i in range(img_cnt):
        # 対象画像中のグラフに使用するタイトルと値を選択
        ts, vs = titles[i * 24:(i + 1) * 24], values[i * 24:(i + 1) * 24]

        # 画像設定
        plt.figure(figsize=const.IMG_SIZE)
        plt.subplots_adjust(left=0.03, right=0.99, bottom=0.05, top=0.97)

        # グラフ描画
        for j, (title, value) in enumerate(zip(ts, vs)):
            # 画像内の場所指定
            # matplotlibでは, 1から横向きに順番付けされているが, 縦に並べたいので適当に変換する
            position = (j % const.GRAPH_ROW_CNT) * const.GRAPH_COL_CNT + j // const.GRAPH_ROW_CNT + 1
            plt.subplot(const.GRAPH_ROW_CNT, const.GRAPH_COL_CNT, position)

            plt.title(f'{title[0]}：{title[1]}', fontproperties=gothic_font)
            plt.plot(value)
            plt.ylabel('MW')
            plt.ylim(bottom=0)

            plt.xlim((-1, 48))
            plt.xticks([0, 12, 24, 36, 47], ['00:00', '06:00', '12:00', '18:00', '24:00'])
            plt.legend(['発電', '認可出力'], prop=gothic_font)
        # 画像保存
        plt.savefig(f'{const.IMG_PATH}/{i:02}.png')
        plt.close()
    client = TweepyClient('./config.json')
    for i in range((img_cnt + 3) // 4):
        inner_loop_cnt = min(4, img_cnt - i * 4) # 残りの画像が4枚未満の時はその枚数を指定する
        client.tweet(f'{frm.isostring()}のユニット別発電実績', [f'./img/{(i+j):02}.png' for j in range(inner_loop_cnt)])
    rmtree(const.IMG_PATH)

