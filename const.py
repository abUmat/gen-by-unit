import os
from datetime import timezone, timedelta

JST = timezone(timedelta(hours=+9), 'JST')

BASE_URL = 'https://hatsuden-kokai.occto.or.jp/hks-web-public'
DISCLAIMER_ENDPOINT = '/disclaimer-agree/next'
SEARCH_ENDPOINT = '/info/hks/search'
DOWNLOAD_ENDPOINT = '/info/hks/downloadCsv'
DATE_FORMAT_SLASHED = '%Y/%m/%d'
DATETIME_FORMAT_SLASHED = '%Y/%m/%d %H:%M:%S'

IPA_GOTHIC_FONT_PATH = './IPAexfont00401/ipaexg.ttf'

GRAPH_ROW_CNT = 4
GRAPH_COL_CNT = 3
GRAPH_CNT_IN_IMG = GRAPH_ROW_CNT * GRAPH_COL_CNT
IMG_SIZE = (24, 13.5)
GRAPH_SUPTITLE_FONT_SIZE = 24
GRAPH_TITLE_FONT_SIZE = 18

IMG_PATH = os.environ.get('IMG_PATH', './img')

TWITTER_API_CONFIG_FILE_PATH = './config.json'
TWITTER_MEDIA_CNT_PER_TWEET = 4

OCCTO_REQUEST_HOUR_TH = 16
OCCTO_CITATION = '電力広域的運営推進機関 ユニット別発電実績公開システム より 作成'
OCCTO_CITATION_FONT_SIZE = 24
