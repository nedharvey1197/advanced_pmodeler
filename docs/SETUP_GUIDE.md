# Advanced Process Modeler - Setup Guide

## Local Development Setup (Original Developer)

### Prerequisites
- Python 3.8 or higher
- Git
- Virtual environment tool (venv)
- Excel (for template development)
- Node.js (for some Streamlit components)

### Initial Setup
1. **Create Virtual Environment**:
   ```bash
   # Navigate to your project directory
   cd /path/to/advanced_pmodeler
   
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Mac/Linux:
   source venv/bin/activate
   # On Windows:
   .\venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   # Install all requirements (recommended for development)
   pip install -r requirements/dev.txt
   pip install -r requirements/web.txt
   pip install -r requirements/visualization.txt
   pip install -r requirements/optimization.txt
   
   # Or install specific components:
   pip install -r requirements/base.txt        # Core functionality only
   pip install -r requirements/web.txt         # Web interface
   pip install -r requirements/visualization.txt  # Visualization features
   pip install -r requirements/optimization.txt   # Advanced optimization
   ```

3. **Set Up Database**:
   ```bash
   # Initialize the database
   python src/utils/db_init.py
   ```

4. **Run Tests**:
   ```bash
   # Run all tests
   python -m pytest tests/
   
   # Run with coverage report
   python -m pytest --cov=src tests/
   
   # Run specific test file
   python -m pytest tests/test_financial_service.py
   ```

### Development Workflow
1. **Create New Feature Branch**:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Run Test Server**:
   ```bash
   # Start Streamlit app with hot reloading
   streamlit run src/web/streamlit_app.py --server.runOnSave=true
   ```

3. **Generate Test Data**:
   ```bash
   # Create test workbook
   python tests/data/comprehensive_test_scenario.py
   ```

4. **Code Quality**:
   ```bash
   # Run linting
   flake8 src tests
   black src tests
   isort src tests
   
   # Run type checking
   mypy src
   
   # Run security checks
   bandit -r src
   ```

## Remote Setup (New Developer)

### Prerequisites
- Python 3.8 or higher
- Git
- Virtual environment tool (venv)
- GitHub account
- Excel
- Node.js (for some Streamlit components)

### Initial Setup
1. **Clone Repository**:
   ```bash
   # Clone the repository
   git clone https://github.com/username/advanced_pmodeler.git
   cd advanced_pmodeler
   
   # Switch to development branch
   git checkout develop
   ```

2. **Create Virtual Environment**:
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Mac/Linux:
   source venv/bin/activate
   # On Windows:
   .\venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   # Install all requirements
   pip install -r requirements/dev.txt
   pip install -r requirements/web.txt
   pip install -r requirements/visualization.txt
   pip install -r requirements/optimization.txt
   ```

4. **Initialize Database**:
   ```bash
   # Create and initialize database
   python src/utils/db_init.py
   ```

5. **Run Tests**:
   ```bash
   # Run all tests with coverage
   python -m pytest --cov=src tests/
   ```

### Development Workflow
1. **Update Repository**:
   ```bash
   git checkout develop
   git pull origin develop
   ```

2. **Create Feature Branch**:
   ```bash
   git checkout -b feat/your-feature-name
   ```

3. **Run Application**:
   ```bash
   # Start Streamlit app with debug mode
   streamlit run src/web/streamlit_app.py --server.runOnSave=true --logger.level=debug
   ```

## Common Tasks

### Working with Templates
1. **Generate Test Template**:
   ```bash
   python tests/data/comprehensive_test_scenario.py
   ```

2. **Run Template Tests**:
   ```bash
   python -m pytest tests/test_template_service.py
   ```

### Database Management
1. **Reset Database**:
   ```bash
   python src/utils/db_reset.py
   ```

2. **Create Test Data**:
   ```bash
   python src/utils/create_test_data.py
   ```

### Running Analysis
1. **From Command Line**:
   ```bash
   python scripts/run_analysis.py --template path/to/template.xlsx
   ```

2. **From Excel**:
   - Open template from `data/templates/`
   - Fill in data
   - Click "Generate Analysis" button

3. **From Web Interface**:
   ```bash
   # Start web interface
   streamlit run src/web/streamlit_app.py
   ```

## Troubleshooting

### Common Issues
1. **Import Errors**:
   - Verify virtual environment is activated
   - Check all requirements are installed
   - Verify Python path includes project root
   - Try reinstalling requirements: `pip install -r requirements/dev.txt --force-reinstall`

2. **Database Errors**:
   - Check database file exists
   - Verify permissions
   - Try resetting database
   - Check SQLAlchemy connection string

3. **Excel Integration**:
   - Verify openpyxl is installed
   - Check Excel file is not open
   - Verify template format
   - Try with different Excel versions

4. **Streamlit Issues**:
   - Check Node.js is installed
   - Clear browser cache
   - Try different browser
   - Check port availability

### Getting Help
1. **Documentation**:
   - Check `docs/` directory
   - Review inline code documentation
   - Check test cases for examples
   - Read function docstrings

2. **Support**:
   - Create GitHub issue
   - Check existing issues
   - Review pull requests
   - Check error logs

## Best Practices
1. **Code Quality**:
   - Run tests before committing
   - Follow PEP 8 style guide
   - Add docstrings to functions
   - Update tests for new features
   - Run linting and type checks

2. **Git Workflow**:
   - Keep commits focused
   - Write clear commit messages
   - Pull before pushing
   - Create pull requests for review
   - Use conventional commit format

3. **Testing**:
   - Write tests for new features
   - Maintain test coverage
   - Use test fixtures
   - Test edge cases
   - Add performance tests

4. **Documentation**:
   - Update docs with changes
   - Add code examples
   - Document breaking changes
   - Keep README updated
   - Add inline comments 