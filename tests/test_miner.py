#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals
from os import path, walk

from pandas import read_csv

from .context import modules
from modules import miner

BASE_DIR = path.dirname(path.abspath(__file__))
TEST_OUTPUT = "test_output.csv"


def test_scrape():
    """Scrape features from valid pre-downloaded HTML files"""

    miner_obj = miner.Miner(
        sorted([filenames for (dirpath, dirnames, filenames)
                in walk("responses")][0]),
        TEST_OUTPUT, gui=True
    )

    miner_obj.scan_files()
    miner_obj.export()

    assert(path.isfile(TEST_OUTPUT))


def test_accuracy():
    """Verify the accuracy of the output"""

    original_df = read_csv(path.join(BASE_DIR, "origin_output.csv"))
    new_df = read_csv(path.join(BASE_DIR, TEST_OUTPUT))
    assert(original_df.equals(new_df))
