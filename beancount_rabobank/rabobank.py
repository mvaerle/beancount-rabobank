import re
import csv
from os import path
import datetime

from beancount.ingest import importer
from beancount.core import data
from beancount.core import amount
from beancount.core.number import D

RABOBANK_FILE_PATTERNS = [
    r"CSV_A_(\d{4}\d{2}\d{2})_\d{6}\.csv"
]

RABOBANK_HEADER_PATTERNS = [
    r"\"IBAN/BBAN\",\"Munt\",\"BIC\",\"Volgnr\",\"Datum\",\"Rentedatum\",\"Bedrag\",\"Saldo na trn\",\"Tegenrekening IBAN/BBAN\",\"Naam tegenpartij\",\"Naam uiteindelijke partij\",",
    r"\"IBAN/BBAN\",\"Ccy\",\"BIC\",\"Seq No\",\"Date\",\"Value Date\",\"Amount\",\"Bal After Bkng\",\"Counterpty IBAN/BBAN\",\"Name Counterpty\",\"Name Ultimate Pty\",\"Name Initiating Pty\",\"Counterpty BIC\",\"Code\",\"Batch ID\",\"Transaction Reference\",\"Mandate Reference\",\"Collector ID\",\"Payment Reference\",\"Description-1\",\"Description-2\",\"Description-3\",\"Reasoncode\",\"Instr Amt\",\"Instr Ccy\",\"Rate\""
]


DATE_PATTERNS = ["Datum", "Date"]
COUNTERPARTY_PATTERNS = ["Naam tegenpartij", "Name Counterpty"]
AMOUNT_PATTERNS = ["Bedrag", "Amount"]
DESCRIPTION_1_PATTERNS = ["Omschrijving-1", "Description-1"]
DESCRIPTION_2_PATTERNS = ["Omschrijving-2", "Description-2"]
DESCRIPTION_3_PATTERNS = ["Omschrijving-3", "Description-3"]
BALANCE_PATTERNS = ["Saldo na trn", "Bal After Bkng"]


class Importer(importer.ImporterProtocol):
    def __init__(self, currency, account_root):
        self.currency = currency
        self.account_root = account_root

    def match_patterns(self, s, patterns):
        return [re.match(pattern, s) for pattern in patterns]

    def str_to_date(self, date, pattern=r"(\d{4})(\d{2})(\d{2})"):
        date_search = re.search(pattern, date)
        return datetime.date(
            year=int(date_search.group(1)),
            month=int(date_search.group(2)),
            day=int(date_search.group(3))
        )

    def str_to_amount(self, amt, is_withdrawal):
        amt_decimal = D(amt.replace(",", "."))
        amt_decimal_signed = -amt_decimal if is_withdrawal else amt_decimal

        return amount.Amount(amt_decimal_signed, self.currency)

    def transform_rabo_amount(self, amt):
        return self.str_to_amount(
            amt.replace("+", "").replace("-", ""),
            amt.startswith("-")
        )

    def name(self):
        return "Rabobank CSV"

    def identify(self, file):
        matches_files = self.match_patterns(
            path.basename(file.name), RABOBANK_FILE_PATTERNS)

        if not any(matches_files):
            return False

        matches_header = self.match_patterns(
            file.head(), RABOBANK_HEADER_PATTERNS)
        return any(matches_files) and any(matches_header)

    def file_name(self, file):
        return 'rabobank.{}'.format(path.basename(file.name))

    def file_account(self, _):
        return self.account_root

    def file_date(self, file):
        matches = self.match_patterns(
            path.basename(file.name), RABOBANK_FILE_PATTERNS)
        date_str = next((x for x in matches if x)).group(1)
        return self.str_to_date(date_str)

    def transaction_entry(self, date, counterparty_name, desc, account, amt):
        postings = [data.Posting(
            account, amt, None, None, None, None), ]

        return data.Transaction(  # pylint: disable=not-callable
            self.meta,
            date,
            self.FLAG,
            counterparty_name,
            desc,
            data.EMPTY_SET,
            data.EMPTY_SET,
            postings)

    def balance_entry(self):
        return data.Balance(  # pylint: disable=not-callable
            self.meta,
            self.prev_date + datetime.timedelta(days=1),
            self.prev_account,
            self.prev_balance,
            None,
            None)

    def get_row_value(self, row, pattern):
        result = None
        for key in pattern:
            result = row.get(key)
            if result:
                break

        return result

    def extract(self, file, existing_entries=None):
        entries = []
        index = 0
        self.prev_account = None
        self.prev_date = None
        self.prev_balance = None

        for index, row in enumerate(csv.DictReader(open(file.name, mode="r", encoding="latin-1"))):
            self.meta = data.new_metadata(file.name, index)

            date = self.str_to_date(
                self.get_row_value(row, DATE_PATTERNS),
                r"(\d{4})-(\d{2})-(\d{2})")
            counterparty_name = self.get_row_value(row, COUNTERPARTY_PATTERNS)
            amount = self.transform_rabo_amount(
                self.get_row_value(row, AMOUNT_PATTERNS))

            desc_patterns = [DESCRIPTION_1_PATTERNS,
                             DESCRIPTION_2_PATTERNS, DESCRIPTION_3_PATTERNS]

            desc = ""
            for patterns in desc_patterns:
                desc += self.get_row_value(row, patterns) or ""
            desc = desc.strip()

            account = self.account_root
            balance = self.transform_rabo_amount(
                self.get_row_value(row, BALANCE_PATTERNS))

            # if the account changes make a balance assertion
            if self.prev_account != account and self.prev_account != None:
                entries.append(self.balance_entry())

            entries.append(
                self.transaction_entry(date, counterparty_name, desc, account, amount))

            self.prev_account = account
            self.prev_date = date
            self.prev_balance = balance

        # make balance assertion for the last row
        entries.append(self.balance_entry())

        return entries
