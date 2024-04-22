#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
購入履歴情報を収集します．

Usage:
  generate_ledger.py [-c CONFIG]

Options:
  -c CONFIG    : CONFIG を設定ファイルとして読み込んで実行します．[default: config.yaml]
"""

import logging
import openpyxl

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
    {
        "name": "Mercari",
        "handle_module": mercari.handle,
        "export_module": mercari.transaction_history,
    },
]


def get_excel_font(config):
    font_config = config["output"]["excel"]["font"]
    return openpyxl.styles.Font(name=font_config["name"], size=font_config["size"])


def generate_sheet(book):
    for crawler_def in CRAWLER_DEF_LIST:
        handle = crawler_def["handle_module"].create(config)

        crawler_def["handle_module"].set_progress_bar(handle, crawler_def["export_module"].STATUS_ALL, 3)
        crawler_def["export_module"].generate_sheet(handle, book)

        crawler_def["handle_module"].finish(handle)


def generate_table_excel(config):
    logging.info("Start to Generate excel file")

    excel_file = config["output"]["excel"]["table"]

    book = openpyxl.Workbook()
    book._named_styles["Normal"].font = get_excel_font(config)

    generate_sheet(book)

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

    config = local_lib.config.load(args["-c"])

    try:
        generate_table_excel(config)
    except:
        logging.error(traceback.format_exc())
