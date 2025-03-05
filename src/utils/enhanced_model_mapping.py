"""
Enhanced model mapping utility for comprehensive analysis of models, services, and their relationships.

This module provides tools for:
1. Schema relationship analysis
2. Model dependency tracking
3. Service dependency mapping
4. Database table relationship mapping
5. Import pattern analysis
6. Circular dependency detection
"""

import os
import ast
import logging
import networkx as nx
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from sqlalchemy import inspect, MetaData
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.relationships import RelationshipProperty

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelRelationshipMapper:
    """
    Enhanced mapper for analyzing and tracking relationships between models, services, and database tables.
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize the mapper.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.models_dir = project_root / "src" / "models"
        self.services_dir = project_root / "src" / "services"
        
        # Initialize graphs for different types of relationships
        self.model_dependencies = nx.DiGraph()  # Model-to-model dependencies
        self.service_dependencies = nx.DiGraph()  # Service-to-service dependencies
        self.model_service_dependencies = nx.DiGraph()  # Model-to-service dependencies
        self.db_relationships = nx.DiGraph()  # Database table relationships
        
        # Initialize caches
        self.model_cache = {}  # Cache for parsed model information
        self.service_cache = {}  # Cache for parsed service information
        self.import_cache = {}  # Cache for import statements
        
        # Initialize metadata storage
        self.metadata = {
            "models": {},
            "services": {},
            "tables": {},
            "relationships": {},
            "circular_deps": set()
        }
    
    def analyze_models(self) -> Dict[str, Any]:
        """
        Analyze all models in the project.
        
        Returns:
            Dictionary containing model analysis results
        """
        logger.info("Analyzing models...")
        model_files = [f for f in os.listdir(self.models_dir) 
                      if f.endswith('.py') and not f.startswith('__')]
        
        for model_file in model_files:
            self._analyze_model_file(model_file)
        
        # Analyze model relationships
        self._analyze_model_relationships()
        
        return {
            "models": self.metadata["models"],
            "relationships": self.metadata["relationships"]
        }
    
    def analyze_services(self) -> Dict[str, Any]:
        """
        Analyze all services in the project.
        
        Returns:
            Dictionary containing service analysis results
        """
        logger.info("Analyzing services...")
        service_files = [f for f in os.listdir(self.services_dir) 
                        if f.endswith('.py') and not f.startswith('__')]
        
        for service_file in service_files:
            self._analyze_service_file(service_file)
        
        # Detect circular dependencies
        self._detect_circular_dependencies()
        
        return {
            "services": self.metadata["services"],
            "circular_deps": list(self.metadata["circular_deps"])
        }
    
    def analyze_database_schema(self, engine) -> Dict[str, Any]:
        """
        Analyze database schema and relationships.
        
        Args:
            engine: SQLAlchemy engine instance
            
        Returns:
            Dictionary containing schema analysis results
        """
        logger.info("Analyzing database schema...")
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        # Analyze each table
        for table_name in metadata.tables:
            table = metadata.tables[table_name]
            self.metadata["tables"][table_name] = {
                "columns": self._get_table_columns(table),
                "foreign_keys": self._get_table_foreign_keys(table),
                "indices": self._get_table_indices(table)
            }
            
            # Add relationships to graph
            for fk in table.foreign_keys:
                self.db_relationships.add_edge(
                    table_name,
                    fk.column.table.name,
                    type="foreign_key"
                )
        
        return {
            "tables": self.metadata["tables"],
            "relationships": self._get_relationship_summary()
        }
    
    def _analyze_model_file(self, model_file: str):
        """Analyze a single model file."""
        try:
            file_path = self.models_dir / model_file
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse the AST
            tree = ast.parse(content)
            
            # Extract model information
            model_info = {
                "classes": self._extract_classes(tree),
                "imports": self._extract_imports(tree),
                "dependencies": self._extract_dependencies(tree),
                "attributes": self._extract_attributes(tree)
            }
            
            model_name = model_file.replace('.py', '')
            self.metadata["models"][model_name] = model_info
            
            # Update dependency graph
            for dep in model_info["dependencies"]:
                self.model_dependencies.add_edge(model_name, dep)
                
        except Exception as e:
            logger.error(f"Error analyzing model file {model_file}: {str(e)}")
    
    def _analyze_service_file(self, service_file: str):
        """Analyze a single service file."""
        try:
            file_path = self.services_dir / service_file
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse the AST
            tree = ast.parse(content)
            
            # Extract service information
            service_info = {
                "classes": self._extract_classes(tree),
                "imports": self._extract_imports(tree),
                "model_dependencies": self._extract_model_dependencies(tree),
                "service_dependencies": self._extract_service_dependencies(tree),
                "function_calls": self._extract_function_calls(tree)
            }
            
            service_name = service_file.replace('.py', '')
            self.metadata["services"][service_name] = service_info
            
            # Update dependency graphs
            for dep in service_info["service_dependencies"]:
                self.service_dependencies.add_edge(service_name, dep)
            
            for model in service_info["model_dependencies"]:
                self.model_service_dependencies.add_edge(service_name, model)
            
            # Add dependencies from function calls
            for called_service in service_info["function_calls"]:
                self.service_dependencies.add_edge(service_name, called_service)
                
        except Exception as e:
            logger.error(f"Error analyzing service file {service_file}: {str(e)}")
    
    def _analyze_model_relationships(self):
        """Analyze relationships between models using SQLAlchemy metadata."""
        for model_name, model_info in self.metadata["models"].items():
            for class_name in model_info["classes"]:
                try:
                    # Get the actual model class
                    model_class = self._get_model_class(model_name, class_name)
                    if not model_class:
                        continue
                    
                    # Get mapper for the model
                    mapper = class_mapper(model_class)
                    
                    # Analyze relationships
                    relationships = {}
                    for rel in mapper.relationships:
                        relationships[rel.key] = {
                            "target": rel.target.name,
                            "type": rel.direction.name,
                            "cascade": rel.cascade,
                            "uselist": rel.uselist
                        }
                    
                    self.metadata["relationships"][class_name] = relationships
                    
                except Exception as e:
                    logger.error(f"Error analyzing relationships for {class_name}: {str(e)}")
    
    def _detect_circular_dependencies(self):
        """Detect circular dependencies in services."""
        try:
            # First, ensure all nodes are in the graph
            service_files = [f.replace('.py', '') for f in os.listdir(self.services_dir) 
                           if f.endswith('.py') and not f.startswith('__')]
            for service in service_files:
                if service not in self.service_dependencies:
                    self.service_dependencies.add_node(service)
            
            # Find all simple cycles
            cycles = list(nx.simple_cycles(self.service_dependencies))
            
            # Add cycles to metadata
            self.metadata["circular_deps"].update(tuple(cycle) for cycle in cycles)
            
            # Log found cycles
            if cycles:
                logger.info(f"Found {len(cycles)} circular dependencies:")
                for cycle in cycles:
                    logger.info(f"  - {' -> '.join(cycle)}")
            
        except Exception as e:
            logger.error(f"Error detecting circular dependencies: {str(e)}")
    
    def _extract_classes(self, tree: ast.AST) -> List[str]:
        """Extract class definitions from AST."""
        return [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    
    def _extract_imports(self, tree: ast.AST) -> List[Dict[str, str]]:
        """Extract import statements from AST."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend({"name": n.name, "asname": n.asname} for n in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.extend({
                    "name": n.name,
                    "asname": n.asname,
                    "module": node.module
                } for n in node.names)
        return imports
    
    def _extract_dependencies(self, tree: ast.AST) -> Set[str]:
        """Extract model dependencies from AST."""
        deps = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "models" in node.module:
                    deps.update(n.name for n in node.names)
        return deps
    
    def _extract_attributes(self, tree: ast.AST) -> Dict[str, List[str]]:
        """Extract class attributes from AST."""
        attributes = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                attributes[node.name] = [
                    n.target.id for n in node.body 
                    if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
                ]
        return attributes
    
    def _extract_model_dependencies(self, tree: ast.AST) -> Set[str]:
        """Extract model dependencies from service file AST."""
        deps = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "models" in node.module:
                    deps.update(n.name for n in node.names)
        return deps
    
    def _extract_service_dependencies(self, tree: ast.AST) -> Set[str]:
        """Extract service dependencies from service file AST."""
        deps = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and (node.module.startswith('.') or 'services' in node.module):
                    # Handle both relative and absolute imports
                    deps.update(n.name.split('.')[0].lower() for n in node.names)
            elif isinstance(node, ast.Import):
                # Handle direct imports
                for name in node.names:
                    if 'services' in name.name:
                        deps.add(name.name.split('.')[-1].lower())
        return deps
    
    def _extract_function_calls(self, tree: ast.AST) -> Set[str]:
        """Extract service dependencies from function calls."""
        deps = set()
        service_functions = {
            'calculate_financial_projection': 'financial_service',
            'model_shift_operations': 'equipment_service',
            'calculate_sales_forecast': 'sales_service',
            'calculate_ga_expenses': 'ga_services',
            'optimize_equipment_purchases': 'equipment_service',
            'calculate_financial_projections': 'financial_service',
            'calculate_unit_economics': 'financial_service',
            'calculate_equipment_utilization': 'equipment_service',
            'get_comprehensive_analysis': 'financial_service',
            'get_risk_adjusted_metrics': 'financial_service'
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    # Direct function calls
                    if node.func.id in service_functions:
                        deps.add(service_functions[node.func.id])
                elif isinstance(node.func, ast.Attribute):
                    # Method calls on service instances
                    if isinstance(node.func.value, ast.Name):
                        service_instance = node.func.value.id.lower()
                        if 'service' in service_instance:
                            deps.add(service_instance)
                    # Check for imported function calls
                    if node.func.attr in service_functions:
                        deps.add(service_functions[node.func.attr])
        return deps
    
    def _get_model_class(self, model_name: str, class_name: str) -> Optional[type]:
        """Get the actual model class from its name."""
        try:
            # Import the model module
            module = __import__(f"src.models.{model_name}", fromlist=[class_name])
            return getattr(module, class_name)
        except Exception as e:
            logger.error(f"Error getting model class {class_name}: {str(e)}")
            return None
    
    def _get_table_columns(self, table) -> Dict[str, Dict[str, Any]]:
        """Get column information for a table."""
        return {
            col.name: {
                "type": str(col.type),
                "nullable": col.nullable,
                "primary_key": col.primary_key,
                "default": str(col.default) if col.default else None
            }
            for col in table.columns
        }
    
    def _get_table_foreign_keys(self, table) -> List[Dict[str, str]]:
        """Get foreign key information for a table."""
        return [{
            "column": fk.parent.name,
            "references": f"{fk.column.table.name}.{fk.column.name}"
        } for fk in table.foreign_keys]
    
    def _get_table_indices(self, table) -> List[Dict[str, Any]]:
        """Get index information for a table."""
        return [{
            "name": idx.name,
            "columns": [col.name for col in idx.columns],
            "unique": idx.unique
        } for idx in table.indexes]
    
    def _get_relationship_summary(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get a summary of all relationships."""
        return {
            "model_relationships": [
                {"source": s, "target": t, "attrs": d}
                for s, t, d in self.model_dependencies.edges(data=True)
            ],
            "service_relationships": [
                {"source": s, "target": t, "attrs": d}
                for s, t, d in self.service_dependencies.edges(data=True)
            ],
            "model_service_relationships": [
                {"source": s, "target": t, "attrs": d}
                for s, t, d in self.model_service_dependencies.edges(data=True)
            ],
            "database_relationships": [
                {"source": s, "target": t, "attrs": d}
                for s, t, d in self.db_relationships.edges(data=True)
            ]
        }
    
    def generate_report(self) -> str:
        """
        Generate a comprehensive analysis report.
        
        Returns:
            Formatted report string
        """
        report = []
        report.append("# Enhanced Model Analysis Report")
        report.append("=" * 50)
        
        # Model Analysis
        report.append("\n## Model Analysis")
        report.append("-" * 20)
        for model_name, model_info in self.metadata["models"].items():
            report.append(f"\n### {model_name}")
            report.append("\nClasses:")
            for class_name in model_info["classes"]:
                report.append(f"- {class_name}")
            
            report.append("\nDependencies:")
            for dep in model_info["dependencies"]:
                report.append(f"- {dep}")
        
        # Service Analysis
        report.append("\n## Service Analysis")
        report.append("-" * 20)
        for service_name, service_info in self.metadata["services"].items():
            report.append(f"\n### {service_name}")
            report.append("\nModel Dependencies:")
            for dep in service_info["model_dependencies"]:
                report.append(f"- {dep}")
            
            report.append("\nService Dependencies:")
            for dep in service_info["service_dependencies"]:
                report.append(f"- {dep}")
        
        # Database Analysis
        report.append("\n## Database Analysis")
        report.append("-" * 20)
        for table_name, table_info in self.metadata["tables"].items():
            report.append(f"\n### {table_name}")
            report.append("\nColumns:")
            for col_name, col_info in table_info["columns"].items():
                report.append(f"- {col_name}: {col_info['type']}")
            
            report.append("\nForeign Keys:")
            for fk in table_info["foreign_keys"]:
                report.append(f"- {fk['column']} -> {fk['references']}")
        
        # Circular Dependencies
        if self.metadata["circular_deps"]:
            report.append("\n## Circular Dependencies")
            report.append("-" * 20)
            for cycle in self.metadata["circular_deps"]:
                report.append(f"- {' -> '.join(cycle)}")
        
        return "\n".join(report)

def create_model_map(project_root: str, engine) -> Dict[str, Any]:
    """
    Create a comprehensive model map for the project.
    
    Args:
        project_root: Path to project root directory
        engine: SQLAlchemy engine instance
        
    Returns:
        Dictionary containing complete analysis results
    """
    mapper = ModelRelationshipMapper(Path(project_root))
    
    # Run all analyses
    model_analysis = mapper.analyze_models()
    service_analysis = mapper.analyze_services()
    schema_analysis = mapper.analyze_database_schema(engine)
    
    # Generate report
    report = mapper.generate_report()
    
    # Save report
    report_path = Path(project_root) / "docs" / "enhanced_model_analysis.md"
    with open(report_path, 'w') as f:
        f.write(report)
    
    return {
        "models": model_analysis,
        "services": service_analysis,
        "schema": schema_analysis,
        "report_path": str(report_path)
    } 