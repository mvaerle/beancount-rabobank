# Beancount Rabobank CSV Importer

`beancount-rabobank` provides an importer for converting CSV exports of
[Rabobank] (Netherlands) account summaries to the [Beancount] format.

## Installation

```sh
$ pip install beancount-rabobank
```

## Usage

If you're not familiar with how to import external data into Beancount, please
read [this guide] first.

Adjust your [config file] to include the provided `rabobank.Importer` class.
A sample configuration might look like the following:

```python
from beancount_rabobank import rabobank

CONFIG = [
    # ...
    rabobank.Importer("EUR", "Assets:Liquid:Rabobank:Checkings")
    # ...
]
```

Once this is in place, you should be able to run `bean-extract` on the command
line to extract the transactions and pipe all of them into your Beancount file.
It should also work in fava using the same configuration.

```sh
$ bean-extract /path/to/config.py transaction.csv >> you.beancount
```

This importer works with [smart-importer] which will auto suggest postings based
on machine learning, which is lovely. In this case a config can look like this:

```python
from smart_importer import apply_hooks, PredictPostings
from beancount_rabobank import rabobank

CONFIG = [
    # ...
    apply_hooks(rabobank.Importer(
        "EUR", "Assets:Liquid:Rabobank:Checkings"), [PredictPostings()])
    # ...
]
```

## Contributing

Contributions are most welcome!

Please make sure you have Python 3.9+ and [Poetry] installed.

1. Clone the repository
2. If you want to develop using VSCode run the following command: `poetry config virtualenvs.in-project true`
3. Install the packages required for development: `poetry install`
4. That's basically it. You should now be able to run the test suite: `poetry run py.test`.

[beancount]: http://furius.ca/beancount/
[config file]: https://beancount.github.io/docs/importing_external_data.html#configuration
[rabobank]: https://www.rabobank.nl/
[poetry]: https://python-poetry.org/
[this guide]: https://beancount.github.io/docs/importing_external_data.html
[smart-importer]: https://github.com/beancount/smart_importer
