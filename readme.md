# Manufacturing Expansion Financial Model

A comprehensive financial modeling tool for manufacturing expansion planning. This application helps analyze and optimize manufacturing capacity, equipment utilization, and financial projections for expansion scenarios.

## Features

- Equipment capacity planning and utilization analysis
- Product cost modeling with detailed cost drivers
- Financial projections including income statement, balance sheet, and cash flow
- Scenario comparison and optimization
- Interactive web interface using Streamlit

## Project Structure

```
manufacturing_model/
├── models/                 # SQLAlchemy data models
│   ├── __init__.py
│   ├── base_model.py      # Base configuration and session management
│   ├── equipment_models.py # Equipment and capacity models
│   ├── product_models.py  # Product and cost driver models
│   └── financial_projections_model.py
├── services/              # Business logic services
│   ├── __init__.py
│   ├── financial_service.py
│   ├── equipment_service.py
│   └── scenario_service.py
├── utils/                 # Helper functions
│   ├── __init__.py
│   ├── db_utils.py
│   ├── financial_utils.py
│   └── visualization_utils.py
├── data/                  # Data storage
│   └── manufacturing_model.db
└── streamlit_app.py      # Web application entry point
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd manufacturing_model
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Database Setup

The application uses SQLite as its database. To initialize the database:

```python
from models import create_tables
create_tables()
```

## Running the Application

1. Start the Streamlit web interface:
```bash
streamlit run streamlit_app.py
```

2. Open your browser and navigate to `http://localhost:8501`

## Development

- Code formatting: `black .`
- Linting: `flake8`
- Running tests: `pytest`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
