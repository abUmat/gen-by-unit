import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from collections import defaultdict
from os import makedirs
from shutil import rmtree
import requests
import json
import lib, const, model, tweepy_client
from log_config import logger


def main():
    rmtree(const.IMG_PATH, ignore_errors=True)
    makedirs(const.IMG_PATH, exist_ok=True)
    groups = lib.get_groups()
    units = lib.get_units()
    unit_dict = lib.unit_dict(units)

    frm = to = lib.get_request_date_param_by_time()
    logger.info(f'from: {frm.isoformat()}, to: {to.isoformat()}')
    measurements = lib.get_measurements(frm, to)
    logger.info('Measurement data retrieval completed successfully.')
    # 測定日時の順で発電量をソート
    measurements.sort(key=lambda x: x.measured_at)

    # ユニットごとに48コマ発電を入れる
    gen_by_unit: defaultdict[model.Unit, list[float]] = defaultdict(list)
    for m in measurements:
        try:
            u = unit_dict[(m.plant_key_name, m.unit_key_name)]
        except Exception as e:
            raise e
        # mはkWh/30minなのでMWに変換
        gen_by_unit[u].append(m.measurements * 2 * 1e-3)

    img_cnt = 0
    # ツイートするテキストと画像
    all_text_s: list[str] = []
    all_images_s: list[list[str]] = []

    for area in const.Area:
        target_groups = [g for g in groups if g.area == area]

        # 今回ループのエリアの画像枚数 切り上げる
        img_cnt_per_area = (len(target_groups) + const.GRAPH_CNT_IN_IMG - 1) // const.GRAPH_CNT_IN_IMG

        # ツイート内容
        text_s: list[str] = []
        images_s: list[list[str]] = []
        for i in range(0, img_cnt_per_area, const.TWITTER_MEDIA_CNT_PER_TWEET):
            text_s.append(f'{area.to_str()} {frm.isoformat()}のユニット別発電実績{f"その{i // const.TWITTER_MEDIA_CNT_PER_TWEET + 1}" if i else ""}')
            images_s.append([f'{const.IMG_PATH}/{img_cnt + j:02}.png' for j in range(i, min(img_cnt_per_area, i + const.TWITTER_MEDIA_CNT_PER_TWEET))])
        all_text_s += text_s
        all_images_s += images_s

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
            logger.info(f'Image successfully saved to {path}')
            plt.close()

            lib.add_citation(path, const.IPA_GOTHIC_FONT_PATH)
            logger.info(f'Successfully added attribution to {path}')
            img_cnt += 1

    # ツイートをまとめる
    all_text_s_merged = []
    all_images_s_merged = []
    for t, img in zip(all_text_s, all_images_s):
        if len(all_images_s_merged) > 0 and len(all_images_s_merged[-1]) + len(img) <= const.TWITTER_MEDIA_CNT_PER_TWEET:
            all_text_s_merged[-1] += '\n' + t
            all_images_s_merged[-1] += img
        else:
            all_text_s_merged.append(t)
            all_images_s_merged.append(img)
    # tweet
    client = tweepy_client.TweepyClient(const.TWITTER_API_CONFIG_FILE_PATH)
    client.tweet_many(all_text_s, all_images_s)
    txt = '\n\t\t\t\t' + '\n\t\t\t\t'.join([f'{text} with image {img}' for text, img in zip(all_text_s, all_images_s)])
    logger.info(f'Successfully tweeted message {txt}')

def handler(event, context):
    try:
        main()
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Request successful'
            })
        }
    except requests.exceptions.RequestException as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': str(e)
            })
        }
    except model.CSVParseError as e:
        return {
            'statusCode': 502,
            'body': json.dumps({
                'error': str(e)
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

if __name__ == '__main__':
    logger.info(handler(None, None))

