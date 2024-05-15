# gen-by-unit

OCCTOの[ユニット別発電実績公開システム](https://hatsuden-kokai.occto.or.jp/hks-web-public/info/hks)から1日分のデータの取得を行い, TwitterへTweetする.

## 目次

- [概要](#概要)
- [インストール](#インストール)
- [使用方法](#使用方法)
- [ライセンス](#ライセンス)
- [作者](#作者)

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
