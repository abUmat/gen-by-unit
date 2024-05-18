# gen-by-unit

OCCTOの[ユニット別発電実績公開システム](https://hatsuden-kokai.occto.or.jp/hks-web-public/info/hks)から1日分のデータの取得を行い, TwitterへTweetする.

## 目次

- [概要](#概要)
- [インストール](#インストール)
- [使用方法](#使用方法)
- [ライセンス](#ライセンス)
- [作者](#作者)
- [参考](#参考)

## 概要

1. OCCTOの[ユニット別発電実績公開システム](https://hatsuden-kokai.occto.or.jp/hks-web-public/info/hks)から1日分のデータの取得を行う.
1. 発電所データは JEPXの[発電情報公開システム_ユニット一覧](https://hjks.jepx.or.jp/hjks/unit)から取得しており, `./plant-data/plants.csv`, ユニットのデータは `./plant-data/units.csv` に保存されている. それを参照して集計を行う.
1. matplotlibを用いて認可出力と発電実績をグラフにして, 複数グラフを1枚の画像にまとめる.
1. `./config.json` に保存したTwitterAPIの認証情報を取得して, Tweetを行う.

## インストール

```bash
# リポジトリをクローンする
git clone https://github.com/abUmat/gen-by-unit.git

# プロジェクトディレクトリに移動する
cd gen-by-unit
```

## 使用方法

TwitterAPIの登録を行い, 認証情報を `./config.json` に保存する. `pip` コマンドなどを用いてライブラリをインストールした後に, `python main.py` などで実行する.

## ライセンス

このプロダクト自体のライセンスは保有しないが, IPAフォントやOCCTOのデータなどについてはそれに従うものとする.

## 作者

[Twitterリンク](https://twitter.com/PjAUaLTfE)

## 参考

### 石炭火力発電所の発電方式について

- [資源エネルギー庁_石炭火力発電所一覧_(2020-07-13)](https://www.meti.go.jp/shingikai/enecho/denryoku_gas/denryoku_gas/pdf/026_s01_00.pdf)
- [特定非営利活動法人気候ネットワーク_―提言レポート―石炭火力2030フェーズアウトの道筋](https://www.kikonet.org/wp/wp-content/uploads/2019/03/Report_Japan-Coal-phase-Out_JP.pdf)(2024-05-18時点)

### LNG火力発電所の発電方式について

各社HP等ののGTや燃焼温度、LHV基準発電効率から推測

### 水力発電所の発電方式について

- [北海道電力_主な水力発電所](https://www.hepco.co.jp/energy/water_power/hydroelectric_ps.html)(2024-05-18時点)
- [水力ドットコム_日本の水力発電所](http://www.suiryoku.com/)(2024-05-18時点)
