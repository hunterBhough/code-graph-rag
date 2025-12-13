"""Structural query tools for weavr.

This module provides pre-built structural query tools for exploring code relationships:
- Function callers and callees
- Class inheritance hierarchies
- Module dependencies
- Interface implementations
- Call graph generation
- Expert mode Cypher queries
"""

from dataclasses import dataclass, field
from typing import Any, Literal

from loguru import logger


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class QueryMetadata:
    """Metadata for query execution."""

    row_count: int
    total_count: int
    truncated: bool
    execution_time_ms: float
    max_depth: int | None = None
    query_type: str = "structural"


@dataclass
class StructuralQueryResult:
    """Base result for all structural queries."""

    query_description: str
    results: list[dict[str, Any]]
    metadata: QueryMetadata


# =============================================================================
# Result Formatting Utilities
# =============================================================================


def format_cypher_results(
    rows: list[dict[str, Any]],
    columns: list[str],
    execution_time_ms: float,
    truncate_limit: int = 100,
) -> dict[str, Any]:
    """Format Cypher query results into standardized structure.

    Args:
        rows: Raw result rows from Cypher query
        columns: Column names from query
        execution_time_ms: Query execution time in milliseconds
        truncate_limit: Maximum rows to return (default: 100)

    Returns:
        Formatted result dictionary with metadata
    """
    total_count = len(rows)
    truncated = total_count > truncate_limit
    limited_rows = rows[:truncate_limit] if truncated else rows

    return {
        "rows": limited_rows,
        "columns": columns,
        "metadata": {
            "row_count": len(limited_rows),
            "total_count": total_count,
            "truncated": truncated,
            "execution_time_ms": round(execution_time_ms, 2),
            "query_type": "structural",
        },
    }


def format_table_output(
    rows: list[dict[str, Any]], columns: list[str], max_rows: int = 50
) -> str:
    """Format query results as ASCII table.

    Args:
        rows: Result rows
        columns: Column names
        max_rows: Maximum rows to display

    Returns:
        Formatted table string
    """
    if not rows:
        return "No results found."

    # Calculate column widths
    col_widths = {col: len(col) for col in columns}
    for row in rows[:max_rows]:
        for col in columns:
            value = str(row.get(col, ""))
            col_widths[col] = max(col_widths[col], len(value))

    # Build header
    header = " | ".join(col.ljust(col_widths[col]) for col in columns)
    separator = "-+-".join("-" * col_widths[col] for col in columns)

    # Build rows
    table_rows = []
    for row in rows[:max_rows]:
        table_row = " | ".join(
            str(row.get(col, "")).ljust(col_widths[col]) for col in columns
        )
        table_rows.append(table_row)

    # Combine
    table = f"{header}\n{separator}\n" + "\n".join(table_rows)

    # Add truncation notice
    if len(rows) > max_rows:
        table += f"\n\n... {len(rows) - max_rows} more rows (showing {max_rows} of {len(rows)})"

    return table


# =============================================================================
# Result Truncation Logic
# =============================================================================


def apply_truncation(
    results: list[Any],
    limit: int,
    query_type: Literal["expert", "prebuilt"] = "prebuilt",
) -> tuple[list[Any], bool, int]:
    """Apply result set truncation based on query type.

    Args:
        results: Query results to truncate
        limit: Explicit limit to apply (overrides defaults)
        query_type: Type of query ("expert" or "prebuilt")

    Returns:
        Tuple of (truncated_results, was_truncated, total_count)
    """
    # Default limits based on query type
    default_limits = {
        "expert": 50,  # Expert mode: smaller limit encourages refinement
        "prebuilt": 100,  # Pre-built: balance completeness vs performance
    }

    effective_limit = limit if limit > 0 else default_limits[query_type]
    total_count = len(results)
    truncated = total_count > effective_limit

    if truncated:
        logger.info(
            f"Truncating results: {total_count} total, returning {effective_limit}"
        )
        return results[:effective_limit], True, total_count
    else:
        return results, False, total_count


def create_truncation_message(
    shown_count: int, total_count: int, query_type: str = "query"
) -> str:
    """Create user-friendly truncation message.

    Args:
        shown_count: Number of results shown
        total_count: Total results available
        query_type: Type of query for context

    Returns:
        Formatted message string
    """
    if shown_count >= total_count:
        return f"All {total_count} results shown."
    else:
        omitted = total_count - shown_count
        return (
            f"Showing {shown_count} of {total_count} results ({omitted} omitted). "
            f"Refine your {query_type} for more specific results."
        )


# =============================================================================
# Error Handling Utilities
# =============================================================================


class CodeGraphError(Exception):
    """Base exception for all weavr errors."""

    pass


class QueryTimeoutError(CodeGraphError):
    """Raised when a query exceeds the execution time limit."""

    def __init__(
        self, message: str, query: str = "", max_depth: int | None = None
    ) -> None:
        self.query = query
        self.max_depth = max_depth
        super().__init__(message)


class NodeNotFoundError(CodeGraphError):
    """Raised when a query target doesn't exist in the graph."""

    def __init__(self, qualified_name: str, node_type: str = "Node") -> None:
        self.qualified_name = qualified_name
        self.node_type = node_type
        message = f"{node_type} '{qualified_name}' not found in code graph."
        super().__init__(message)


class ConnectionError(CodeGraphError):
    """Raised when Memgraph connection fails or is lost."""

    pass


