from enum import Enum

BASE_URL = 'https://hatsuden-kokai.occto.or.jp/hks-web-public'
DISCLAIMER_ENDPOINT = '/disclaimer-agree/next'
SEARCH_ENDPOINT = '/info/hks/search'
DOWNLOAD_ENDPOINT = '/info/hks/downloadCsv'
DATE_FORMAT_SLASHED = '%Y/%m/%d'
DATETIME_FORMAT_SLASHED = '%Y/%m/%d %H:%M:%S'

IPA_GOTHIC_FONT_PATH = './IPAexfont00401/ipaexg.ttf'
IPA_MINCHOU_FONT_PATH = './IPAexfont00401/ipaexm.ttf'

PLANTS_CSV_PATH = './plant_data/plants.csv'
UNITS_CSV_PATH = './plant_data/units.csv'

GRAPH_ROW_CNT = 4
GRAPH_COL_CNT = 6
GRAPH_CNT_IN_IMG = GRAPH_ROW_CNT * GRAPH_COL_CNT
IMG_SIZE = (24, 13.5)

IMG_PATH = './img'

class Area(Enum):
    HOKKAIDO = 1
    TOHOKU = 2
    TOKYO = 3
    CHUBU = 4
    HOKURIKU = 5
    KANSAI = 6
    CHUGOKU = 7
    SHIKOKU = 8
    KYUSHU = 9
    OKINAWA = 10

class UnitType(Enum):
    NUCLEAR = 1
    HYDRO = 2
    COAL = 3
    LNG = 4
    OIL = 5
    GEOTHERMAL = 6
    WIND = 7
    SOLAR = 8
    OTHER = 9
