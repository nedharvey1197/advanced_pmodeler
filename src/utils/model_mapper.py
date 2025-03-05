"""
Dynamic model mapping and validation system.

This module maintains a live map of:
1. Database schemas
2. Model definitions
3. Service dependencies
4. Data integrity
"""

import os
import inspect
import importlib
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from sqlalchemy import inspect as sql_inspect
from sqlalchemy.orm import class_mapper
import networkx as nx
import json
from datetime import datetime

class ModelMap:
    """Represents the complete model mapping of the system."""
    def __init__(self):
        self.tables: Dict[str, Dict] = {}  # Database tables
        self.models: Dict[str, Dict] = {}  # Model classes
        self.services: Dict[str, Dict] = {}  # Services
        self.relationships: Dict[str, List] = {}  # Model relationships
        self.service_dependencies: Dict[str, Set] = {}  # Service-to-service dependencies
        self.model_usage: Dict[str, Set] = {}  # Model-to-service usage
        self.validation_errors: List[str] = []  # Validation errors
        self.last_updated = None
        self.metadata: Dict[str, str] = {}  # Additional metadata

    def to_dict(self) -> Dict:
        """Convert map to dictionary for serialization."""
        return {
            "tables": self.tables,
            "models": self.models,
            "services": self.services,
            "relationships": self.relationships,
            "service_dependencies": {k: list(v) for k, v in self.service_dependencies.items()},
            "model_usage": {k: list(v) for k, v in self.model_usage.items()},
            "validation_errors": self.validation_errors,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "metadata": self.metadata
        }

    def to_markdown(self) -> str:
        """Generate clear, tabular documentation."""
        lines = ["# Model and Service Mapping", ""]
        
        # Paths
        if hasattr(self, 'metadata'):
            lines.extend([
                "## Paths",
                "",
                "| Component | Path |",
                "|-----------|------|",
                f"| Database | {self.metadata.get('database_path', 'Not set')} |",
                f"| Models | {self.metadata.get('models_path', 'Not set')} |",
                f"| Services | {self.metadata.get('services_path', 'Not set')} |",
                ""
            ])
        
        # Quick Reference Table
        lines.extend([
            "## Quick Reference",
            "",
            "| Model | Table | Used By Services | Related Models |",
            "|-------|--------|-----------------|----------------|"
        ])
        
        for model_name, model_info in self.models.items():
            services = self.model_usage.get(model_name, set())
            relationships = [r.split(" -> ")[1] for r in model_info.get("relationships", [])]
            lines.append(
                f"| {model_name} | {model_info['table_name']} | "
                f"{', '.join(sorted(services))} | {', '.join(relationships)} |"
            )
        
        # Service Dependencies Table
        lines.extend([
            "",
            "## Service Dependencies",
            "",
            "| Service | Uses Models | Depends On Services |",
            "|---------|-------------|-------------------|"
        ])
        
        for service_name, service_info in self.services.items():
            models = service_info["models_used"]
            deps = service_info["dependencies"]
            lines.append(
                f"| {service_name} | {', '.join(models)} | {', '.join(deps)} |"
            )
        
        # Database Schema Summary
        lines.extend([
            "",
            "## Database Schema",
            "",
            "| Table | Columns | Foreign Keys |",
            "|-------|---------|--------------|"
        ])
        
        for table_name, table_info in self.tables.items():
            columns = [f"{name} ({info['type']})" for name, info in table_info["columns"].items()]
            fks = [f"{fk['constrained_columns'][0]} → {fk['referred_table']}" 
                  for fk in table_info["foreign_keys"]]
            lines.append(
                f"| {table_name} | {', '.join(columns)} | {', '.join(fks) or 'None'} |"
            )
        
        # Validation Issues (if any)
        if self.validation_errors:
            lines.extend([
                "",
                "## ⚠️ Validation Issues",
                "",
                "| Type | Issue |",
                "|------|--------|"
            ])
            for error in self.validation_errors:
                if "Table" in error:
                    error_type = "Schema"
                elif "Circular" in error:
                    error_type = "Dependency"
                else:
                    error_type = "Other"
                lines.append(f"| {error_type} | {error} |")
        
        return "\n".join(lines)

