import lib, const

# 発電所情報を結合したjoin.csvを作成する
if __name__ == '__main__':
    units = lib.get_units()
    with open(const.JOINED_CSV_PATH, 'w') as f:
        print('エリア',
              'グループ名',
              '発電所名',
              'ユニット名',
              '発電方式',
              '凡例のユニット名',
              '認可出力(万kW)',
            sep=',', file=f)
        for unit in units:
            print(unit.group.area.name,
                unit.group.name,
                unit.plant_key_name,
                unit.unit_key_name,
                unit.type_.name,
                unit.name,
                unit.power,
                sep=',', file=f)
