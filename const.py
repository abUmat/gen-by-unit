from enum import Enum

BASE_URL = 'https://hatsuden-kokai.occto.or.jp/hks-web-public'
DISCLAIMER_ENDPOINT = '/disclaimer-agree/next'
SEARCH_ENDPOINT = '/info/hks/search'
DOWNLOAD_ENDPOINT = '/info/hks/downloadCsv'
DATE_FORMAT_SLASHED = '%Y/%m/%d'
DATETIME_FORMAT_SLASHED = '%Y/%m/%d %H:%M:%S'

IPA_GOTHIC_FONT_PATH = './IPAexfont00401/ipaexg.ttf'
IPA_MINCHOU_FONT_PATH = './IPAexfont00401/ipaexm.ttf'

GROUPS_CSV_PATH = './plant_data/groups.csv'
PLANTS_CSV_PATH = './plant_data/plants.csv'
UNITS_CSV_PATH = './plant_data/units.csv'

GRAPH_ROW_CNT = 4
GRAPH_COL_CNT = 4
GRAPH_CNT_IN_IMG = GRAPH_ROW_CNT * GRAPH_COL_CNT
IMG_SIZE = (24, 13.5)

SUBPLOT_LEGENDS_ROW_CNT = 12

IMG_PATH = './img'

TWITTER_API_CONFIG_FILE_PATH = './config.json'
TWITTER_MEDIA_CNT_PER_TWEET = 4

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
    def area_name(self):
        match self:
            case self.HOKKAIDO:
                return '北海道エリア'
            case self.TOHOKU:
                return '東北エリア'
            case self.TOKYO:
                return '東京エリア'
            case self.CHUBU:
                return '中部エリア'
            case self.HOKURIKU:
                return '北陸エリア'
            case self.KANSAI:
                return '関西エリア'
            case self.CHUGOKU:
                return '中国エリア'
            case self.SHIKOKU:
                return '四国エリア'
            case self.KYUSHU:
                return '九州エリア'
            case self.OKINAWA:
                return '沖縄エリア'

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