def create_error_response(
    error_type: str,
    message: str,
    suggestion: str | None = None,
    provided_input: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create standardized error response.

    Args:
        error_type: Error type code (e.g., "NODE_NOT_FOUND", "QUERY_TIMEOUT")
        message: Human-readable error message
        suggestion: Optional suggestion for resolving the error
        provided_input: Optional dict of user inputs that caused the error

    Returns:
        Formatted error response dictionary
    """
    response: dict[str, Any] = {
        "error": message,
        "error_code": error_type,
    }

    if suggestion:
        response["suggestion"] = suggestion

    if provided_input:
        response["provided_input"] = provided_input

    return response


def handle_node_not_found(
    qualified_name: str, node_type: str = "Function"
) -> dict[str, Any]:
    """Create user-friendly error for non-existent nodes.

    Args:
        qualified_name: The qualified name that wasn't found
        node_type: Type of node (Function, Class, Module, etc.)

    Returns:
        Error response dictionary
    """
    message = f"{node_type} '{qualified_name}' not found in code graph."

    suggestions = [
        "1. Verify the codebase has been indexed (run index_repository)",
        "2. Check qualified name format (e.g., 'module.ClassName.method_name')",
        "3. Use query_cypher to search by partial name: "
        f"MATCH (n:{node_type}) WHERE n.name CONTAINS '{qualified_name.split('.')[-1]}' "
        "RETURN n.qualified_name LIMIT 10",
    ]

    return create_error_response(
        error_type="NODE_NOT_FOUND",
        message=message,
        suggestion="\n".join(suggestions),
        provided_input={f"{node_type.lower()}_name": qualified_name},
    )


def handle_query_timeout(
    query: str, max_depth: int | None = None, timeout_sec: int = 10
) -> dict[str, Any]:
    """Create user-friendly error for query timeouts.

    Args:
        query: The query that timed out
        max_depth: Maximum depth parameter if applicable
        timeout_sec: Timeout threshold in seconds

    Returns:
        Error response dictionary
    """
    message = f"Query exceeded time limit ({timeout_sec} seconds)."

    suggestions = [
        "Possible reasons:",
        "1. max_depth is too large for this codebase (try reducing it)",
        "2. The query matches too many nodes (add more specific filters)",
        "3. The database is under heavy load",
        "",
        "Suggestions:",
    ]

    if max_depth and max_depth > 3:
        suggestions.append(f"- Reduce max_depth: Try max_depth={max_depth - 2} instead")
    suggestions.append("- Use more specific filters: Specify exact module or class names")
    suggestions.append(
        "- Check database health: Run 'docker stats' to verify Memgraph resource usage"
    )

    return create_error_response(
        error_type="QUERY_TIMEOUT",
        message=message,
        suggestion="\n".join(suggestions),
        provided_input={"query": query[:100] + "..." if len(query) > 100 else query},
    )


# =============================================================================
# Base Query Tool Class
# =============================================================================


@dataclass
class StructuralQueryTool:
    """Base class for all structural query tools.

    Provides common functionality for:
    - Result formatting
    - Error handling
    - Truncation logic
    - Performance logging
    """

    name: str
    description: str
    truncate_limit: int = 100

    def format_results(
        self,
        rows: list[dict[str, Any]],
        execution_time_ms: float,
        query_description: str = "",
    ) -> dict[str, Any]:
        """Format query results with metadata.

        Args:
            rows: Raw query results
            execution_time_ms: Query execution time
            query_description: Human-readable query description

        Returns:
            Formatted result dictionary
        """
        truncated_rows, was_truncated, total_count = apply_truncation(
            rows, self.truncate_limit, "prebuilt"
        )

        metadata = QueryMetadata(
            row_count=len(truncated_rows),
            total_count=total_count,
            truncated=was_truncated,
            execution_time_ms=round(execution_time_ms, 2),
            query_type="structural",
        )

        return {
            "query": query_description or self.description,
            "results": truncated_rows,
            "metadata": {
                "row_count": metadata.row_count,
                "total_count": metadata.total_count,
                "truncated": metadata.truncated,
                "execution_time_ms": metadata.execution_time_ms,
                "query_type": metadata.query_type,
            },
        }

    def handle_error(
        self, error: Exception, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Handle query errors with user-friendly messages.

        Args:
            error: The exception that occurred
            context: Optional context about the query

        Returns:
            Error response dictionary
        """
        if isinstance(error, NodeNotFoundError):
            return handle_node_not_found(error.qualified_name, error.node_type)
        elif isinstance(error, QueryTimeoutError):
            return handle_query_timeout(
                error.query, error.max_depth if hasattr(error, "max_depth") else None
            )
        else:
            logger.error(f"Unexpected error in {self.name}: {error}")
            return create_error_response(
                error_type="UNKNOWN_ERROR",
                message=f"An unexpected error occurred: {str(error)}",
                suggestion="Check the logs for more details or contact support.",
                provided_input=context,
            )


# =============================================================================
# User Story 1: Query Function Call Relationships
# =============================================================================


@dataclass
class FindCallersQuery(StructuralQueryTool):
    """Find all functions that call a specified target function.

    Supports both direct callers and multi-level call chains.
    """

    name: str = "find_callers"
    description: str = "Find all functions/methods that call a specified function"
    truncate_limit: int = 100

    def execute(
        self,
        ingestor: Any,
        function_name: str,
        max_depth: int = 1,
        include_paths: bool = True,
    ) -> dict[str, Any]:
        """Execute caller query.

        Args:
            ingestor: MemgraphIngestor instance
            function_name: Fully qualified function name to find callers for
            max_depth: Maximum depth for call chain traversal (1=direct only)
            include_paths: Whether to include file paths and line numbers

        Returns:
            Formatted result dictionary with callers and metadata
        """
        # Validate max_depth
        if max_depth < 1 or max_depth > 5:
            return create_error_response(
                error_type="INVALID_PARAMETER",
                message=f"max_depth must be between 1 and 5 (got {max_depth})",
                suggestion="Use max_depth=1 for direct callers, max_depth=2-3 for impact analysis",
                provided_input={"function_name": function_name, "max_depth": max_depth},
            )

        # Build query based on depth
        if max_depth == 1:
            # Direct callers only - simpler, faster query
            query = """
            MATCH (caller:Function|Method)-[:CALLS]->(target:Function|Method {qualified_name: $name})
            RETURN
                caller.qualified_name AS caller_name,
                caller.name AS short_name,
                labels(caller) AS type,
                caller.file_path AS file_path,
                caller.line_start AS line_number
            ORDER BY caller.qualified_name
            LIMIT 100
            """
            params = {"name": function_name}
        else:
            # Multi-hop callers with call chains
            query = f"""
            MATCH path = (caller:Function|Method)-[:CALLS*1..{max_depth}]->(target:Function|Method {{qualified_name: $name}})
            RETURN
                caller.qualified_name AS caller_name,
                caller.name AS short_name,
                labels(caller) AS type,
                caller.file_path AS file_path,
                caller.line_start AS line_number,
                length(path) AS depth,
                [node in nodes(path) | node.qualified_name] AS call_chain
            ORDER BY depth, caller_name
            LIMIT 100
            """
            params = {"name": function_name}

        try:
            # Execute query with performance logging
            results, execution_time_ms = ingestor.execute_structural_query(
                query, params, query_name=f"find_callers(depth={max_depth})"
            )

            # Check if target function exists
            if not results:
                # Verify if the function exists in the graph
                check_query = """
                MATCH (n:Function|Method {qualified_name: $name})
                RETURN n.qualified_name
                """
                exists = ingestor.fetch_all(check_query, {"name": function_name})
                if not exists:
                    raise NodeNotFoundError(function_name, "Function")

            # Format results
            formatted_results = []
            for row in results:
                result_item: dict[str, Any] = {
                    "caller": row["caller_name"],
                    "type": row["type"][0] if row["type"] else "Unknown",
                }

                if include_paths and row.get("file_path"):
                    result_item["file_path"] = row["file_path"]
                    if row.get("line_number"):
                        result_item["line_number"] = row["line_number"]

                if max_depth > 1 and "depth" in row:
                    result_item["depth"] = row["depth"]
                    if "call_chain" in row:
                        result_item["call_chain"] = row["call_chain"]

                formatted_results.append(result_item)

            query_desc = (
                f"Callers of {function_name}"
                + (f" (up to depth {max_depth})" if max_depth > 1 else "")
            )

            return self.format_results(formatted_results, execution_time_ms, query_desc)

        except NodeNotFoundError as e:
            return handle_node_not_found(e.qualified_name, e.node_type)
        except Exception as e:
            return self.handle_error(
                e, {"function_name": function_name, "max_depth": max_depth}
            )


def create_find_callers_tool(ingestor: Any) -> dict[str, Any]:
    """Create MCP tool for finding function callers.

    Args:
        ingestor: MemgraphIngestor instance

    Returns:
        Tool definition dictionary
    """
    query_tool = FindCallersQuery()

    async def find_callers(
        function_name: str, max_depth: int = 1, include_paths: bool = True
    ) -> dict[str, Any]:
        """Find all functions that call a specified target function.

        Args:
            function_name: Fully qualified name of the target function
            max_depth: Maximum depth for caller chain traversal (1=direct only, default: 1)
            include_paths: Whether to include file paths and line numbers (default: true)

        Returns:
            Dictionary containing callers and metadata
        """
        return query_tool.execute(ingestor, function_name, max_depth, include_paths)

    return {
        "name": "query_callers",
        "description": (
            "Find all functions/methods that call a specified function. "
            "Supports multi-level caller chains up to max_depth. "
            "Use this for impact analysis before refactoring or to understand function usage."
        ),
        "handler": find_callers,
        "input_schema": {
            "type": "object",
            "properties": {
                "function_name": {
                    "type": "string",
                    "description": "Fully qualified name of the function to find callers for (e.g., 'auth.services.login')",
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth for caller chain traversal. 1 = direct callers only, 2 = callers of callers, etc. (default: 1)",
                    "minimum": 1,
                    "maximum": 5,
                    "default": 1,
                },
                "include_paths": {
                    "type": "boolean",
                    "description": "Whether to include file paths and line numbers in results (default: true)",
                    "default": True,
                },
            },
            "required": ["function_name"],
        },
    }


# =============================================================================
# User Story 3: Analyze Module Dependencies
# =============================================================================


@dataclass
class DependencyAnalysisQuery(StructuralQueryTool):
    """Analyze module or function dependencies including imports and function calls."""

    name: str = "dependency_analysis"
    description: str = "Analyze module/function dependencies (imports, calls, or both)"
    truncate_limit: int = 100

    def execute(
        self,
        ingestor: Any,
        target: str,
        dependency_type: Literal["imports", "calls", "all"] = "all",
        include_transitive: bool = False,
    ) -> dict[str, Any]:
        """Execute dependency analysis query.

        Args:
            ingestor: MemgraphIngestor instance
            target: Qualified name of module or function to analyze
            dependency_type: Type of dependencies ('imports', 'calls', or 'all')
            include_transitive: Include transitive dependencies (dependencies of dependencies)

        Returns:
            Formatted result dictionary with dependencies and metadata
        """
        # Validate dependency_type parameter
        if dependency_type not in ("imports", "calls", "all"):
            return create_error_response(
                error_type="INVALID_PARAMETER",
                message=f'Invalid dependency_type parameter. Must be "imports", "calls", or "all" (got "{dependency_type}")',
                suggestion='Use dependency_type="all" to see complete dependencies',
                provided_input={"target": target, "dependency_type": dependency_type},
            )

        try:
            imports = []
            calls = []
            execution_times = []

            # Query import dependencies
            if dependency_type in ("imports", "all"):
                imports, import_exec_time = self._query_import_dependencies(
                    ingestor, target, include_transitive
                )
                execution_times.append(import_exec_time)

            # Query call dependencies
            if dependency_type in ("calls", "all"):
                calls, call_exec_time = self._query_call_dependencies(
                    ingestor, target, include_transitive
                )
                execution_times.append(call_exec_time)

            # Check if target exists if no results
            if not imports and not calls:
                check_query = """
                MATCH (n)
                WHERE n.qualified_name = $name
                  AND (n:Module OR n:Function OR n:Method OR n:Class)
                RETURN n.qualified_name, labels(n) AS type
                """
                exists = ingestor.fetch_all(check_query, {"name": target})
                if not exists:
                    raise NodeNotFoundError(target, "Module/Function")

            # Build dependency graph (adjacency list)
            dependency_graph = self._build_dependency_graph(target, imports, calls)

            # Categorize dependencies
            categorized_imports = self._categorize_dependencies(imports)
            categorized_calls = self._categorize_dependencies(calls)

            # Calculate total execution time
            total_exec_time = sum(execution_times) if execution_times else 0

            result = {
                "query": f"Dependencies of {target} (type: {dependency_type})",
                "imports": categorized_imports if dependency_type in ("imports", "all") else [],
                "calls": categorized_calls if dependency_type in ("calls", "all") else [],
                "dependency_graph": dependency_graph,
                "metadata": {
                    "row_count": len(imports) + len(calls),
                    "total_count": len(imports) + len(calls),
                    "truncated": False,
                    "execution_time_ms": round(total_exec_time, 2),
                    "query_type": "structural",
                    "include_transitive": include_transitive,
                },
            }

            return result

        except NodeNotFoundError as e:
            return handle_node_not_found(e.qualified_name, e.node_type)
        except Exception as e:
            return self.handle_error(
                e, {"target": target, "dependency_type": dependency_type}
            )

    def _query_import_dependencies(
        self, ingestor: Any, target: str, include_transitive: bool
    ) -> tuple[list[dict[str, Any]], float]:
        """Query import dependencies for a module or function.

        Args:
            ingestor: MemgraphIngestor instance
            target: Target module or function
            include_transitive: Include transitive imports

        Returns:
            Tuple of (import results list, execution time in ms)
        """
        if include_transitive:
            # Multi-hop import dependencies (use cautiously)
            query = """
            MATCH path = (source)-[:IMPORTS*1..3]->(imported)
            WHERE source.qualified_name = $target
              AND (source:Module OR source:Function OR source:Method)
              AND (imported:Module OR imported:ExternalPackage)
            RETURN
                imported.qualified_name AS dependency_name,
                labels(imported) AS dependency_type,
                imported.name AS short_name,
                length(path) AS depth,
                [node in nodes(path) | node.qualified_name] AS import_chain
            ORDER BY depth, dependency_name
            LIMIT 50
            """
        else:
            # Direct imports only
            query = """
            MATCH (source)-[:IMPORTS]->(imported)
            WHERE source.qualified_name = $target
              AND (source:Module OR source:Function OR source:Method)
              AND (imported:Module OR imported:ExternalPackage)
            RETURN
                imported.qualified_name AS dependency_name,
                labels(imported) AS dependency_type,
                imported.name AS short_name
            ORDER BY dependency_name
            LIMIT 100
            """

        results, exec_time = ingestor.execute_structural_query(
            query,
            {"target": target},
            query_name=f"dependency_analysis(imports, transitive={include_transitive})",
        )

        formatted_results = []
        for row in results:
            result_item: dict[str, Any] = {
                "dependency_name": row["dependency_name"],
                "short_name": row["short_name"],
                "dependency_type": row["dependency_type"][0] if row["dependency_type"] else "Unknown",
            }

            if include_transitive and "depth" in row:
                result_item["depth"] = row["depth"]
                if "import_chain" in row:
                    result_item["import_chain"] = row["import_chain"]

            formatted_results.append(result_item)

        return formatted_results, exec_time

    def _query_call_dependencies(
        self, ingestor: Any, target: str, include_transitive: bool
    ) -> tuple[list[dict[str, Any]], float]:
        """Query call dependencies for a function or method.

        Args:
            ingestor: MemgraphIngestor instance
            target: Target function or method
            include_transitive: Include transitive calls

        Returns:
            Tuple of (call results list, execution time in ms)
        """
        if include_transitive:
            # Multi-hop call dependencies
            query = """
            MATCH path = (source:Function|Method)-[:CALLS*1..3]->(called:Function|Method)
            WHERE source.qualified_name = $target
            RETURN
                called.qualified_name AS dependency_name,
                called.name AS short_name,
                labels(called) AS dependency_type,
                called.file_path AS file_path,
                length(path) AS depth,
                [node in nodes(path) | node.qualified_name] AS call_chain
            ORDER BY depth, dependency_name
            LIMIT 50
            """
        else:
            # Direct calls only
            query = """
            MATCH (source:Function|Method)-[:CALLS]->(called:Function|Method)
            WHERE source.qualified_name = $target
            RETURN
                called.qualified_name AS dependency_name,
                called.name AS short_name,
                labels(called) AS dependency_type,
                called.file_path AS file_path
            ORDER BY dependency_name
            LIMIT 100
            """

        results, exec_time = ingestor.execute_structural_query(
            query,
            {"target": target},
            query_name=f"dependency_analysis(calls, transitive={include_transitive})",
        )

        formatted_results = []
        for row in results:
            result_item: dict[str, Any] = {
                "dependency_name": row["dependency_name"],
                "short_name": row["short_name"],
                "dependency_type": row["dependency_type"][0] if row["dependency_type"] else "Unknown",
            }

            if row.get("file_path"):
                result_item["file_path"] = row["file_path"]

            if include_transitive and "depth" in row:
                result_item["depth"] = row["depth"]
                if "call_chain" in row:
                    result_item["call_chain"] = row["call_chain"]

            formatted_results.append(result_item)

        return formatted_results, exec_time

    def _build_dependency_graph(
        self, target: str, imports: list[dict[str, Any]], calls: list[dict[str, Any]]
    ) -> dict[str, list[str]]:
        """Build adjacency list representation of dependency graph.

        Args:
            target: Root node (target being analyzed)
            imports: List of import dependencies
            calls: List of call dependencies

        Returns:
            Adjacency list dictionary
        """
        all_dependencies = []

        for imp in imports:
            all_dependencies.append(imp["dependency_name"])

        for call in calls:
            all_dependencies.append(call["dependency_name"])

        return {target: all_dependencies}

    def _categorize_dependencies(
        self, dependencies: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Categorize dependencies as external libraries, internal modules, or standard library.

        Args:
            dependencies: List of dependency dictionaries

        Returns:
            Categorized dependencies with category field added
        """
        categorized = []

        for dep in dependencies:
            dep_copy = dep.copy()
            dep_type = dep_copy.get("dependency_type", "Unknown")
            dep_name = dep_copy.get("dependency_name", "")

            # Categorize based on type and name patterns
            if dep_type == "ExternalPackage":
                dep_copy["category"] = "external"
            elif self._is_standard_library(dep_name):
                dep_copy["category"] = "standard_library"
            else:
                dep_copy["category"] = "internal"

            categorized.append(dep_copy)

        return categorized

    def _is_standard_library(self, module_name: str) -> bool:
        """Check if a module is part of the Python standard library.

        Args:
            module_name: Module name to check

        Returns:
            True if standard library module, False otherwise
        """
        # Common Python standard library modules
        stdlib_modules = {
            "os", "sys", "io", "re", "json", "yaml", "csv", "xml", "html",
            "http", "urllib", "email", "datetime", "time", "calendar",
            "collections", "itertools", "functools", "operator",
            "pathlib", "typing", "dataclasses", "abc", "contextlib",
            "logging", "argparse", "subprocess", "threading", "multiprocessing",
            "asyncio", "concurrent", "queue", "socket", "ssl",
            "unittest", "pytest", "doctest", "pdb", "trace",
            "math", "random", "statistics", "decimal", "fractions",
            "string", "textwrap", "unicodedata", "struct", "codecs",
            "pickle", "shelve", "sqlite3", "dbm", "gzip", "bz2", "zipfile", "tarfile",
        }

        # Extract base module name (e.g., "os.path" -> "os")
        base_module = module_name.split(".")[0] if module_name else ""

        return base_module in stdlib_modules


def create_dependency_analysis_tool(ingestor: Any) -> dict[str, Any]:
    """Create MCP tool for analyzing dependencies.

    Args:
        ingestor: MemgraphIngestor instance

    Returns:
        Tool definition dictionary
    """
    query_tool = DependencyAnalysisQuery()

    async def dependency_analysis(
        target: str,
        dependency_type: Literal["imports", "calls", "all"] = "all",
        include_transitive: bool = False,
    ) -> dict[str, Any]:
        """Analyze module or function dependencies.

        Args:
            target: Qualified name of module or function to analyze
            dependency_type: Type of dependencies ('imports', 'calls', or 'all')
            include_transitive: Include transitive dependencies (default: false)

        Returns:
            Dictionary containing dependencies and metadata
        """
        return query_tool.execute(ingestor, target, dependency_type, include_transitive)

    return {
        "name": "query_dependencies",
        "description": (
            "Analyze module or function dependencies including imports and function calls. "
            "Use this for module extraction planning, understanding coupling, and dependency auditing. "
            "Supports both direct dependencies and transitive dependencies (dependencies of dependencies)."
        ),
        "handler": dependency_analysis,
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Qualified name of module or function to analyze (e.g., 'auth.services' or 'payment.processor.process_payment')",
                },
                "dependency_type": {
                    "type": "string",
                    "enum": ["imports", "calls", "all"],
                    "description": "Type of dependencies to retrieve: 'imports' for module imports, 'calls' for function calls, 'all' for both (default: 'all')",
                    "default": "all",
                },
                "include_transitive": {
                    "type": "boolean",
                    "description": "Include transitive dependencies (dependencies of dependencies). Use cautiously as this can generate large result sets. (default: false)",
                    "default": False,
                },
            },
            "required": ["target"],
        },
    }


# =============================================================================
# User Story 4: Find Interface Implementations
# =============================================================================


@dataclass
class InterfaceImplementationsQuery(StructuralQueryTool):
    """Find all classes that implement a specified interface or extend a base class."""

    name: str = "interface_implementations"
    description: str = "Find all classes that implement a given interface or extend a base class"
    truncate_limit: int = 100

    def execute(
        self,
        ingestor: Any,
        interface_name: str,
        include_indirect: bool = False,
    ) -> dict[str, Any]:
        """Execute interface implementations query.

        Args:
            ingestor: MemgraphIngestor instance
            interface_name: Fully qualified name of interface or base class
            include_indirect: Include indirect implementations (child classes of implementers)

        Returns:
            Formatted result dictionary with implementations and metadata
        """
        try:
            implementations = []
            execution_times = []

            # Query IMPLEMENTS relationships (direct interface implementations)
            implements_results, implements_exec_time = self._query_implements(
                ingestor, interface_name, include_indirect
            )
            execution_times.append(implements_exec_time)
            implementations.extend(implements_results)

            # Query INHERITS relationships (base class extensions) as fallback
            inherits_results, inherits_exec_time = self._query_inherits(
                ingestor, interface_name, include_indirect
            )
            execution_times.append(inherits_exec_time)
            implementations.extend(inherits_results)

            # Remove duplicates (in case a class appears in both IMPLEMENTS and INHERITS)
            unique_implementations = self._deduplicate_implementations(implementations)

            # Check if interface/base class exists if no results
            if not unique_implementations:
                check_query = """
                MATCH (n:Class {qualified_name: $name})
                RETURN n.qualified_name
                """
                exists = ingestor.fetch_all(check_query, {"name": interface_name})
                if not exists:
                    raise NodeNotFoundError(interface_name, "Interface/Class")

            # Build inheritance depth mapping
            inheritance_depth = {
                impl["class_name"]: impl["depth"]
                for impl in unique_implementations
            }

            # Calculate total execution time
            total_exec_time = sum(execution_times) if execution_times else 0

            result = {
                "query": f"Implementations of {interface_name}",
                "implementations": unique_implementations,
                "inheritance_depth": inheritance_depth,
                "metadata": {
                    "row_count": len(unique_implementations),
                    "total_count": len(unique_implementations),
                    "truncated": False,
                    "execution_time_ms": round(total_exec_time, 2),
                    "query_type": "structural",
                    "include_indirect": include_indirect,
                },
            }

            return result

        except NodeNotFoundError as e:
            return handle_node_not_found(e.qualified_name, e.node_type)
        except Exception as e:
            return self.handle_error(
                e, {"interface_name": interface_name, "include_indirect": include_indirect}
            )

    def _query_implements(
        self, ingestor: Any, interface_name: str, include_indirect: bool
    ) -> tuple[list[dict[str, Any]], float]:
        """Query IMPLEMENTS relationships for interface implementations.

        Args:
            ingestor: MemgraphIngestor instance
            interface_name: Interface name to find implementations for
            include_indirect: Include indirect implementations

        Returns:
            Tuple of (implementation results list, execution time in ms)
        """
        if include_indirect:
            # Multi-hop IMPLEMENTS relationships (indirect implementations)
            query = """
            MATCH path = (impl:Class)-[:IMPLEMENTS*1..10]->(interface:Class {qualified_name: $name})
            RETURN
                impl.qualified_name AS class_name,
                impl.name AS short_name,
                impl.file_path AS file_path,
                impl.line_start AS line_start,
                length(path) AS depth
            ORDER BY depth, class_name
            LIMIT 100
            """
        else:
            # Direct IMPLEMENTS relationships only
            query = """
            MATCH (impl:Class)-[:IMPLEMENTS]->(interface:Class {qualified_name: $name})
            RETURN
                impl.qualified_name AS class_name,
                impl.name AS short_name,
                impl.file_path AS file_path,
                impl.line_start AS line_start,
                1 AS depth
            ORDER BY class_name
            LIMIT 100
            """

        results, exec_time = ingestor.execute_structural_query(
            query,
            {"name": interface_name},
            query_name=f"interface_implementations(IMPLEMENTS, indirect={include_indirect})",
        )

        formatted_results = []
        for row in results:
            result_item: dict[str, Any] = {
                "class_name": row["class_name"],
                "short_name": row["short_name"],
                "depth": row["depth"],
            }

            if row.get("file_path"):
                result_item["file_path"] = row["file_path"]
            if row.get("line_start"):
                result_item["line_start"] = row["line_start"]

            formatted_results.append(result_item)

        return formatted_results, exec_time

    def _query_inherits(
        self, ingestor: Any, interface_name: str, include_indirect: bool
    ) -> tuple[list[dict[str, Any]], float]:
        """Query INHERITS relationships as fallback for base class extensions.

        Args:
            ingestor: MemgraphIngestor instance
            interface_name: Base class name to find extensions for
            include_indirect: Include indirect inheritances

        Returns:
            Tuple of (inheritance results list, execution time in ms)
        """
        if include_indirect:
            # Multi-hop INHERITS relationships (deep inheritance)
            query = """
            MATCH path = (child:Class)-[:INHERITS*1..10]->(parent:Class {qualified_name: $name})
            RETURN
                child.qualified_name AS class_name,
                child.name AS short_name,
                child.file_path AS file_path,
                child.line_start AS line_start,
                length(path) AS depth
            ORDER BY depth, class_name
            LIMIT 100
            """
        else:
            # Direct INHERITS relationships only
            query = """
            MATCH (child:Class)-[:INHERITS]->(parent:Class {qualified_name: $name})
            RETURN
                child.qualified_name AS class_name,
                child.name AS short_name,
                child.file_path AS file_path,
                child.line_start AS line_start,
                1 AS depth
            ORDER BY class_name
            LIMIT 100
            """

        results, exec_time = ingestor.execute_structural_query(
            query,
            {"name": interface_name},
            query_name=f"interface_implementations(INHERITS, indirect={include_indirect})",
        )

        formatted_results = []
        for row in results:
            result_item: dict[str, Any] = {
                "class_name": row["class_name"],
                "short_name": row["short_name"],
                "depth": row["depth"],
            }

            if row.get("file_path"):
                result_item["file_path"] = row["file_path"]
            if row.get("line_start"):
                result_item["line_start"] = row["line_start"]

            formatted_results.append(result_item)

        return formatted_results, exec_time

    def _deduplicate_implementations(
        self, implementations: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Remove duplicate implementations (same class appearing multiple times).

        Args:
            implementations: List of implementation dictionaries

        Returns:
            Deduplicated list (keeping the entry with smallest depth)
        """
        # Use dict to track unique implementations by class_name
        unique: dict[str, dict[str, Any]] = {}

        for impl in implementations:
            class_name = impl["class_name"]

            # Keep the implementation with the smallest depth
            if class_name not in unique or impl["depth"] < unique[class_name]["depth"]:
                unique[class_name] = impl

        # Return as sorted list
        return sorted(unique.values(), key=lambda x: (x["depth"], x["class_name"]))


def create_interface_implementations_tool(ingestor: Any) -> dict[str, Any]:
    """Create MCP tool for finding interface implementations.

    Args:
        ingestor: MemgraphIngestor instance

    Returns:
        Tool definition dictionary
    """
    query_tool = InterfaceImplementationsQuery()

    async def interface_implementations(
        interface_name: str,
        include_indirect: bool = False,
    ) -> dict[str, Any]:
        """Find all classes that implement an interface or extend a base class.

        Args:
            interface_name: Fully qualified name of interface or base class
            include_indirect: Include indirect implementations (default: false)

        Returns:
            Dictionary containing implementations and metadata
        """
        return query_tool.execute(ingestor, interface_name, include_indirect)

    return {
        "name": "query_implementations",
        "description": (
            "Find all classes that implement a specified interface or extend a base class. "
            "Use this for finding all implementations of an interface, ensuring consistent behavior "
            "across implementers, or identifying all subclasses before refactoring a base class. "
            "Searches both IMPLEMENTS relationships (interface implementations) and INHERITS relationships (base class extensions)."
        ),
        "handler": interface_implementations,
        "input_schema": {
            "type": "object",
            "properties": {
                "interface_name": {
                    "type": "string",
                    "description": "Fully qualified name of interface or base class (e.g., 'auth.interfaces.PaymentProvider' or 'models.BaseModel')",
                },
                "include_indirect": {
                    "type": "boolean",
                    "description": "Include indirect implementations (child classes of implementers). Use cautiously with deep inheritance trees. (default: false)",
                    "default": False,
                },
            },
            "required": ["interface_name"],
        },
    }


# =============================================================================
# User Story 5: Execute Custom Graph Queries (Expert Mode)
# =============================================================================

# Graph schema documentation for expert users
GRAPH_SCHEMA_DOC = """
## Code-Graph-RAG Schema Reference

### Node Types
- **Project**: Project container (name) - for project isolation
- **Module**: Code module/file (qualified_name, name, path, extension)
- **Package**: Code package/directory (qualified_name, name, path)
- **Class**: Class definition (qualified_name, name, file_path, line_start, line_end, base_classes)
- **Function**: Standalone function (qualified_name, name, file_path, line_start, line_end, decorators)
- **Method**: Class method (qualified_name, name, class_name, file_path, line_start, line_end, decorators)
- **File**: Source file (path, name, extension)
- **ExternalPackage**: Third-party package (name)

### Relationship Types
- **CONTAINS**: Project → * (project isolation - all nodes belong to a project)
- **DEFINES**: Module → Function|Class|Method (module defines code entities)
- **CALLS**: Function|Method → Function|Method (function/method calls another)
- **INHERITS**: Class → Class (class inherits from parent class)
- **IMPLEMENTS**: Class → Class (class implements interface)
- **IMPORTS**: Module|Function → Module|ExternalPackage (import dependency)

### Example Queries

Find functions with specific decorator:
```cypher
MATCH (f:Function)
WHERE 'dataclass' IN f.decorators
RETURN f.qualified_name, f.file_path
LIMIT 50;
```

Find most-called functions:
```cypher
MATCH (caller)-[:CALLS]->(callee:Function)
RETURN callee.qualified_name, count(caller) AS call_count
ORDER BY call_count DESC
LIMIT 10;
```

Find circular dependencies:
```cypher
MATCH path = (c:Class)-[:INHERITS*]->(c)
RETURN c.qualified_name, length(path) AS cycle_length
ORDER BY cycle_length;
```

Cross-module function calls:
```cypher
MATCH (m1:Module)-[:DEFINES]->(f1:Function)-[:CALLS]->(f2:Function)<-[:DEFINES]-(m2:Module)
WHERE m1.qualified_name <> m2.qualified_name
RETURN m1.qualified_name AS from_module, m2.qualified_name AS to_module, count(*) AS call_count
ORDER BY call_count DESC
LIMIT 20;
```
"""


@dataclass
class ExpertModeQuery(StructuralQueryTool):
    """Execute custom Cypher queries against the code knowledge graph (expert mode)."""

    name: str = "expert_mode_cypher"
    description: str = "Execute custom Cypher queries for advanced graph analysis"
    truncate_limit: int = 50  # Expert mode uses smaller default limit

    def execute(
        self,
        ingestor: Any,
        query: str,
        parameters: dict[str, Any] | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Execute expert-mode Cypher query.

        Args:
            ingestor: MemgraphIngestor instance
            query: Cypher query string
            parameters: Query parameters for parameterized queries
            limit: Maximum number of rows to return (1-1000)

        Returns:
            Formatted result dictionary with query results and metadata
        """
        # Validate limit
        if limit < 1 or limit > 1000:
            return create_error_response(
                error_type="INVALID_PARAMETER",
                message=f"limit must be between 1 and 1000 (got {limit})",
                suggestion="Use smaller limit values to avoid overwhelming results. Default is 50.",
                provided_input={"query": query[:100], "limit": limit},
            )

        # Validate query is not empty
        if not query or not query.strip():
            return create_error_response(
                error_type="INVALID_QUERY",
                message="Query cannot be empty",
                suggestion="Provide a valid Cypher query. See schema documentation for examples.",
                provided_input={"query": query},
            )

        # Sanitize query (basic validation)
        validation_error = self._validate_cypher_query(query)
        if validation_error:
            return validation_error

        try:
            # Set parameters default
            params = parameters or {}

            # Execute query with performance logging
            results, execution_time_ms = ingestor.execute_structural_query(
                query, params, query_name="expert_mode_cypher"
            )

            # Extract column names from first result if available
            columns = list(results[0].keys()) if results else []

            # Apply truncation
            truncated_results, was_truncated, total_count = apply_truncation(
                results, limit, "expert"
            )

            # Format results
            result = {
                "query": query,
                "rows": truncated_results,
                "columns": columns,
                "row_count": len(truncated_results),
                "truncated": was_truncated,
                "metadata": {
                    "row_count": len(truncated_results),
                    "total_count": total_count,
                    "truncated": was_truncated,
                    "execution_time_ms": round(execution_time_ms, 2),
                    "query_type": "expert_cypher",
                    "limit_applied": limit,
                },
            }

            # Add truncation message if applicable
            if was_truncated:
                result["truncation_message"] = create_truncation_message(
                    len(truncated_results), total_count, "expert query"
                )

            return result

        except Exception as e:
            # Check for timeout errors
            error_msg = str(e).lower()
            if "timeout" in error_msg or "exceeded" in error_msg:
                return handle_query_timeout(query, max_depth=None, timeout_sec=10)
            else:
                return self.handle_error(
                    e, {"query": query[:100] + "..." if len(query) > 100 else query}
                )

    def _validate_cypher_query(self, query: str) -> dict[str, Any] | None:
        """Validate and sanitize Cypher query.

        Args:
            query: Cypher query string to validate

        Returns:
            Error response dict if validation fails, None if valid
        """
        query_upper = query.upper().strip()

        # Prevent CREATE operations (check before other CREATE variants)
        # Must check for plain CREATE before checking CREATE INDEX/CONSTRAINT
        if "CREATE" in query_upper and "CREATE INDEX" not in query_upper and "CREATE CONSTRAINT" not in query_upper:
            return create_error_response(
                error_type="FORBIDDEN_OPERATION",
                message="Destructive operation 'CREATE' is not allowed in expert mode",
                suggestion="Expert mode is read-only. Use MATCH, RETURN, WHERE, ORDER BY, LIMIT for queries.",
                provided_input={"query": query[:100]},
            )

        # Prevent destructive operations
        destructive_keywords = ["DELETE", "DETACH DELETE", "DROP", "CREATE INDEX", "CREATE CONSTRAINT"]
        for keyword in destructive_keywords:
            if keyword in query_upper:
                return create_error_response(
                    error_type="FORBIDDEN_OPERATION",
                    message=f"Destructive operation '{keyword}' is not allowed in expert mode",
                    suggestion="Expert mode is read-only. Use MATCH, RETURN, WHERE, ORDER BY, LIMIT for queries.",
                    provided_input={"query": query[:100]},
                )

        # Warn about queries without LIMIT (not an error, but a warning in response)
        if "LIMIT" not in query_upper:
            logger.warning(f"Expert query without LIMIT clause: {query[:50]}...")
            # Not returning error - just logging warning

        # Prevent SET operations (data modification)
        if " SET " in query_upper:
            return create_error_response(
                error_type="FORBIDDEN_OPERATION",
                message="SET operations are not allowed in expert mode (read-only)",
                suggestion="Use MATCH and RETURN to query the graph. Modifications are not permitted.",
                provided_input={"query": query[:100]},
            )

        # Prevent MERGE operations (can create nodes)
        if "MERGE" in query_upper:
            return create_error_response(
                error_type="FORBIDDEN_OPERATION",
                message="MERGE operations are not allowed in expert mode (read-only)",
                suggestion="Use MATCH to find existing nodes. Node creation is not permitted.",
                provided_input={"query": query[:100]},
            )

        return None  # Valid query

    def get_schema_documentation(self) -> str:
        """Get graph schema documentation for expert users.

        Returns:
            Formatted schema documentation string
        """
        return GRAPH_SCHEMA_DOC


def create_expert_mode_tool(ingestor: Any) -> dict[str, Any]:
    """Create MCP tool for expert-mode Cypher queries.

    Args:
        ingestor: MemgraphIngestor instance

    Returns:
        Tool definition dictionary
    """
    query_tool = ExpertModeQuery()

    async def expert_mode_cypher(
        query: str,
        parameters: dict[str, Any] | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Execute a custom Cypher query against the code knowledge graph.

        Args:
            query: Cypher query string
            parameters: Query parameters for parameterized queries (default: {})
            limit: Maximum number of rows to return (default: 50, max: 1000)

        Returns:
            Dictionary containing query results and metadata
        """
        return query_tool.execute(ingestor, query, parameters, limit)

    return {
        "name": "query_cypher",
        "description": (
            "Execute a custom Cypher query against the code knowledge graph (expert mode). "
            "Requires knowledge of the graph schema (see schema_documentation below). "
            "\n\n"
            "For simple queries like finding callers, exploring hierarchies, or analyzing dependencies, "
            "prefer the pre-built query tools which are optimized and easier to use:\n"
            "- query_callers: Find function callers\n"
            "- query_hierarchy: Explore class hierarchies\n"
            "- query_dependencies: Analyze module/function dependencies\n"
            "- query_implementations: Find interface implementations\n"
            "- query_call_graph: Generate call graphs\n"
            "\n\n"
            f"**Graph Schema Documentation**:\n{GRAPH_SCHEMA_DOC}"
        ),
        "handler": expert_mode_cypher,
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Cypher query string. Example: 'MATCH (f:Function) WHERE f.name CONTAINS $pattern RETURN f.qualified_name LIMIT 10'",
                },
                "parameters": {
                    "type": "object",
                    "description": "Query parameters for parameterized queries. Example: {'pattern': 'login'} (default: {})",
                    "default": {},
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of rows to return. Results will be truncated if exceeded. (default: 50, max: 1000)",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 1000,
                },
            },
            "required": ["query"],
        },
    }


