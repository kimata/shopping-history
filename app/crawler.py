#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
購入履歴情報を収集します．

Usage:
  crawler.py [-c CONFIG]

Options:
  -c CONFIG    : CONFIG を設定ファイルとして読み込んで実行します．[default: config.yaml]
"""

import logging

import store_amazon.handle
import store_amazon.crawler

import store_yahoo.handle
import store_yahoo.crawler

import store_yodobashi.handle
import store_yodobashi.crawler

import store_monotaro.handle
import store_monotaro.crawler

import mercari.handle
import mercari.crawler

import local_lib.notify_slack


CRAWLER_DEF_LIST = [
    {"name": "Amazon", "handle_module": store_amazon.handle, "crawler_module": store_amazon.crawler},
    {"name": "Yahoo", "handle_module": store_yahoo.handle, "crawler_module": store_yahoo.crawler},
    {"name": "Yodobashi", "handle_module": store_yodobashi.handle, "crawler_module": store_yodobashi.crawler},
    {"name": "Monotaro", "handle_module": store_monotaro.handle, "crawler_module": store_monotaro.crawler},
    {"name": "Mercari", "handle_module": mercari.handle, "crawler_module": mercari.crawler},
]


def execute(config, is_export_mode=False):
    for crawler_def in CRAWLER_DEF_LIST:
        try:
            logging.info("{name} の購買履歴の収集を開始します．".format(name=crawler_def["name"]))
            handle = crawler_def["handle_module"].create(config)

            crawler_def["crawler_module"].fetch_order_item_list(handle)

            crawler_def["handle_module"].finish(handle)

            logging.info("{name} の購買履歴の収集を完了しました．".format(name=crawler_def["name"]))
        except:
            logging.warning("{name} の購買履歴の収集中にエラーが発生しました．".format(name=crawler_def["name"]))

            local_lib.notify_slack.error(
                config["slack"]["bot_token"],
                config["slack"]["error"]["channel"]["name"],
                "購買履歴取得エラー: {name}".format(name=name),
                traceback.format_exc(),
            )

    logging.info("全ての情報収集が完了しました．")


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
        execute(config)
    except:
        logging.error(traceback.format_exc())
