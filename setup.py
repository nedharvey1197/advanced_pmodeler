from setuptools import setup, find_packages

setup(
    name="advanced_pmodeler",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Core dependencies
        "SQLAlchemy>=2.0.0",
        "alembic>=1.12.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "python-dateutil>=2.8.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0.0",
        "tqdm>=4.65.0",
        "requests>=2.31.0",
        "urllib3>=2.0.0",
        
        # Web application
        "streamlit>=1.10.0",
        
        # Development tools
        "black>=22.3.0",
        "flake8>=4.0.0",
        "pytest>=7.0.0",
        "pytest-cov>=3.0.0",
        
        # Optional dependencies
        "openpyxl>=3.0.0",
        "xlrd>=2.0.0",
        
        # Error Handling & Logging
        "loguru>=0.7.0",
    ],
    extras_require={
        "web": [
            "streamlit-extras>=0.3.0",
            "st-pages>=0.4.0",
            "streamlit-option-menu>=0.3.0",
            "streamlit-aggrid>=0.3.0",
            "streamlit-authenticator>=0.2.0",
            "extra-streamlit-components>=0.1.56",
            "hydralit>=1.0.14",
            "hydralit-components>=1.0.10",
        ],
        "visualization": [
            "matplotlib>=3.7.0",
            "seaborn>=0.12.0",
            "plotly>=5.18.0",
            "bokeh>=3.3.0",
            "altair>=5.2.0",
            "holoviews>=1.17.0",
            "hvplot>=0.9.0",
            "panel>=1.3.0",
            "pyvista>=0.42.0",
            "vtk>=9.2.0",
            "folium>=0.14.0",
            "geopandas>=0.13.0",
            "shapely>=2.0.0",
        ],
        "optimization": [
            "pulp>=2.7.0",
            "cvxopt>=1.3.0",
            "pyomo>=6.6.0",
            "scikit-opt>=0.6.0",
            "scikit-learn>=1.3.0",
            "tensorflow>=2.13.0",
            "keras>=2.13.0",
            "torch>=2.1.0",
            "optuna>=3.3.0",
            "statsmodels>=0.14.0",
            "sympy>=1.12.0",
            "dask>=2023.0.0",
            "distributed>=2023.0.0",
            "joblib>=1.3.0",
            "ray>=2.6.0",
        ],
    },
    python_requires=">=3.8",
    author="Your Name",
    author_email="your.email@example.com",
    description="Advanced Process Modeler with Optimization Support",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/advanced_pmodeler",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
) 