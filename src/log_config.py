import logging

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ハンドラの設定
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