class ModelMapper:
    """
    Dynamic model mapping and validation system.
    
    This class maintains a live map of database schemas, models,
    and service dependencies, ensuring data integrity and providing
    easy-to-read documentation.
    """
    
    def __init__(self, engine, project_root: Path):
        """
        Initialize the mapper.
        
        Args:
            engine: SQLAlchemy engine
            project_root: Root directory of the project
        """
        self.engine = engine
        self.project_root = project_root
        self.models_dir = project_root / "src" / "models"
        self.services_dir = project_root / "src" / "services"
        self.docs_dir = project_root / "docs"
        self.data_dir = project_root / "data"
        self.map = ModelMap()
        
    def generate_map(self) -> ModelMap:
        """Generate complete model map."""
        # Clear previous data
        self.map = ModelMap()
        
        # Add paths to metadata
        self.map.metadata = {
            "database_path": str(self.data_dir / "manufacturing_model.db"),
            "models_path": str(self.models_dir),
            "services_path": str(self.services_dir)
        }
        
        # Map database schema
        self._map_database_schema()
        
        # Map models
        self._map_models()
        
        # Map services
        self._map_services()
        
        # Validate relationships
        self._validate_relationships()
        
        # Update timestamp
        self.map.last_updated = datetime.now()
        
        return self.map
    
    def _map_database_schema(self):
        """Map database schema."""
        inspector = sql_inspect(self.engine)
        
        for table_name in inspector.get_table_names():
            columns = {}
            for column in inspector.get_columns(table_name):
                columns[column["name"]] = {
                    "type": str(column["type"]),
                    "nullable": column["nullable"],
                    "primary_key": column.get("primary_key", False),
                    "default": str(column.get("default", ""))
                }
            
            foreign_keys = []
            for fk in inspector.get_foreign_keys(table_name):
                foreign_keys.append({
                    "referred_table": fk["referred_table"],
                    "referred_columns": fk["referred_columns"],
                    "constrained_columns": fk["constrained_columns"]
                })
            
            self.map.tables[table_name] = {
                "columns": columns,
                "foreign_keys": foreign_keys
            }
    
    def _map_models(self):
        """Map model classes and their relationships."""
        try:
            # Import models through the package
            from src.models import (
                Scenario, Equipment, Product, CostDriver,
                FinancialProjection, SalesParameter, SalesForecast,
                ProductForecast, GAExpense, IndustryStandard,
                ScenarioAssumption
            )
            
            # Map each model
            for name, cls in [(n, c) for n, c in locals().items() 
                            if hasattr(c, '__table__')]:
                try:
                    mapper = class_mapper(cls)
                    self.map.models[name] = {
                        "table_name": mapper.local_table.name,
                        "attributes": [p.key for p in mapper.iterate_properties],
                        "relationships": [
                            f"{r.key} -> {r.mapper.class_.__name__}"
                            for r in mapper.relationships
                        ]
                    }
                except Exception as e:
                    self.map.validation_errors.append(
                        f"Error mapping model {name}: {str(e)}"
                    )
                    
        except Exception as e:
            self.map.validation_errors.append(
                f"Error importing models: {str(e)}"
            )
    
    def _map_services(self):
        """Map services and their dependencies."""
        for service_file in self.services_dir.glob("*.py"):
            if service_file.name.startswith("__"):
                continue
                
            service_name = service_file.stem
            try:
                with open(service_file, 'r') as f:
                    content = f.read()
                
                # Find model imports
                models_used = set()
                for model_name in self.map.models:
                    if f"from ..models import {model_name}" in content or \
                       f"import {model_name}" in content:
                        models_used.add(model_name)
                
                # Find service dependencies
                dependencies = set()
                for other_service in [s.stem for s in self.services_dir.glob("*.py")]:
                    if other_service != service_name and \
                       (f"from .{other_service}" in content or \
                        f"import {other_service}" in content):
                        dependencies.add(other_service)
                
                self.map.services[service_name] = {
                    "models_used": list(models_used),
                    "dependencies": list(dependencies)
                }
                
                # Update model usage
                for model in models_used:
                    if model not in self.map.model_usage:
                        self.map.model_usage[model] = set()
                    self.map.model_usage[model].add(service_name)
                
                # Update service dependencies
                self.map.service_dependencies[service_name] = dependencies
                
            except Exception as e:
                self.map.validation_errors.append(
                    f"Error mapping service {service_name}: {str(e)}"
                )
    
    def _validate_relationships(self):
        """Validate relationships and data integrity."""
        # Check for missing tables
        for model in self.map.models.values():
            if model["table_name"] not in self.map.tables:
                self.map.validation_errors.append(
                    f"Table {model['table_name']} not found in database"
                )
        
        # Check for orphaned tables
        for table in self.map.tables:
            if not any(m["table_name"] == table for m in self.map.models.values()):
                self.map.validation_errors.append(
                    f"Table {table} has no corresponding model"
                )
        
        # Check for circular dependencies
        graph = nx.DiGraph(
            {k: list(v) for k, v in self.map.service_dependencies.items()}
        )
        try:
            cycles = list(nx.simple_cycles(graph))
            if cycles:
                for cycle in cycles:
                    self.map.validation_errors.append(
                        f"Circular dependency detected: {' -> '.join(cycle)}"
                    )
        except Exception:
            pass
    
    def save_documentation(self):
        """Save documentation files."""
        # Save markdown documentation
        docs_path = self.docs_dir / "model_mapping.md"
        with open(docs_path, 'w') as f:
            f.write(self.map.to_markdown())
        
        # Save JSON data
        json_path = self.docs_dir / "model_mapping.json"
        with open(json_path, 'w') as f:
            json.dump(self.map.to_dict(), f, indent=2)
        
        return {
            "markdown": str(docs_path),
            "json": str(json_path)
        }

def create_model_map(engine, project_root: str) -> Dict[str, Any]:
    """
    Create a complete model map.
    
    Args:
        engine: SQLAlchemy engine
        project_root: Path to project root
        
    Returns:
        Dictionary with mapping results and documentation paths
    """
    mapper = ModelMapper(engine, Path(project_root))
    model_map = mapper.generate_map()
    docs = mapper.save_documentation()
    
    return {
        "map": model_map.to_dict(),
        "documentation": docs,
        "errors": model_map.validation_errors
    } 