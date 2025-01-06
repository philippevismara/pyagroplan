# Pyagroplan

[![python-package](https://github.com/philippevismara/pyagroplan/actions/workflows/python-package.yml/badge.svg)](https://github.com/philippevismara/pyagroplan/actions)
[![code-style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Installation

The software has been tested for Python versions >= 3.10.
The dependecies can be installed using `pip`,
```script
pip install -r requirements.txt
```


## Unit tests

To run unit tests, from the root directory, execute:
```script
python -m pytest tests
```


## Documentation

To build the documentation, first make sure to have the dependencies installed:
```script
pip install -r docs/docs_requirements.txt
```

Then, execute:
```script
cd docs
make html
```

The documentation is then available at `docs/build/html/index.html`.
