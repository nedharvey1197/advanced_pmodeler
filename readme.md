# Advanced Process Modeler

A comprehensive financial modeling and optimization tool for manufacturing expansion scenarios.

## Directory Structure

- `src/`: Source code
  - `models/`: Data models
  - `services/`: Business logic services
  - `utils/`: Utility functions
  - `web/`: Web applications (Streamlit)
- `config/`: Configuration files
- `data/`: Data files
  - `templates/`: Excel templates
  - `output/`: Generated files
- `docs/`: Documentation
- `tests/`: Test files
- `scripts/`: Scripts and tools
- `requirements/`: Python package requirements

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements/base.txt
   pip install -r requirements/spreadsheet.txt
   ```

2. Run the web application:
   ```bash
   streamlit run src/web/streamlit_app.py
   ```

## Development

1. Install all dependencies:
   ```bash
   pip install -r requirements/base.txt
   pip install -r requirements/spreadsheet.txt
   ```

2. Run tests:
   ```bash
   python -m pytest tests/
   ```
