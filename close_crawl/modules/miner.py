#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Miner


TODO:
    Finish docs
    Refactor to lower complexity

"""

from __future__ import absolute_import, print_function, unicode_literals
from csv import DictWriter
from json import dump, dumps, load
from os import path

from bs4 import BeautifulSoup
from tqdm import trange

from .patterns import MONEY_PAT, TITLE_SPLIT_PAT, ZIP_PAT, filter_addr
from .settings import HTML_FILE, NO_CASE
from .settings import FEATURES, FIELDS, INTERNAL_FIELDS


class Miner(object):

    def __init__(self, responses, output, debug=False):

        self.responses = responses
        self.output = output
        self.debug = debug
        self.dataset = []
        self.maybe_tax = False
        self.features = [i + ':' for i in FEATURES]

    def scan_files(self):

        case_range = trange(len(self.responses), desc="Mining", leave=True) \
            if not self.debug else range(len(self.responses))

        for file_name in case_range:
            with open(
                HTML_FILE.format(case=self.responses[file_name]), 'r'
            ) as html_src:

                if not self.debug:
                    case_range.set_description(
                        "Mining {}".format(self.responses[file_name])
                    )

                feature_list = self.scrape(html_src.read())
                row = self.distribute(feature_list)

                if not row:

                    if not path.isfile(NO_CASE):
                        with open(NO_CASE, 'w') as no_case_file:
                            dump([], no_case_file)

                    with open(NO_CASE, "r+") as no_case_file:
                        no_case_data = load(no_case_file)
                        no_case_data.append(str(self.responses[file_name][:-5]))
                        no_case_file.seek(0)
                        no_case_file.write(dumps(sorted(set(no_case_data))))
                        no_case_file.truncate()

                self.dataset.extend(row)

    def export(self):

        file_exists = path.isfile(self.output)

        with open(self.output, 'a') as csv_file:
            writer = DictWriter(
                csv_file,
                fieldnames=[
                    col for col in FIELDS if col not in INTERNAL_FIELDS
                ]
            )

            if not file_exists:
                writer.writeheader()

            for row in self.dataset:
                writer.writerow(row)

    def scrape(self, html_data):
        """Scrapes the desired features

        Args:
            html_data: <str>, source HTML

        Returns:
            scraped_features: <dict>, features scraped and mapped from content
        """

        soup = BeautifulSoup(html_data, "html.parser")

        if "tax" in soup.text.lower():
            self.maybe_tax = True

        tr_list = soup.find_all("tr")

        feature_list = []
        for tag in tr_list:
            try:
                tag = [j.string for j in tag.findAll("span")]
                if set(tuple(tag)) & set(self.features):
                    try:
                        tag = [i for i in tag if "(each" not in i.lower()]
                    except AttributeError:
                        continue
                    feature_list.append(tag)

            except IndexError:
                continue

        try:
            # flatten multidimensional list
            feature_list = [
                item.replace(':', '')
                for sublist in feature_list for item in sublist
            ]

        except AttributeError:
            pass

        return feature_list

    def distribute(self, feature_list):

        def __pair(list_type):

            def __raw_business(i):
                return any(
                    x in feature_list[i:i + 2][0] for x in INTERNAL_FIELDS
                )

            def __feature_list(i):
                return feature_list[i:i + 2][0] in FEATURES

            condition = __raw_business if list_type else __feature_list

            return [
                tuple(feature_list[i:i + 2])
                for i in range(0, len(feature_list), 2)
                if condition(i)
            ]

        # break up elements with n-tuples greater than 2
        # then convert list of tuples to dict for faster lookup
        raw_business = __pair(1)
        feature_list = dict(__pair(0))

        filtered_business = []

        for label, value in enumerate(raw_business):
            try:
                # if "Party Type" == "Property Address" and
                # section == "Business or Organization Name"
                if value[1].upper() == "PROPERTY ADDRESS" and \
                        raw_business[label + 1][0].upper() == \
                        "BUSINESS OR ORGANIZATION NAME":
                    filtered_business.append(raw_business[label + 1])

            except IndexError:
                print("Party Type issue at Case", feature_list["Case Number"])

        scraped_features = []

        for address in filtered_business:

            str_address = filter_addr(str(address[-1]))

            temp_features = {
                key: value for key, value in feature_list.items()
                if key in ["Title",
                           "Case Type",
                           "Case Number",
                           "Filing Date"]
            }

            if temp_features["Case Type"].upper() == "FORECLOSURE":
                temp_features["Case Type"] = "Mortgage"

            elif temp_features["Case Type"].upper() == \
                    "FORECLOSURE RIGHTS OF REDEMPTION" and self.maybe_tax:
                temp_features["Case Type"] = "Tax"

            else:
                # break out of the rest of the loop if case type is neither
                continue

            # break up Title feature into Plaintiff and Defendant
            try:
                temp_features["Plaintiff"], temp_features["Defendant"] = \
                    TITLE_SPLIT_PAT.split(temp_features["Title"])

            except ValueError:
                temp_features["Plaintiff"], temp_features["Defendant"] = \
                    (", ")

            temp_features["Address"] = \
                str_address if str_address else address[-1]

            temp_features["Zip Code"] = ''.join(ZIP_PAT.findall(address[-1]))

            temp_features["Partial Cost"] = ''.join(
                MONEY_PAT.findall(address[-1])
            )

            scraped_features.append(temp_features)
            temp_features = {}

        return scraped_features