# =============================================================================
# User Story 6: Generate Call Graph Visualizations
# =============================================================================


@dataclass
class CallGraphGeneratorQuery(StructuralQueryTool):
    """Generate call graphs starting from an entry point function."""

    name: str = "call_graph_generator"
    description: str = "Generate call graphs from an entry point with configurable depth"
    truncate_limit: int = 100

    def execute(
        self,
        ingestor: Any,
        entry_point: str,
        max_depth: int = 3,
        max_nodes: int = 50,
    ) -> dict[str, Any]:
        """Execute call graph generation query.

        Args:
            ingestor: MemgraphIngestor instance
            entry_point: Fully qualified name of entry point function
            max_depth: Maximum depth to traverse call graph (1-5)
            max_nodes: Maximum number of nodes to return (1-100)

        Returns:
            Formatted result dictionary with call graph nodes, edges, and metadata
        """
        # Validate parameters
        if max_depth < 1 or max_depth > 5:
            return create_error_response(
                error_type="INVALID_PARAMETER",
                message=f"max_depth must be between 1 and 5 (got {max_depth})",
                suggestion="Use max_depth=3 for typical call graphs. Higher values can exponentially increase result size.",
                provided_input={"entry_point": entry_point, "max_depth": max_depth},
            )

        if max_nodes < 1 or max_nodes > 100:
            return create_error_response(
                error_type="INVALID_PARAMETER",
                message=f"max_nodes must be between 1 and 100 (got {max_nodes})",
                suggestion="Use max_nodes=50 for balanced detail. Increase cautiously for larger graphs.",
                provided_input={"entry_point": entry_point, "max_nodes": max_nodes},
            )

        try:
            # Query for call graph (multi-hop CALLS traversal)
            query = f"""
            MATCH path = (entry:Function|Method {{qualified_name: $entry_point}})-[:CALLS*1..{max_depth}]->(called:Function|Method)
            RETURN
                entry.qualified_name AS entry_name,
                called.qualified_name AS called_name,
                called.name AS short_name,
                labels(called) AS node_type,
                called.file_path AS file_path,
                called.line_start AS line_number,
                length(path) AS depth,
                relationships(path) AS edges
            ORDER BY depth, called_name
            LIMIT 200
            """

            results, execution_time_ms = ingestor.execute_structural_query(
                query,
                {"entry_point": entry_point},
                query_name=f"call_graph_generator(depth={max_depth})",
            )

            # Check if entry point exists
            if not results:
                check_query = """
                MATCH (n:Function|Method {qualified_name: $entry_point})
                RETURN n.qualified_name
                """
                exists = ingestor.fetch_all(check_query, {"entry_point": entry_point})
                if not exists:
                    raise NodeNotFoundError(entry_point, "Function/Method")
                # Entry point exists but has no outgoing calls
                # Return minimal graph with just entry point
                return self._create_empty_graph_result(
                    entry_point, execution_time_ms, max_depth
                )

            # Extract nodes and edges from results
            nodes, edges = self._extract_nodes_and_edges(results, entry_point)

            # Apply node truncation
            truncated_nodes, was_truncated, total_node_count = self._truncate_nodes(
                nodes, max_nodes
            )

            # Filter edges to only include those between remaining nodes
            node_ids = {node["id"] for node in truncated_nodes}
            filtered_edges = [
                edge for edge in edges
                if edge["from"] in node_ids and edge["to"] in node_ids
            ]

            result = {
                "query": f"Call graph from {entry_point} (max_depth={max_depth})",
                "nodes": truncated_nodes,
                "edges": filtered_edges,
                "truncated": was_truncated,
                "total_nodes": total_node_count,
                "metadata": {
                    "row_count": len(truncated_nodes),
                    "total_count": total_node_count,
                    "truncated": was_truncated,
                    "execution_time_ms": round(execution_time_ms, 2),
                    "query_type": "structural",
                    "max_depth": max_depth,
                },
            }

            # Add truncation warning if applicable
            if was_truncated:
                result["truncation_message"] = (
                    f"Graph truncated to {len(truncated_nodes)} nodes "
                    f"(of {total_node_count} total). "
                    f"Consider reducing max_depth or using more specific entry point."
                )

            return result

        except NodeNotFoundError as e:
            return handle_node_not_found(e.qualified_name, e.node_type)
        except Exception as e:
            return self.handle_error(
                e, {"entry_point": entry_point, "max_depth": max_depth, "max_nodes": max_nodes}
            )

    def _extract_nodes_and_edges(
        self, results: list[dict[str, Any]], entry_point: str
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Extract unique nodes and edges from query results.

        Args:
            results: Query result rows
            entry_point: Entry point function name

        Returns:
            Tuple of (nodes list, edges list)
        """
        nodes_dict: dict[str, dict[str, Any]] = {}
        edges_list: list[dict[str, Any]] = []

        # Add entry point as a node
        if results:
            first_result = results[0]
            nodes_dict[entry_point] = {
                "id": entry_point,
                "name": entry_point.split(".")[-1],  # Extract short name
                "type": "Function",  # We'll update this if we find it in results
            }

        # Process all results
        for row in results:
            called_name = row["called_name"]

            # Add called node if not already present
            if called_name not in nodes_dict:
                node_info: dict[str, Any] = {
                    "id": called_name,
                    "name": row["short_name"],
                    "type": row["node_type"][0] if row["node_type"] else "Function",
                }

                if row.get("file_path"):
                    node_info["file_path"] = row["file_path"]
                if row.get("line_number"):
                    node_info["line_number"] = row["line_number"]

                nodes_dict[called_name] = node_info

            # Extract edges from path
            # For simplicity, we'll create edges based on the path traversal
            # The path goes from entry_point to called_name
            # We need to extract individual hops

        # Build edges from the query results
        # Each result represents a path, we need to reconstruct the edges
        edges_seen: set[tuple[str, str]] = set()

        for row in results:
            # The path is from entry_point to called_name
            # We can infer edges from depth and the call chain
            # For now, create a direct edge (simplified)
            caller = row["entry_name"]
            callee = row["called_name"]

            edge_key = (caller, callee)
            if edge_key not in edges_seen:
                edges_list.append({
                    "from": caller,
                    "to": callee,
                    "call_type": "direct",  # We don't have enough info to determine exact type
                })
                edges_seen.add(edge_key)

        # Convert nodes dict to list
        nodes_list = list(nodes_dict.values())

        return nodes_list, edges_list

    def _truncate_nodes(
        self, nodes: list[dict[str, Any]], max_nodes: int
    ) -> tuple[list[dict[str, Any]], bool, int]:
        """Truncate nodes list to max_nodes.

        Args:
            nodes: List of node dictionaries
            max_nodes: Maximum nodes to keep

        Returns:
            Tuple of (truncated nodes, was_truncated, total_count)
        """
        total_count = len(nodes)
        was_truncated = total_count > max_nodes

        if was_truncated:
            # Keep the first max_nodes nodes
            return nodes[:max_nodes], True, total_count
        else:
            return nodes, False, total_count

    def _create_empty_graph_result(
        self, entry_point: str, execution_time_ms: float, max_depth: int
    ) -> dict[str, Any]:
        """Create result for entry point with no outgoing calls.

        Args:
            entry_point: Entry point function name
            execution_time_ms: Query execution time
            max_depth: Max depth parameter

        Returns:
            Formatted result dictionary
        """
        return {
            "query": f"Call graph from {entry_point} (max_depth={max_depth})",
            "nodes": [
                {
                    "id": entry_point,
                    "name": entry_point.split(".")[-1],
                    "type": "Function",
                }
            ],
            "edges": [],
            "truncated": False,
            "total_nodes": 1,
            "metadata": {
                "row_count": 1,
                "total_count": 1,
                "truncated": False,
                "execution_time_ms": round(execution_time_ms, 2),
                "query_type": "structural",
                "max_depth": max_depth,
            },
        }


def create_call_graph_tool(ingestor: Any) -> dict[str, Any]:
    """Create MCP tool for call graph generation.

    Args:
        ingestor: MemgraphIngestor instance

    Returns:
        Tool definition dictionary
    """
    query_tool = CallGraphGeneratorQuery()

    async def call_graph_generator(
        entry_point: str,
        max_depth: int = 3,
        max_nodes: int = 50,
    ) -> dict[str, Any]:
        """Generate a call graph starting from an entry point function.

        Args:
            entry_point: Fully qualified name of entry point function
            max_depth: Maximum depth to traverse (default: 3, max: 5)
            max_nodes: Maximum number of nodes to return (default: 50, max: 100)

        Returns:
            Dictionary containing call graph nodes, edges, and metadata
        """
        return query_tool.execute(ingestor, entry_point, max_depth, max_nodes)

    return {
        "name": "query_call_graph",
        "description": (
            "Generate a call graph starting from an entry point function, showing all called functions up to max_depth. "
            "Use this to visualize execution flow, understand program structure, and trace function call paths. "
            "Returns nodes (functions/methods) and edges (call relationships) suitable for graph visualization. "
            "Note: Higher max_depth values exponentially increase result size."
        ),
        "handler": call_graph_generator,
        "input_schema": {
            "type": "object",
            "properties": {
                "entry_point": {
                    "type": "string",
                    "description": "Fully qualified name of the entry point function (e.g., 'app.main' or 'services.UserService.process_request')",
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth to traverse call graph. Higher values exponentially increase result size. (default: 3, max: 5)",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 5,
                },
                "max_nodes": {
                    "type": "integer",
                    "description": "Maximum number of nodes to return. Graph will be truncated if exceeded. (default: 50, max: 100)",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 100,
                },
            },
            "required": ["entry_point"],
        },
    }


# =============================================================================
# User Story 2: Explore Class Inheritance Hierarchies
# =============================================================================


@dataclass
class ClassHierarchyQuery(StructuralQueryTool):
    """Explore class inheritance hierarchies showing ancestors, descendants, or both."""

    name: str = "class_hierarchy"
    description: str = "Explore class inheritance hierarchies (ancestors, descendants, or both)"
    truncate_limit: int = 100

    def execute(
        self,
        ingestor: Any,
        class_name: str,
        direction: Literal["up", "down", "both"] = "both",
        max_depth: int = 10,
    ) -> dict[str, Any]:
        """Execute class hierarchy query.

        Args:
            ingestor: MemgraphIngestor instance
            class_name: Fully qualified class name
            direction: Traversal direction ('up'=ancestors, 'down'=descendants, 'both')
            max_depth: Maximum hierarchy depth to traverse

        Returns:
            Formatted result dictionary with hierarchy and metadata
        """
        # Validate direction parameter
        if direction not in ("up", "down", "both"):
            return create_error_response(
                error_type="INVALID_PARAMETER",
                message=f'Invalid direction parameter. Must be "up", "down", or "both" (got "{direction}")',
                suggestion='Use direction="both" to see complete hierarchy',
                provided_input={"class_name": class_name, "direction": direction},
            )

        # Validate parameters
        if max_depth < 1 or max_depth > 10:
            return create_error_response(
                error_type="INVALID_PARAMETER",
                message=f"max_depth must be between 1 and 10 (got {max_depth})",
                suggestion="Use max_depth=5 for typical hierarchies",
                provided_input={"class_name": class_name, "max_depth": max_depth},
            )

        try:
            ancestors = []
            descendants = []
            execution_times = []

            # Query ancestors (parent classes)
            if direction in ("up", "both"):
                ancestor_query = f"""
                MATCH path = (child:Class {{qualified_name: $name}})-[:INHERITS*1..{max_depth}]->(ancestor:Class)
                RETURN
                    ancestor.qualified_name AS ancestor_name,
                    ancestor.name AS short_name,
                    length(path) AS depth,
                    [node in nodes(path)[1..] | node.name] AS inheritance_chain
                ORDER BY depth
                LIMIT 20
                """
                ancestor_results, exec_time = ingestor.execute_structural_query(
                    ancestor_query, {"name": class_name}, query_name="class_hierarchy(ancestors)"
                )
                execution_times.append(exec_time)
                ancestors = [
                    {
                        "class_name": row["ancestor_name"],
                        "short_name": row["short_name"],
                        "depth": row["depth"],
                        "inheritance_chain": row.get("inheritance_chain", []),
                    }
                    for row in ancestor_results
                ]

            # Query descendants (child classes)
            if direction in ("down", "both"):
                descendant_query = f"""
                MATCH path = (parent:Class {{qualified_name: $name}})<-[:INHERITS*1..{max_depth}]-(descendant:Class)
                RETURN
                    descendant.qualified_name AS descendant_name,
                    descendant.name AS short_name,
                    length(path) AS depth
                ORDER BY depth
                LIMIT 50
                """
                descendant_results, exec_time = ingestor.execute_structural_query(
                    descendant_query, {"name": class_name}, query_name="class_hierarchy(descendants)"
                )
                execution_times.append(exec_time)
                descendants = [
                    {
                        "class_name": row["descendant_name"],
                        "short_name": row["short_name"],
                        "depth": row["depth"],
                    }
                    for row in descendant_results
                ]

            # Check if class exists if no results
            if not ancestors and not descendants:
                check_query = """
                MATCH (n:Class {qualified_name: $name})
                RETURN n.qualified_name
                """
                exists = ingestor.fetch_all(check_query, {"name": class_name})
                if not exists:
                    raise NodeNotFoundError(class_name, "Class")

            # Check for circular dependencies
            circular_deps = self._detect_circular_inheritance(ingestor, class_name)

            # Build hierarchy tree structure
            hierarchy_tree = self._build_hierarchy_tree(class_name, ancestors, descendants, direction)

            # Prepare warnings
            warnings = []
            if circular_deps:
                warnings.append(
                    f"⚠️  Circular inheritance detected: {' → '.join(circular_deps)}"
                )

            # Calculate total execution time
            total_exec_time = sum(execution_times) if execution_times else 0

            result = {
                "query": f"Class hierarchy for {class_name} (direction: {direction})",
                "hierarchy_tree": hierarchy_tree,
                "ancestors": ancestors if direction in ("up", "both") else [],
                "descendants": descendants if direction in ("down", "both") else [],
                "circular_dependencies": circular_deps,
                "warnings": warnings,
                "metadata": {
                    "row_count": len(ancestors) + len(descendants),
                    "total_count": len(ancestors) + len(descendants),
                    "truncated": False,
                    "execution_time_ms": round(total_exec_time, 2),
                    "query_type": "structural",
                    "max_depth": max_depth,
                },
            }

            return result

        except NodeNotFoundError as e:
            return handle_node_not_found(e.qualified_name, e.node_type)
        except Exception as e:
            return self.handle_error(
                e, {"class_name": class_name, "direction": direction, "max_depth": max_depth}
            )

    def _detect_circular_inheritance(self, ingestor: Any, class_name: str) -> list[str]:
        """Detect circular inheritance patterns.

        Args:
            ingestor: MemgraphIngestor instance
            class_name: Class to check for circular inheritance

        Returns:
            List of class names forming a cycle, or empty list if no cycle
        """
        try:
            circular_query = """
            MATCH path = (c:Class {qualified_name: $name})-[:INHERITS*]->(c)
            RETURN [node in nodes(path) | node.qualified_name] AS cycle
            LIMIT 1
            """
            results = ingestor.fetch_all(circular_query, {"name": class_name})
            if results and results[0].get("cycle"):
                return results[0]["cycle"]
            return []
        except Exception:
            return []

    def _build_hierarchy_tree(
        self,
        root_name: str,
        ancestors: list[dict[str, Any]],
        descendants: list[dict[str, Any]],
        direction: str,
    ) -> dict[str, Any]:
        """Build hierarchical tree structure.

        Args:
            root_name: Root class name
            ancestors: List of ancestor class dicts
            descendants: List of descendant class dicts
            direction: Query direction

        Returns:
            Tree structure dictionary
        """
        tree: dict[str, Any] = {
            "name": root_name,
            "type": "root",
        }

        if direction in ("up", "both") and ancestors:
            tree["parents"] = [
                {"name": anc["class_name"], "depth": anc["depth"]}
                for anc in ancestors
            ]

        if direction in ("down", "both") and descendants:
            tree["children"] = [
                {"name": desc["class_name"], "depth": desc["depth"]}
                for desc in descendants
            ]

        return tree


def create_class_hierarchy_tool(ingestor: Any) -> dict[str, Any]:
    """Create MCP tool for exploring class hierarchies.

    Args:
        ingestor: MemgraphIngestor instance

    Returns:
        Tool definition dictionary
    """
    query_tool = ClassHierarchyQuery()

    async def class_hierarchy(
        class_name: str,
        direction: Literal["up", "down", "both"] = "both",
        max_depth: int = 10,
    ) -> dict[str, Any]:
        """Explore class inheritance hierarchies.

        Args:
            class_name: Fully qualified class name
            direction: Traversal direction ('up', 'down', or 'both')
            max_depth: Maximum hierarchy depth (default: 10)

        Returns:
            Dictionary containing hierarchy tree and metadata
        """
        return query_tool.execute(ingestor, class_name, direction, max_depth)

    return {
        "name": "query_hierarchy",
        "description": (
            "Explore class inheritance hierarchies showing ancestors (parent classes), "
            "descendants (child classes), or both. "
            "Use this for understanding OOP relationships and safe base class refactoring."
        ),
        "handler": class_hierarchy,
        "input_schema": {
            "type": "object",
            "properties": {
                "class_name": {
                    "type": "string",
                    "description": "Fully qualified name of the class to analyze (e.g., 'auth.models.BaseAuth')",
                },
                "direction": {
                    "type": "string",
                    "enum": ["up", "down", "both"],
                    "description": "Direction to traverse: 'up' for ancestors, 'down' for descendants, 'both' for complete tree (default: 'both')",
                    "default": "both",
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth to traverse hierarchy (default: 10)",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 10,
                },
            },
            "required": ["class_name"],
        },
    }


# =============================================================================
# Module Exports Query (Phase 9)
# =============================================================================


@dataclass
class ModuleExportsQuery(StructuralQueryTool):
    """Retrieve all public exports from a module.

    Returns functions and classes defined by a module, optionally including
    private members (those starting with underscore).
    """

    name: str = "module_exports"
    description: str = "Retrieve all public exports (functions, classes) from a module"
    truncate_limit: int = 100

    def execute(
        self,
        ingestor: Any,
        module_name: str,
        include_private: bool = False,
    ) -> dict[str, Any]:
        """Execute module exports query.

        Args:
            ingestor: MemgraphIngestor instance
            module_name: Fully qualified module name
            include_private: Whether to include private members (starting with _)

        Returns:
            Formatted result dictionary with exports and metadata
        """
        # Build query to find all exports via DEFINES relationship
        query = """
        MATCH (module:Module {qualified_name: $name})-[:DEFINES]->(export:Function|Class|Method)
        RETURN
            export.qualified_name AS export_name,
            export.name AS short_name,
            labels(export) AS type,
            export.file_path AS file_path,
            export.line_start AS line_number
        ORDER BY labels(export)[0], short_name
        """
        params = {"name": module_name}

        try:
            # Execute query with performance logging
            results, execution_time_ms = ingestor.execute_structural_query(
                query, params, query_name="module_exports"
            )

            # Check if module exists
            if not results:
                # Verify if the module exists in the graph
                check_query = """
                MATCH (m:Module {qualified_name: $name})
                RETURN m.qualified_name
                """
                exists = ingestor.fetch_all(check_query, {"name": module_name})
                if not exists:
                    raise NodeNotFoundError(module_name, "Module")

            # Filter out private members if requested
            formatted_results = []
            for row in results:
                short_name = row["short_name"]

                # Skip private members unless explicitly requested
                if not include_private and short_name.startswith("_"):
                    continue

                result_item: dict[str, Any] = {
                    "export": row["export_name"],
                    "name": short_name,
                    "type": row["type"][0] if row["type"] else "Unknown",
                }

                if row.get("file_path"):
                    result_item["file_path"] = row["file_path"]
                    if row.get("line_number"):
                        result_item["line_number"] = row["line_number"]

                formatted_results.append(result_item)

            query_desc = (
                f"Exports from module {module_name}"
                + (" (including private)" if include_private else " (public only)")
            )

            return self.format_results(formatted_results, execution_time_ms, query_desc)

        except NodeNotFoundError as e:
            return handle_node_not_found(e.qualified_name, e.node_type)
        except Exception as e:
            return self.handle_error(
                e, {"module_name": module_name, "include_private": include_private}
            )


def create_module_exports_tool(ingestor: Any) -> dict[str, Any]:
    """Create MCP tool for retrieving module exports.

    Args:
        ingestor: MemgraphIngestor instance

    Returns:
        Tool definition dictionary
    """
    query_tool = ModuleExportsQuery()

    async def module_exports(
        module_name: str, include_private: bool = False
    ) -> dict[str, Any]:
        """Retrieve all public exports from a module.

        Args:
            module_name: Fully qualified module name (e.g., 'auth.services')
            include_private: Include private members starting with underscore (default: false)

        Returns:
            Dictionary containing exports and metadata
        """
        return query_tool.execute(ingestor, module_name, include_private)

    return {
        "name": "query_module_exports",
        "description": (
            "Retrieve all public exports (functions, classes, methods) from a specified module. "
            "Use this to understand a module's public API surface and identify what functionality it provides. "
            "Optionally include private members (starting with _) for complete module analysis."
        ),
        "handler": module_exports,
        "input_schema": {
            "type": "object",
            "properties": {
                "module_name": {
                    "type": "string",
                    "description": "Fully qualified name of the module to analyze (e.g., 'auth.services', 'utils.validation')",
                },
                "include_private": {
                    "type": "boolean",
                    "description": "Include private members (names starting with underscore) in results (default: false)",
                    "default": False,
                },
            },
            "required": ["module_name"],
        },
    }
