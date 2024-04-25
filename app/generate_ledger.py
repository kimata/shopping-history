#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
購入履歴情報を Excel ファイルとして出力します．

Usage:
  generate_ledger.py [-c CONFIG] [-N]

Options:
  -c CONFIG    : CONFIG を設定ファイルとして読み込んで実行します．[default: config.yaml]
  -N            : サムネイル画像を含めないようにします．
"""

import copy
import logging
import openpyxl
import openpyxl.styles
import openpyxl.formatting.rule

import store_amazon.handle
import store_amazon.order_history

import store_yahoo.handle
import store_yahoo.order_history

import store_yodobashi.handle
import store_yodobashi.order_history

import store_monotaro.handle
import store_monotaro.order_history

import mercari.handle
import mercari.transaction_history

STATUS_ALL = "[generate] Excel file"
STATUS_INSERT_BOUGHT_ITEM = "[generate] Insert bought item"
STATUS_INSERT_SOLD_ITEM = "[generate] Insert sold item"

CRAWLER_DEF_LIST = [
    {
        "name": "Amazon",
        "handle_module": store_amazon.handle,
        "export_module": store_amazon.order_history,
    },
    {
        "name": "Yahoo",
        "handle_module": store_yahoo.handle,
        "export_module": store_yahoo.order_history,
    },
    {
        "name": "Yodobashi",
        "handle_module": store_yodobashi.handle,
        "export_module": store_yodobashi.order_history,
    },
    {
        "name": "Monotaro",
        "handle_module": store_monotaro.handle,
        "export_module": store_monotaro.order_history,
    },
    # NOTE: メルカリは購入だけでなく販売も含まれ，他と違うので末尾にする
    {
        "name": "Mercari",
        "handle_module": mercari.handle,
        "export_module": mercari.transaction_history,
    },
]


def get_excel_font(config):
    font_config = config["output"]["excel"]["font"]
    return openpyxl.styles.Font(name=font_config["name"], size=font_config["size"])


def get_bought_sheet_def():
    sheet_def = copy.deepcopy(CRAWLER_DEF_LIST[0]["export_module"].SHEET_DEF)
    sheet_def["SHEET_TITLE"] = "購入"

    # NOTE: 全てに共通の列のみ残して，他は削除
    col_set = None
    for crawler_def in CRAWLER_DEF_LIST:
        if "SHEET_TITLE" in crawler_def["export_module"].SHEET_DEF:
            col_list = crawler_def["export_module"].SHEET_DEF["TABLE_HEADER"]["col"].keys()
        else:
            col_list = crawler_def["export_module"].SHEET_DEF["BOUGHT"]["TABLE_HEADER"]["col"].keys()

        if col_set is None:
            col_set = set(col_list)
        else:
            col_set &= set(col_list)

    for col_key in list(sheet_def["TABLE_HEADER"]["col"].keys()):
        if col_key not in col_set:
            sheet_def["TABLE_HEADER"]["col"].pop(col_key)
            continue

        # NOTE: ここのファイルの処理では元データを補正するので，それに伴って不要になる定義は削除しておく
        for key in ["value", "formal_key"]:
            if key in sheet_def["TABLE_HEADER"]["col"][col_key]:
                sheet_def["TABLE_HEADER"]["col"][col_key].pop(key)

    # NOTE: メルカリの場合，価格が取れない場合が存在するので，価格はオプション扱いにする
    sheet_def["TABLE_HEADER"]["col"]["price"]["optional"] = True

    # NOTE: 削除した列を詰める
    col_pos_list = list(
        sorted(
            map(
                lambda col_key: [col_key, sheet_def["TABLE_HEADER"]["col"][col_key]["pos"]],
                sheet_def["TABLE_HEADER"]["col"].keys(),
            ),
            key=lambda x: x[1],
        )
    )
    pos = None
    for col_pos in col_pos_list:
        if pos is None:
            pos = col_pos[1] + 1
            continue

        col_pos[1] = pos
        if col_pos[0] == "category":
            pos += 3
        else:
            pos += 1

    for col_pos in col_pos_list:
        sheet_def["TABLE_HEADER"]["col"][col_pos[0]]["pos"] = col_pos[1]

    return sheet_def


def get_bought_item_list():
    all_item_list = []
    for crawler_def in CRAWLER_DEF_LIST:
        handle = crawler_def["handle_module"].create(config)

        if crawler_def["name"] == "Mercari":
            item_list = crawler_def["handle_module"].get_bought_item_list(handle)
        else:
            item_list = crawler_def["handle_module"].get_item_list(handle)

        for item in item_list:
            item["shop_name"] = crawler_def["export_module"].SHOP_NAME
            # FIXME: メルカリ用データの補正
            if "date" not in item:
                item["date"] = item["purchase_date"]
            if "no" not in item:
                item["no"] = item["id"]
            # FIXME: アマゾン用データの補正
            if "id" not in item:
                item["id"] = item["asin"]

        all_item_list += item_list

    return sorted(all_item_list, key=lambda x: x["date"])


def set_pattern_fill(sheet, sheet_def, row_last):
    shop_fill_list = [
        {"name": store_amazon.order_history.SHOP_NAME, "color": "FF9900"},
        {"name": store_monotaro.order_history.SHOP_NAME, "color": "D51B28"},
        {"name": store_yodobashi.order_history.SHOP_NAME, "color": "FC2828"},
        {"name": store_yahoo.order_history.SHOP_NAME, "color": "FF0033"},
        {"name": mercari.transaction_history.SHOP_NAME, "color": "E72121"},
    ]

    for shop_fill in shop_fill_list:
        rule = openpyxl.formatting.rule.FormulaRule(
            formula=[
                '${pos}="{name}"'.format(
                    pos=local_lib.openpyxl_util.gen_text_pos(
                        sheet_def["TABLE_HEADER"]["row"]["pos"] + 1,
                        sheet_def["TABLE_HEADER"]["col"]["shop_name"]["pos"],
                    ),
                    name=shop_fill["name"],
                )
            ],
            fill=openpyxl.styles.PatternFill(bgColor=shop_fill["color"], fill_type="solid"),
        )
        sheet.conditional_formatting.add(
            "{start}:{end}".format(
                start=local_lib.openpyxl_util.gen_text_pos(
                    sheet_def["TABLE_HEADER"]["row"]["pos"] + 1,
                    sheet_def["TABLE_HEADER"]["col"]["shop_name"]["pos"],
                ),
                end=local_lib.openpyxl_util.gen_text_pos(
                    row_last,
                    sheet_def["TABLE_HEADER"]["col"]["shop_name"]["pos"],
                ),
            ),
            rule,
        )


def get_thumb_path(handle_def_map, item):
    handle_def = handle_def_map[item["shop_name"]]

    return handle_def["module"].get_thumb_path(handle_def["handle"], item)


def generate_bought_sheet(handle, book, handle_def_map, is_need_thumb):
    sheet_def = get_bought_sheet_def()
    item_list = get_bought_item_list()

    CRAWLER_DEF_LIST[0]["handle_module"].set_progress_bar(handle, STATUS_INSERT_BOUGHT_ITEM, len(item_list))

    sheet = local_lib.openpyxl_util.generate_list_sheet(
        book,
        item_list,
        sheet_def,
        is_need_thumb,
        lambda item: get_thumb_path(handle_def_map, item),
        lambda status: None,
        lambda: None,
        lambda: CRAWLER_DEF_LIST[0]["handle_module"]
        .get_progress_bar(handle, STATUS_INSERT_BOUGHT_ITEM)
        .update(),
    )
    set_pattern_fill(sheet, sheet_def, sheet_def["TABLE_HEADER"]["row"]["pos"] + len(item_list))

    CRAWLER_DEF_LIST[0]["handle_module"].get_progress_bar(handle, STATUS_INSERT_BOUGHT_ITEM).update()


def get_sold_sheet_def():
    sheet_def = copy.deepcopy(mercari.transaction_history.SHEET_DEF["SOLD"])
    sheet_def["SHEET_TITLE"] = "販売"

    return sheet_def


def get_sold_item_list():
    item_list = mercari.handle.get_sold_item_list(mercari.handle.create(config))

    for item in item_list:
        item["shop_name"] = mercari.transaction_history.SHOP_NAME

    return item_list


def generate_sold_sheet(handle, book, handle_def_map, is_need_thumb):
    sheet_def = get_sold_sheet_def()
    item_list = get_sold_item_list()

    CRAWLER_DEF_LIST[0]["handle_module"].set_progress_bar(handle, STATUS_INSERT_SOLD_ITEM, len(item_list))

    sheet = local_lib.openpyxl_util.generate_list_sheet(
        book,
        item_list,
        sheet_def,
        is_need_thumb,
        lambda item: get_thumb_path(handle_def_map, item),
        lambda status: None,
        lambda: None,
        lambda: CRAWLER_DEF_LIST[0]["handle_module"]
        .get_progress_bar(handle, STATUS_INSERT_SOLD_ITEM)
        .update(),
    )
    set_pattern_fill(sheet, sheet_def, sheet_def["TABLE_HEADER"]["row"]["pos"] + len(item_list))

    CRAWLER_DEF_LIST[0]["handle_module"].get_progress_bar(handle, STATUS_INSERT_SOLD_ITEM).update()


def generate_table_excel(config, is_need_thumb):
    logging.info("Start to Generate excel file")

    handle_def_map = {}
    for crawler_def in CRAWLER_DEF_LIST:
        handle_def_map[crawler_def["export_module"].SHOP_NAME] = {
            "module": crawler_def["handle_module"],
            "handle": crawler_def["handle_module"].create(config),
        }

    excel_file = config["output"]["excel"]["table"]

    book = openpyxl.Workbook()
    book._named_styles["Normal"].font = get_excel_font(config)

    handle = handle_def_map[CRAWLER_DEF_LIST[0]["export_module"].SHOP_NAME]["handle"]

    generate_bought_sheet(handle, book, handle_def_map, is_need_thumb)
    generate_sold_sheet(handle, book, handle_def_map, is_need_thumb)

    book.remove(book.worksheets[0])

    book.save(excel_file)
    book.close()

    logging.info("Complete to Generate excel file")


######################################################################
if __name__ == "__main__":
    from docopt import docopt
    import traceback

    import local_lib.logger
    import local_lib.config

    args = docopt(__doc__)

    local_lib.logger.init("Shopping history", level=logging.INFO)

    config_file = args["-c"]
    is_need_thumb = not args["-N"]

    config = local_lib.config.load(args["-c"])

    try:
        generate_table_excel(config, is_need_thumb)
    except:
        logging.error(traceback.format_exc())
