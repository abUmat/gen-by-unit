from enum import Enum
from datetime import timezone, timedelta

JST = timezone(timedelta(hours=+9), 'JST')

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
JOINED_CSV_PATH = './plant_data/joined.csv'

GRAPH_ROW_CNT = 4
GRAPH_COL_CNT = 3
GRAPH_CNT_IN_IMG = GRAPH_ROW_CNT * GRAPH_COL_CNT
IMG_SIZE = (24, 13.5)
GRAPH_SUPTITLE_FONT_SIZE = 24
GRAPH_TITLE_FONT_SIZE = 18

IMG_PATH = './img'

TWITTER_API_CONFIG_FILE_PATH = './config.json'
TWITTER_MEDIA_CNT_PER_TWEET = 4

OCCTO_REQUEST_HOUR_TH = 16
OCCTO_CITATION = '電力広域的運営推進機関 ユニット別発電実績公開システム より 作成'
OCCTO_CITATION_FONT_SIZE = 24

class GraphColors(Enum):
    NUCLEAR_COLORS = ('#708090',
                      '#696969',
                      '#808080',
                      '#A9A9A9',
                      '#C0C0C0',
                      '#D3D3D3',
                      '#DCDCDC')

    HYDRO_COLORS = ('#0000FF',
                    '#ADD8E6',
                    '#00FFFF',
                    '#5F9EA0',
                    '#AFEEEE',
                    '#4682B4')

    COAL_COLORS = ('#4B3621',
                   '#8B4513',
                   '#A0522D',
                   '#D2B48C',
                   '#8B7355')

    LNG_COLORS = ('#FF0000',
                  '#FFA500',
                  '#FF69B4',
                  '#FF4500',
                  '#CD5C5C',
                  '#DAA520',
                  '#FF8C00',
                  '#FFA07A')

    OIL_COLORS = ('#32CD32',
                  '#9ACD32',
                  '#7FFF00')

    OTHER_COLORS = ('#000000',
                    '#757575')

class Area(Enum):
    '''
    グループが連系されている系統エリア
    '''
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
    def to_str(self):
        match self:
            case Area.HOKKAIDO:
                return '北海道エリア'
            case Area.TOHOKU:
                return '東北エリア'
            case Area.TOKYO:
                return '東京エリア'
            case Area.CHUBU:
                return '中部エリア'
            case Area.HOKURIKU:
                return '北陸エリア'
            case Area.KANSAI:
                return '関西エリア'
            case Area.CHUGOKU:
                return '中国エリア'
            case Area.SHIKOKU:
                return '四国エリア'
            case Area.KYUSHU:
                return '九州エリア'
            case Area.OKINAWA:
                return '沖縄エリア'

class FuelType(Enum):
    '''
    発電所の燃料またはエネルギー源
    '''
    NUCLEAR = 1
    '原子力'
    HYDRO = 2
    '水力'
    COAL = 3
    '石炭'
    LNG = 4
    'LNG'
    OIL = 5
    '石油'
    GEOTHERMAL = 6
    '地熱'
    WIND = 7
    '風力'
    SOLAR = 8
    '太陽光太陽熱'
    OTHER = 9
    'その他(不明含む)'
    BIOMASS = 10
    'バイオマス'
    def colors(self) -> GraphColors:
        match self:
            case FuelType.NUCLEAR:
                return GraphColors.NUCLEAR_COLORS
            case FuelType.HYDRO:
                return GraphColors.HYDRO_COLORS
            case FuelType.COAL:
                return GraphColors.COAL_COLORS
            case FuelType.LNG:
                return GraphColors.LNG_COLORS
            case FuelType.OIL:
                return GraphColors.OIL_COLORS
            case FuelType.GEOTHERMAL | FuelType.WIND | FuelType.SOLAR | FuelType.OTHER | FuelType.BIOMASS:
                return GraphColors.OTHER_COLORS

class UnitType(Enum):
    '''
    発電所の発電方式
    '''
    NUCLEAR = 10
    '原子力'
    HYDRO = 20
    '一般水力'
    PUMPED = 21
    '純揚水'
    HYBRID_PUMPED = 22
    '混合揚水'
    COAL = 30
    '石炭(その他)'
    SUB_C = 31
    '亜臨界圧(Sub-Critical)'
    SC = 32
    '超臨界圧(Super Critical)'
    USC = 33
    '超々臨界圧(Ultra Super Critical)'
    LNG = 40
    'LNG汽力'
    CC = 41
    'コンバインドサイクル(Combined Cycle)'
    ACC = 42
    'Advanced Combined Cycle'
    MACC = 43
    'More Advanced Combined Cycle'
    MACC2 = 44
    'More Advanced Combined Cycle 2'
    OIL = 50
    '石油汽力'
    GEOTHERMAL = 60
    '地熱'
    WIND = 70
    '風力'
    SOLAR = 80
    '太陽光太陽熱'
    OTHER = 90
    'その他(不明含む)'
    BIOMASS = 91
    'バイオマス'

    def fuel(self) -> FuelType:
        '''
        発電方式から燃料を推測して返す
        '''
        match self:
            case UnitType.NUCLEAR:
                return FuelType.NUCLEAR
            case UnitType.HYDRO | UnitType.PUMPED | UnitType.HYBRID_PUMPED:
                return FuelType.HYDRO
            case UnitType.COAL | UnitType.SUB_C | UnitType.SC | UnitType.USC:
                return FuelType.COAL
            case UnitType.LNG | UnitType.CC | UnitType.ACC | UnitType.MACC | UnitType.MACC2:
                return FuelType.LNG
            case UnitType.OIL:
                return FuelType.OIL
            case UnitType.GEOTHERMAL:
                return FuelType.GEOTHERMAL
            case UnitType.WIND:
                return FuelType.WIND
            case UnitType.SOLAR:
                return FuelType.SOLAR
            case UnitType.OTHER:
                return FuelType.OTHER
            case UnitType.BIOMASS:
                return FuelType.BIOMASS

    def to_str(self) -> str:
        '''
        文字列に変換する
        '''
        match self:
            case UnitType.NUCLEAR:
                return '原子力'
            case UnitType.HYDRO:
                return '一般水力'
            case UnitType.PUMPED:
                return '純揚水'
            case UnitType.HYBRID_PUMPED:
                return '混合揚水'
            case UnitType.COAL:
                return '石炭'
            case UnitType.SUB_C:
                return 'SUB-C'
            case UnitType.SC:
                return 'SC'
            case UnitType.USC:
                return 'USC'
            case UnitType.LNG:
                return 'LNG汽力'
            case UnitType.CC:
                return 'CC'
            case UnitType.ACC:
                return 'ACC'
            case UnitType.MACC:
                return 'MACC'
            case UnitType.MACC2:
                return 'MACCⅡ'
            case UnitType.OIL:
                return '石油汽力'
            case UnitType.GEOTHERMAL:
                return '地熱'
            case UnitType.WIND:
                return '風力'
            case UnitType.SOLAR:
                return '太陽光'
            case UnitType.OTHER:
                return 'その他'
            case UnitType.BIOMASS:
                return 'バイオマス'
