# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.


All the changes must be implemented on a ad-hoc branch. 
If the task was already initiate, the existing branch should be used.
Create an issue on github in order to define a new branch. 
The branch must be push on github.
A request to the user must be raised before the branch is merged on main.


## Project Overview

This is `python-codicefiscale`, a Python library for encoding/decoding Italian fiscal codes (Codice Fiscale). The library provides both a Python API and CLI interface for working with Italian tax codes.

## Development Commands

### Testing
```bash
# Run all tests with coverage (minimum 90% required)
pytest tests --cov=codicefiscale --cov-report=term-missing --cov-fail-under=90

# Run tests across multiple Python versions
tox

# Run single test file
pytest tests/test_encode.py
```

### Code Quality
```bash
# Run all linting and formatting checks
pre-commit run -a

# Type checking
mypy --install-types --non-interactive --strict

# Manual formatting (though pre-commit handles this)
black .
ruff check .
```

### Package Building
```bash
# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements.txt -r requirements-test.txt

# Setup pre-commit hooks
pre-commit install --install-hooks
```

### CLI Usage
```bash
# Encode fiscal code
python -m codicefiscale encode --firstname Fabio --lastname Caccamo --gender M --birthdate 03/04/1985 --birthplace Torino

# Decode fiscal code
python -m codicefiscale decode CCCFBA85D03L219P
```

## Architecture

### Core Module Structure
- `codicefiscale/codicefiscale.py`: Main encoding/decoding logic with algorithms for fiscal code calculation
- `codicefiscale/data.py`: Data management for municipalities and countries with auto-update capability 
- `codicefiscale/cli.py`: Command-line interface implementation
- `codicefiscale/__main__.py`: CLI entry point
- `codicefiscale/metadata.py`: Package metadata and version information

### Key Features
- **Omocodia support**: Handles alternative character encoding for duplicate cases
- **Auto-updated data**: Municipality and country data automatically updated weekly from ANPR
- **Flexible date parsing**: Multiple birthdate formats supported via python-dateutil
- **Transliteration**: Name/surname handling for non-ASCII characters
- **Comprehensive validation**: Full fiscal code structure and checksum validation

### Data Files
Located in `codicefiscale/data/`:
- `municipalities.json`: Italian municipality codes and names
- `countries.json`: Foreign country codes  
- `*-patch.json`: Manual corrections to auto-updated data
- `deleted-countries.json`: Historical country codes no longer valid

### Dependencies
- `python-dateutil`: Date parsing flexibility
- `python-fsutil`: File system utilities
- `python-slugify`: Text normalization

## Testing Strategy

Tests are organized by functionality:
- `test_encode.py`: Fiscal code generation tests
- `test_decode.py`: Fiscal code parsing tests  
- `test_cli.py`: Command-line interface tests
- `issues/`: Regression tests for specific GitHub issues

The project maintains 90% test coverage requirement and uses pytest with coverage reporting.