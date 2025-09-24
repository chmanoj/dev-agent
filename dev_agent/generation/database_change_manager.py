"""Database change management for generating migrations and updating queries.

This module handles database schema changes, migration generation,
and updating related database queries.
"""

from __future__ import annotations

import ast
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from ..interfaces.analysis_interface import ICodebaseAnalyzer
from ..models.results import GeneratedCode


class DatabaseChange:
    """Represents a database schema change."""

    def __init__(
        self,
        change_type: str,  # 'create_table', 'alter_table', 'drop_table', 'add_column', etc.
        table_name: str,
        details: dict[str, Any],
        sql_statement: str = "",
    ):
        """Initialize a database change."""
        self.change_type = change_type
        self.table_name = table_name
        self.details = details
        self.sql_statement = sql_statement


class DatabaseChangeManager:
    """Manages database changes and generates migrations."""

    def __init__(self, codebase_analyzer: ICodebaseAnalyzer):
        """Initialize the database change manager."""
        self.codebase_analyzer = codebase_analyzer

    def generate_migrations(
        self, primary_code: GeneratedCode, context: Any
    ) -> list[GeneratedCode]:
        """Generate database migrations for the new code."""
        # Detect database changes in the generated code
        db_changes = self._detect_database_changes(primary_code, context)

        if not db_changes:
            return []

        migrations = []

        # Generate migration files
        migration_file = self._generate_migration_file(db_changes, context)
        if migration_file:
            migrations.append(migration_file)

        # Generate rollback migration
        rollback_file = self._generate_rollback_migration(db_changes, context)
        if rollback_file:
            migrations.append(rollback_file)

        # Update existing queries if needed
        query_updates = self._update_existing_queries(db_changes, context)
        migrations.extend(query_updates)

        return migrations

    def _detect_database_changes(
        self, primary_code: GeneratedCode, context: Any
    ) -> list[DatabaseChange]:
        """Detect database changes in the generated code."""
        changes = []

        try:
            tree = ast.parse(primary_code.code)

            # Look for SQLAlchemy models or similar patterns
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it's a database model
                    if self._is_database_model(node):
                        change = self._analyze_model_changes(node)
                        if change:
                            changes.append(change)

                elif isinstance(node, ast.FunctionDef):
                    # Check for database migration functions
                    if 'migration' in node.name.lower() or 'migrate' in node.name.lower():
                        change = self._analyze_migration_function(node)
                        if change:
                            changes.append(change)

        except SyntaxError:
            pass

        # Look for SQL statements in the code
        sql_changes = self._detect_sql_statements(primary_code.code)
        changes.extend(sql_changes)

        return changes

    def _is_database_model(self, node: ast.ClassDef) -> bool:
        """Check if a class is a database model."""
        # Check for common ORM base classes
        base_class_names = [ast.unparse(base) for base in node.bases]
        
        orm_indicators = [
            'Base', 'Model', 'db.Model', 'DeclarativeBase',
            'SQLModel', 'BaseModel'
        ]

        # Check if inherits from ORM base class
        if any(indicator in ' '.join(base_class_names) for indicator in orm_indicators):
            return True

        # Check for ORM decorators
        for decorator in node.decorator_list:
            decorator_name = ast.unparse(decorator)
            if 'table' in decorator_name.lower() or 'entity' in decorator_name.lower():
                return True

        # Check for table-related attributes
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        if target.id == '__tablename__':
                            return True

        return False

    def _analyze_model_changes(self, node: ast.ClassDef) -> DatabaseChange | None:
        """Analyze a database model for schema changes."""
        table_name = self._extract_table_name(node)
        
        if not table_name:
            table_name = self._camel_to_snake(node.name)

        # Extract columns from the model
        columns = self._extract_model_columns(node)
        
        # For new models, this is a table creation
        return DatabaseChange(
            change_type='create_table',
            table_name=table_name,
            details={
                'columns': columns,
                'model_name': node.name,
            },
            sql_statement=self._generate_create_table_sql(table_name, columns)
        )

    def _analyze_migration_function(self, node: ast.FunctionDef) -> DatabaseChange | None:
        """Analyze a migration function for database changes."""
        # This is a simplified implementation
        # In practice, you'd analyze the function body for SQL operations
        
        function_name = node.name
        docstring = ast.get_docstring(node)
        
        return DatabaseChange(
            change_type='custom_migration',
            table_name='unknown',
            details={
                'function_name': function_name,
                'description': docstring or f"Custom migration: {function_name}",
            }
        )

    def _detect_sql_statements(self, code: str) -> list[DatabaseChange]:
        """Detect SQL statements in the code."""
        changes = []

        # Look for SQL strings
        sql_patterns = [
            r'CREATE\s+TABLE\s+(\w+)',
            r'ALTER\s+TABLE\s+(\w+)',
            r'DROP\s+TABLE\s+(\w+)',
            r'INSERT\s+INTO\s+(\w+)',
            r'UPDATE\s+(\w+)\s+SET',
            r'DELETE\s+FROM\s+(\w+)',
        ]

        for pattern in sql_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                table_name = match.group(1)
                sql_type = match.group(0).split()[0].lower()
                
                change = DatabaseChange(
                    change_type=f'sql_{sql_type}',
                    table_name=table_name,
                    details={'raw_sql': match.group(0)},
                    sql_statement=match.group(0)
                )
                changes.append(change)

        return changes

    def _extract_table_name(self, node: ast.ClassDef) -> str | None:
        """Extract table name from a model class."""
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == '__tablename__':
                        if isinstance(item.value, ast.Constant):
                            return item.value.value
        return None

    def _extract_model_columns(self, node: ast.ClassDef) -> list[dict[str, Any]]:
        """Extract column definitions from a model class."""
        columns = []

        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                column_name = item.target.id
                
                # Skip private attributes and special methods
                if column_name.startswith('_'):
                    continue

                column_info = {
                    'name': column_name,
                    'type': self._extract_column_type(item),
                    'nullable': True,  # Default
                    'primary_key': False,
                    'unique': False,
                }

                # Analyze the column definition for constraints
                if item.value:
                    constraints = self._analyze_column_constraints(item.value)
                    column_info.update(constraints)

                columns.append(column_info)

        return columns

    def _extract_column_type(self, ann_assign: ast.AnnAssign) -> str:
        """Extract column type from annotation."""
        if ann_assign.annotation:
            type_str = ast.unparse(ann_assign.annotation)
            
            # Map Python types to SQL types
            type_mapping = {
                'int': 'INTEGER',
                'str': 'VARCHAR',
                'float': 'FLOAT',
                'bool': 'BOOLEAN',
                'datetime': 'TIMESTAMP',
                'date': 'DATE',
                'Decimal': 'DECIMAL',
            }

            for py_type, sql_type in type_mapping.items():
                if py_type in type_str:
                    return sql_type

            return 'VARCHAR'  # Default

        return 'VARCHAR'

    def _analyze_column_constraints(self, value_node: ast.AST) -> dict[str, Any]:
        """Analyze column constraints from the value assignment."""
        constraints = {}

        if isinstance(value_node, ast.Call):
            # Look for Column() calls or similar
            func_name = ast.unparse(value_node.func) if hasattr(value_node, 'func') else ''
            
            if 'Column' in func_name:
                # Analyze Column arguments
                for arg in value_node.args:
                    arg_str = ast.unparse(arg)
                    if 'primary_key' in arg_str:
                        constraints['primary_key'] = True
                    elif 'unique' in arg_str:
                        constraints['unique'] = True

                # Analyze keyword arguments
                for keyword in value_node.keywords:
                    if keyword.arg == 'nullable':
                        constraints['nullable'] = ast.literal_eval(keyword.value)
                    elif keyword.arg == 'primary_key':
                        constraints['primary_key'] = ast.literal_eval(keyword.value)
                    elif keyword.arg == 'unique':
                        constraints['unique'] = ast.literal_eval(keyword.value)

        return constraints

    def _generate_migration_file(
        self, db_changes: list[DatabaseChange], context: Any
    ) -> GeneratedCode | None:
        """Generate a migration file for the database changes."""
        if not db_changes:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        migration_name = f"migration_{timestamp}"
        
        # Generate migration content
        migration_content = self._create_migration_content(db_changes, migration_name)
        
        # Determine migration file path
        migration_path = self._get_migration_file_path(migration_name)

        return GeneratedCode(
            code=migration_content,
            file_path=migration_path,
            imports=['from alembic import op', 'import sqlalchemy as sa'],
            dependencies=['alembic', 'sqlalchemy'],
        )

    def _generate_rollback_migration(
        self, db_changes: list[DatabaseChange], context: Any
    ) -> GeneratedCode | None:
        """Generate rollback migration for the changes."""
        if not db_changes:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rollback_name = f"rollback_{timestamp}"
        
        # Generate rollback content
        rollback_content = self._create_rollback_content(db_changes, rollback_name)
        
        # Determine rollback file path
        rollback_path = self._get_migration_file_path(rollback_name)

        return GeneratedCode(
            code=rollback_content,
            file_path=rollback_path,
            imports=['from alembic import op', 'import sqlalchemy as sa'],
            dependencies=['alembic', 'sqlalchemy'],
        )

    def _update_existing_queries(
        self, db_changes: list[DatabaseChange], context: Any
    ) -> list[GeneratedCode]:
        """Update existing database queries to work with schema changes."""
        query_updates = []

        # Find files with database queries
        query_files = self._find_query_files()

        for file_path in query_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                updated_content = self._update_queries_in_file(content, db_changes)
                
                if updated_content != content:
                    query_update = GeneratedCode(
                        code=updated_content,
                        file_path=file_path,
                        imports=[],
                        dependencies=[],
                    )
                    query_updates.append(query_update)

            except Exception:
                continue

        return query_updates

    def _create_migration_content(
        self, db_changes: list[DatabaseChange], migration_name: str
    ) -> str:
        """Create the content for a migration file."""
        content_parts = [
            f'"""Migration: {migration_name}',
            '',
            'Auto-generated migration for database schema changes.',
            '"""',
            '',
            'from alembic import op',
            'import sqlalchemy as sa',
            '',
            '',
            'def upgrade():',
            '    """Apply the migration."""',
        ]

        # Add upgrade operations
        for change in db_changes:
            if change.change_type == 'create_table':
                content_parts.extend(self._generate_create_table_migration(change))
            elif change.change_type.startswith('sql_'):
                content_parts.append(f'    op.execute("{change.sql_statement}")')

        content_parts.extend([
            '',
            '',
            'def downgrade():',
            '    """Rollback the migration."""',
        ])

        # Add downgrade operations
        for change in reversed(db_changes):
            if change.change_type == 'create_table':
                content_parts.append(f'    op.drop_table("{change.table_name}")')

        return '\n'.join(content_parts)

    def _create_rollback_content(
        self, db_changes: list[DatabaseChange], rollback_name: str
    ) -> str:
        """Create the content for a rollback migration file."""
        content_parts = [
            f'"""Rollback Migration: {rollback_name}',
            '',
            'Rollback migration for database schema changes.',
            '"""',
            '',
            'from alembic import op',
            'import sqlalchemy as sa',
            '',
            '',
            'def upgrade():',
            '    """Rollback the changes."""',
        ]

        # Add rollback operations (reverse of original changes)
        for change in reversed(db_changes):
            if change.change_type == 'create_table':
                content_parts.append(f'    op.drop_table("{change.table_name}")')

        content_parts.extend([
            '',
            '',
            'def downgrade():',
            '    """Re-apply the original changes."""',
        ])

        # Add re-apply operations
        for change in db_changes:
            if change.change_type == 'create_table':
                content_parts.extend(self._generate_create_table_migration(change))

        return '\n'.join(content_parts)

    def _generate_create_table_migration(self, change: DatabaseChange) -> list[str]:
        """Generate create table migration code."""
        lines = [
            f'    op.create_table("{change.table_name}",',
        ]

        columns = change.details.get('columns', [])
        for i, column in enumerate(columns):
            column_def = self._generate_column_definition(column)
            comma = ',' if i < len(columns) - 1 else ''
            lines.append(f'        {column_def}{comma}')

        lines.append('    )')

        return lines

    def _generate_column_definition(self, column: dict[str, Any]) -> str:
        """Generate SQLAlchemy column definition."""
        col_type = column['type']
        col_name = column['name']
        
        constraints = []
        
        if column.get('primary_key'):
            constraints.append('primary_key=True')
        
        if not column.get('nullable', True):
            constraints.append('nullable=False')
            
        if column.get('unique'):
            constraints.append('unique=True')

        constraint_str = ', '.join(constraints)
        if constraint_str:
            constraint_str = ', ' + constraint_str

        return f'sa.Column("{col_name}", sa.{col_type}(){constraint_str})'

    def _generate_create_table_sql(self, table_name: str, columns: list[dict[str, Any]]) -> str:
        """Generate CREATE TABLE SQL statement."""
        column_defs = []
        
        for column in columns:
            col_def = f"{column['name']} {column['type']}"
            
            if column.get('primary_key'):
                col_def += ' PRIMARY KEY'
            elif not column.get('nullable', True):
                col_def += ' NOT NULL'
                
            if column.get('unique'):
                col_def += ' UNIQUE'
                
            column_defs.append(col_def)

        return f"CREATE TABLE {table_name} ({', '.join(column_defs)})"

    def _get_migration_file_path(self, migration_name: str) -> str:
        """Get the file path for a migration file."""
        # Look for common migration directories
        migration_dirs = [
            'migrations/versions',
            'alembic/versions',
            'db/migrations',
            'database/migrations',
        ]

        for migration_dir in migration_dirs:
            if Path(migration_dir).exists():
                return f"{migration_dir}/{migration_name}.py"

        # Default to creating migrations directory
        Path("migrations/versions").mkdir(parents=True, exist_ok=True)
        return f"migrations/versions/{migration_name}.py"

    def _find_query_files(self) -> list[str]:
        """Find files that contain database queries."""
        query_files = []

        # Look for Python files that might contain queries
        for py_file in Path(".").glob("**/*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check for SQL keywords or ORM usage
                sql_indicators = [
                    'SELECT', 'INSERT', 'UPDATE', 'DELETE',
                    'session.query', 'db.session', '.filter',
                    'CREATE TABLE', 'ALTER TABLE'
                ]

                if any(indicator in content.upper() for indicator in sql_indicators):
                    query_files.append(str(py_file))

            except Exception:
                continue

        return query_files

    def _update_queries_in_file(
        self, content: str, db_changes: list[DatabaseChange]
    ) -> str:
        """Update database queries in a file based on schema changes."""
        updated_content = content

        for change in db_changes:
            if change.change_type == 'create_table':
                # Add imports for new models if needed
                model_name = change.details.get('model_name')
                if model_name and f"from .models import {model_name}" not in content:
                    # Add import at the top of the file
                    lines = updated_content.split('\n')
                    import_line = f"from .models import {model_name}"
                    
                    # Find appropriate place to insert import
                    insert_idx = 0
                    for i, line in enumerate(lines):
                        if line.startswith('from ') or line.startswith('import '):
                            insert_idx = i + 1
                        elif line.strip() and not line.startswith('#'):
                            break

                    lines.insert(insert_idx, import_line)
                    updated_content = '\n'.join(lines)

        return updated_content

    def _camel_to_snake(self, name: str) -> str:
        """Convert CamelCase to snake_case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()