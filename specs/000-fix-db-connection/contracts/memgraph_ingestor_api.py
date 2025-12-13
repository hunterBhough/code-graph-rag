"""
API Contract: MemgraphIngestor

This file documents the public API contract for the MemgraphIngestor class
with multi-database support. This is NOT executable code, but a specification
for the implementation.

Feature: 001-fix-db-connection
Date: 2025-12-08
"""

from typing import Any, Protocol


class MemgraphIngestorProtocol(Protocol):
    """
    Protocol defining the public API contract for MemgraphIngestor.

    This protocol ensures backward compatibility while adding multi-database support.
    """

    # ============================================================================
    # Constructor
    # ============================================================================

    def __init__(
        self,
        host: str,
        port: int,
        batch_size: int = 1000,
        database_name: str | None = None,  # NEW PARAMETER
    ) -> None:
        """
        Initialize MemgraphIngestor with connection parameters.

        Args:
            host: Memgraph server host address (e.g., 'localhost')
            port: Memgraph server port (e.g., 7687)
            batch_size: Number of items to batch before flushing (default: 1000)
            database_name: Target database name (NEW, FR-001)
                          - If None: use settings.MEMGRAPH_DATABASE (FR-003)
                          - If empty string: no database switching (backward compatible)
                          - If provided: validates and uses specified database

        Raises:
            ValueError: If batch_size < 1 (existing behavior)
            ValueError: If database_name contains invalid characters (NEW, FR-004)

        Examples:
            # Legacy usage (backward compatible)
            ingestor = MemgraphIngestor(host='localhost', port=7687)

            # New usage with explicit database
            ingestor = MemgraphIngestor(
                host='localhost',
                port=7687,
                database_name='codegraph_myproject'
            )

            # New usage with environment variable fallback
            os.environ['MEMGRAPH_DATABASE'] = 'codegraph_myproject'
            ingestor = MemgraphIngestor(host='localhost', port=7687)
            # Uses 'codegraph_myproject' from environment
        """
        ...

    # ============================================================================
    # Context Manager Protocol
    # ============================================================================

    def __enter__(self) -> "MemgraphIngestorProtocol":
        """
        Enter context manager: establish connection and switch database.

        Behavior (MODIFIED):
            1. Connect to Memgraph: mgclient.connect(host, port)
            2. Set autocommit: conn.autocommit = True
            3. IF database_name is set: execute USE DATABASE {database_name} (NEW, FR-002)
            4. Log connection and database context (NEW, FR-009)

        Returns:
            Self for context manager chaining

        Raises:
            ConnectionError: If connection to Memgraph fails
            Exception: If USE DATABASE command fails (NEW, FR-005)
                      - Message format: "Failed to switch to database '{name}': {error}"

        Connection Log Format (NEW):
            - Without database: "Connecting to Memgraph at {host}:{port}..."
            - With database: "Connecting to Memgraph at {host}:{port} (database: {name})..."
        """
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit context manager: flush pending operations and close connection.

        Behavior (UNCHANGED):
            1. If exception occurred: log error
            2. Flush all buffered nodes and relationships
            3. Close connection
            4. Log disconnection

        Args:
            exc_type: Exception type (if exception occurred)
            exc_val: Exception value (if exception occurred)
            exc_tb: Exception traceback (if exception occurred)
        """
        ...

    # ============================================================================
    # Query Execution Methods
    # ============================================================================

    def _execute_query(
        self, query: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Execute a single Cypher query in the current database context.

        Behavior (UNCHANGED from existing implementation):
            - All queries execute in the database context set by USE DATABASE (NEW)
            - If not connected: raises ConnectionError
            - Returns results as list of dictionaries

        Args:
            query: Cypher query string
            params: Query parameters (default: {})

        Returns:
            List of result dictionaries with column names as keys

        Raises:
            ConnectionError: If not connected to Memgraph
            Exception: If query execution fails
        """
        ...

    def _execute_batch(self, query: str, params_list: list[dict[str, Any]]) -> None:
        """
        Execute batch query using UNWIND in the current database context.

        Behavior (UNCHANGED from existing implementation):
            - All queries execute in the database context set by USE DATABASE (NEW)
            - Uses UNWIND $batch AS row pattern
            - Handles constraint violation errors

        Args:
            query: Cypher query template (will be wrapped with UNWIND)
            params_list: List of parameter dictionaries

        Raises:
            Exception: If batch execution fails
        """
        ...

    def _execute_batch_with_return(
        self, query: str, params_list: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Execute batch query with result returns in the current database context.

        Behavior (UNCHANGED from existing implementation):
            - All queries execute in the database context set by USE DATABASE (NEW)
            - Returns results from batch query

        Args:
            query: Cypher query template (will be wrapped with UNWIND)
            params_list: List of parameter dictionaries

        Returns:
            List of result dictionaries

        Raises:
            Exception: If batch execution fails
        """
        ...

    # ============================================================================
    # Database Management Methods
    # ============================================================================

    def clean_database(self) -> None:
        """
        Remove all nodes and relationships from the current database context.

        Behavior (MODIFIED):
            - Executes: MATCH (n) DETACH DELETE n;
            - Operates on the database context set by USE DATABASE (NEW, FR-006)
            - Does NOT affect other databases

        Raises:
            ConnectionError: If not connected to Memgraph
        """
        ...

    def ensure_constraints(self) -> None:
        """
        Create unique constraints for node labels in the current database context.

        Behavior (MODIFIED):
            - Creates constraints for: Project, Package, Folder, Module, Class, Function, Method, File, ExternalPackage
            - Operates on the database context set by USE DATABASE (NEW, FR-006)
            - Constraints are database-specific (not shared across databases)

        Raises:
            ConnectionError: If not connected to Memgraph
        """
        ...

    # ============================================================================
    # Batch Buffer Methods (UNCHANGED)
    # ============================================================================

    def ensure_node_batch(self, label: str, properties: dict[str, Any]) -> None:
        """
        Add node to buffer; flush if batch_size reached.

        Behavior (UNCHANGED):
            - Buffers node for batch insertion
            - Auto-flushes when buffer reaches batch_size

        Args:
            label: Node label (e.g., 'Function', 'Class')
            properties: Node properties dictionary
        """
        ...

    def ensure_relationship_batch(
        self,
        from_spec: tuple[str, str, Any],
        rel_type: str,
        to_spec: tuple[str, str, Any],
        properties: dict[str, Any] | None = None,
    ) -> None:
        """
        Add relationship to buffer; flush if batch_size reached.

        Behavior (UNCHANGED):
            - Buffers relationship for batch insertion
            - Auto-flushes nodes before relationships when buffer reaches batch_size

        Args:
            from_spec: (label, property_key, property_value) for source node
            rel_type: Relationship type (e.g., 'CONTAINS', 'CALLS')
            to_spec: (label, property_key, property_value) for target node
            properties: Relationship properties (optional)
        """
        ...

    def flush_nodes(self) -> None:
        """
        Flush buffered nodes to database.

        Behavior (UNCHANGED):
            - Executes batched node creation queries
            - Clears node buffer after flush
        """
        ...

    def flush_relationships(self) -> None:
        """
        Flush buffered relationships to database.

        Behavior (UNCHANGED):
            - Executes batched relationship creation queries
            - Clears relationship buffer after flush
        """
        ...

    def flush_all(self) -> None:
        """
        Flush all buffered nodes and relationships to database.

        Behavior (UNCHANGED):
            - Flushes nodes first, then relationships
        """
        ...

    # ============================================================================
    # NEW: Static Validation Method
    # ============================================================================

    @staticmethod
    def validate_database_name(name: str) -> bool:
        """
        Validate database name contains only safe characters.

        Validation Rule (NEW, FR-004):
            - Pattern: ^[a-zA-Z0-9_-]+$
            - Must contain only: letters, numbers, underscores, hyphens
            - Empty string returns False
            - None raises TypeError

        Args:
            name: Database name to validate

        Returns:
            True if valid, False otherwise

        Examples:
            >>> MemgraphIngestor.validate_database_name('codegraph_my-project')
            True
            >>> MemgraphIngestor.validate_database_name('codegraph_test_123')
            True
            >>> MemgraphIngestor.validate_database_name('invalid name!')
            False
            >>> MemgraphIngestor.validate_database_name('')
            False
        """
        ...


# ============================================================================
# Configuration Contract
# ============================================================================


class AppConfigProtocol(Protocol):
    """
    Protocol defining configuration settings relevant to database connections.
    """

    # Existing settings
    MEMGRAPH_HOST: str  # Default: "localhost"
    MEMGRAPH_PORT: int  # Default: 7687
    MEMGRAPH_BATCH_SIZE: int  # Default: 1000

    # NEW setting (FR-003)
    MEMGRAPH_DATABASE: str  # Default: "" (empty string for backward compatibility)


# ============================================================================
# Usage Examples
# ============================================================================

"""
Example 1: Backward Compatible Usage (No Database Specified)
-------------------------------------------------------------

with MemgraphIngestor(host='localhost', port=7687) as ingestor:
    ingestor.ensure_node_batch('Function', {'qualified_name': 'main', ...})
    ingestor.flush_all()

# Connects to Memgraph without USE DATABASE command
# Behavior identical to pre-feature implementation


Example 2: Explicit Database Selection
---------------------------------------

with MemgraphIngestor(
    host='localhost',
    port=7687,
    database_name='codegraph_myproject'
) as ingestor:
    ingestor.clean_database()  # Cleans only codegraph_myproject
    ingestor.ensure_constraints()
    ingestor.ensure_node_batch('Function', {'qualified_name': 'main', ...})
    ingestor.flush_all()

# Executes: USE DATABASE codegraph_myproject
# All subsequent queries operate in that database context


Example 3: Environment Variable Configuration
----------------------------------------------

# In .env file or environment:
# MEMGRAPH_DATABASE=codegraph_weavr

from weavr.config import settings

with MemgraphIngestor(host='localhost', port=7687) as ingestor:
    # database_name defaults to settings.MEMGRAPH_DATABASE
    ingestor.ensure_node_batch('Function', {'qualified_name': 'main', ...})
    ingestor.flush_all()

# Automatically uses database from environment variable


Example 4: Stress Test Usage (User Story 2)
--------------------------------------------

import os
os.environ['MEMGRAPH_DATABASE'] = 'codegraph_weavr'

ingestor = MemgraphIngestor(
    host=os.getenv('MEMGRAPH_HOST', 'localhost'),
    port=int(os.getenv('MEMGRAPH_PORT', 7687)),
)

with ingestor:
    results = ingestor._execute_query(
        "MATCH (f:Function) RETURN f.qualified_name LIMIT 10"
    )
    # Results come from codegraph_weavr database only


Example 5: Integration Test Isolation (User Story 3)
-----------------------------------------------------

import pytest
from uuid import uuid4

@pytest.fixture
def test_database():
    db_name = f'codegraph_test_{uuid4().hex[:8]}'

    ingestor = MemgraphIngestor(
        host='localhost',
        port=7687,
        database_name=db_name
    )

    with ingestor:
        ingestor.clean_database()  # Ensure clean state
        yield ingestor
        # Cleanup after test
        ingestor.clean_database()

def test_indexing(test_database):
    test_database.ensure_node_batch('Function', {'qualified_name': 'test_fn', ...})
    test_database.flush_all()

    results = test_database._execute_query(
        "MATCH (f:Function) WHERE f.qualified_name = 'test_fn' RETURN f"
    )
    assert len(results) == 1

# Each test gets isolated database context


Example 6: Multiple Projects in Single Process (User Story 1)
--------------------------------------------------------------

# Project A ingestor
with MemgraphIngestor(
    host='localhost',
    port=7687,
    database_name='codegraph_project-a'
) as ingestor_a:
    ingestor_a.ensure_node_batch('Function', {'qualified_name': 'project_a_fn', ...})
    ingestor_a.flush_all()

# Project B ingestor (can coexist)
with MemgraphIngestor(
    host='localhost',
    port=7687,
    database_name='codegraph_project-b'
) as ingestor_b:
    ingestor_b.ensure_node_batch('Function', {'qualified_name': 'project_b_fn', ...})
    ingestor_b.flush_all()

# No interference between project-a and project-b databases
"""


# ============================================================================
# Error Scenarios
# ============================================================================

"""
Error Scenario 1: Invalid Database Name
----------------------------------------

try:
    ingestor = MemgraphIngestor(
        host='localhost',
        port=7687,
        database_name='invalid name!'  # Contains space and exclamation
    )
except ValueError as e:
    print(e)
    # "Invalid database name 'invalid name!': must contain only alphanumeric
    #  characters, hyphens, and underscores"


Error Scenario 2: Database Switch Failure
------------------------------------------

try:
    with MemgraphIngestor(
        host='localhost',
        port=7687,
        database_name='codegraph_nonexistent'
    ) as ingestor:
        # If Memgraph rejects database creation/switch
        pass
except Exception as e:
    print(e)
    # "Failed to switch to database 'codegraph_nonexistent': <original error>"


Error Scenario 3: Query Without Connection
-------------------------------------------

ingestor = MemgraphIngestor(host='localhost', port=7687)
# NOT using context manager

try:
    ingestor._execute_query("MATCH (n) RETURN n")
except ConnectionError as e:
    print(e)
    # "Not connected to Memgraph."
"""
