from collections import defaultdict
from os import makedirs
from shutil import rmtree
import json
import sys
sys.path.append('./packages')
from packages import requests
import lib, const, model, tweepy_client
from log_config import logger

def main():
    # ディレクトリ作る
    rmtree(const.IMG_PATH, ignore_errors=True)
    makedirs(const.IMG_PATH, exist_ok=True)

    # load_data
    areas, groups, unit_summaries, unit_dict = lib.load_data()

    # api叩く
    frm = to = lib.get_request_date_param_by_time()
    logger.info(f'from: {frm.isoformat()}, to: {to.isoformat()}')
    measurements = lib.get_measurements(frm, to)
    logger.info('Measurement data retrieval completed successfully.')

    # 測定日時の順で発電量をソート
    measurements.sort(key=lambda x: x.measured_at)

    # ユニットごとに48コマ発電を入れる
    gen_by_unit: defaultdict[model.UnitSummary, list[float]] = defaultdict(list)
    for m in measurements:
        if (m.plant_name, m.unit_name) in unit_dict.keys():
            u = unit_dict[(m.plant_name, m.unit_name)]
            # mはkWh/30minなのでMWに変換
            gen_by_unit[u].append(lib.kwh30min_to_mw(m.measurements))
        elif m.measurements == 0:
            continue
        else:
            raise KeyError((m.plant_name, m.unit_name))

    img_cnt = 0
    # ツイートするテキストと画像
    all_text_s: list[str] = []
    all_images_s: list[list[str]] = []

    for area in areas:
        text, images, img_cnt = lib.create_area_graphs(area, groups, unit_summaries, gen_by_unit, frm, img_cnt)
        logger.info(f'Image successfully saved. area: {area.name}')

        # ツイート内容
        all_text_s.append(text)
        all_images_s += images

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
    # client.tweet_many(all_text_s_merged, all_images_s_merged)
    txt = '\n' + '\n\n'.join([f'{text}\n with image {img}' for text, img in zip(all_text_s_merged, all_images_s_merged)])
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
    main()
