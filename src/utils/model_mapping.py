"""
Utility module for maintaining and verifying model-service and model-database mappings.
"""

from typing import Dict, List, Set, Any, Optional
from sqlalchemy import inspect, Table, Column
from sqlalchemy.orm import class_mapper
import importlib
import os
import ast

class ModelMapper:
    """Utility class for analyzing and maintaining model-service mappings."""
    
    def __init__(self, models_dir: str, services_dir: str):
        """
        Initialize ModelMapper.
        
        Args:
            models_dir: Directory containing model files
            services_dir: Directory containing service files
        """
        self.models_dir = models_dir
        self.services_dir = services_dir
        self.model_service_map: Dict[str, Set[str]] = {}
        self.model_field_map: Dict[str, Dict[str, Set[str]]] = {}
        self.database_schema_map: Dict[str, Dict[str, Any]] = {}
    
    def analyze_model_usage(self) -> Dict[str, Set[str]]:
        """
        Analyze which services use which models.
        
        Returns:
            Dictionary mapping model names to sets of service names that use them
        """
        # Get all model files
        model_files = [f for f in os.listdir(self.models_dir) 
                      if f.endswith('.py') and not f.startswith('__')]
        
        # Get all service files
        service_files = [f for f in os.listdir(self.services_dir) 
                        if f.endswith('.py') and not f.startswith('__')]
        
        for model_file in model_files:
            model_name = model_file.replace('.py', '')
            self.model_service_map[model_name] = set()
            
            for service_file in service_files:
                service_path = os.path.join(self.services_dir, service_file)
                with open(service_path, 'r') as f:
                    content = f.read()
                    if f"from ..models import {model_name}" in content or \
                       f"from ..models.{model_name}" in content:
                        self.model_service_map[model_name].add(service_file.replace('.py', ''))
        
        return self.model_service_map
    
    def analyze_model_fields(self, model_class: Any) -> Dict[str, Set[str]]:
        """
        Analyze which fields in a model are used by which services.
        
        Args:
            model_class: The SQLAlchemy model class to analyze
            
        Returns:
            Dictionary mapping field names to sets of service names that use them
        """
        model_name = model_class.__name__
        self.model_field_map[model_name] = {}
        
        # Get all fields from the model
        mapper = class_mapper(model_class)
        for column in mapper.columns:
            field_name = column.name
            self.model_field_map[model_name][field_name] = set()
            
            # Check each service that uses this model
            for service_name in self.model_service_map.get(model_name, set()):
                service_path = os.path.join(self.services_dir, f"{service_name}.py")
                with open(service_path, 'r') as f:
                    content = f.read()
                    if field_name in content:
                        self.model_field_map[model_name][field_name].add(service_name)
        
        return self.model_field_map
    
    def analyze_database_schema(self, engine) -> Dict[str, Dict[str, Any]]:
        """
        Analyze the actual database schema.
        
        Args:
            engine: SQLAlchemy engine instance
            
        Returns:
            Dictionary mapping table names to their schema information
        """
        inspector = inspect(engine)
        
        for table_name in inspector.get_table_names():
            self.database_schema_map[table_name] = {
                'columns': {},
                'foreign_keys': [],
                'primary_keys': []
            }
            
            # Get column information
            for column in inspector.get_columns(table_name):
                self.database_schema_map[table_name]['columns'][column['name']] = {
                    'type': str(column['type']),
                    'nullable': column.get('nullable', True),
                    'default': column.get('default', None)
                }
            
            # Get foreign key information
            for fk in inspector.get_foreign_keys(table_name):
                self.database_schema_map[table_name]['foreign_keys'].append({
                    'constrained_columns': fk['constrained_columns'],
                    'referred_table': fk['referred_table'],
                    'referred_columns': fk['referred_columns']
                })
            
            # Get primary key information
            pk = inspector.get_pk_constraint(table_name)
            self.database_schema_map[table_name]['primary_keys'] = pk['constrained_columns']
        
        return self.database_schema_map
    
    def generate_report(self) -> str:
        """
        Generate a detailed report of the mappings.
        
        Returns:
            String containing the formatted report
        """
        report = []
        report.append("Model-Service Mapping Report")
        report.append("=" * 50)
        
        # Model-Service Usage
        report.append("\nModel-Service Usage:")
        report.append("-" * 20)
        for model, services in self.model_service_map.items():
            report.append(f"\n{model}:")
            for service in sorted(services):
                report.append(f"  - {service}")
        
        # Model Field Usage
        report.append("\nModel Field Usage:")
        report.append("-" * 20)
        for model, fields in self.model_field_map.items():
            report.append(f"\n{model}:")
            for field, services in fields.items():
                report.append(f"  - {field}:")
                for service in sorted(services):
                    report.append(f"    * {service}")
        
        # Database Schema
        report.append("\nDatabase Schema:")
        report.append("-" * 20)
        for table, schema in self.database_schema_map.items():
            report.append(f"\n{table}:")
            report.append("  Columns:")
            for column, info in schema['columns'].items():
                report.append(f"    - {column}: {info['type']}")
            if schema['foreign_keys']:
                report.append("  Foreign Keys:")
                for fk in schema['foreign_keys']:
                    report.append(f"    - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
            if schema['primary_keys']:
                report.append(f"  Primary Keys: {schema['primary_keys']}")
        
        return "\n".join(report)
    
    def verify_consistency(self) -> List[str]:
        """
        Verify consistency between models, services, and database schema.
        
        Returns:
            List of inconsistency warnings
        """
        warnings = []
        
        # Check for unused models
        for model in self.model_service_map:
            if not self.model_service_map[model]:
                warnings.append(f"Warning: Model '{model}' is not used by any service")
        
        # Check for unused fields
        for model, fields in self.model_field_map.items():
            for field, services in fields.items():
                if not services:
                    warnings.append(f"Warning: Field '{field}' in model '{model}' is not used by any service")
        
        # Check for missing database tables
        for model in self.model_service_map:
            if model.lower() not in self.database_schema_map:
                warnings.append(f"Warning: No database table found for model '{model}'")
        
        return warnings 