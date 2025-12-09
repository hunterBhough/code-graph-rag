from loguru import logger
from pydantic_ai import Tool
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..graph_updater import MemgraphIngestor
from ..schemas import GraphData
from ..services.llm import CypherGenerator, LLMGenerationError


class GraphQueryError(Exception):
    """Custom exception for graph query failures."""

    pass


def create_query_tool(
    ingestor: MemgraphIngestor,
    cypher_gen: CypherGenerator,
    console: Console | None = None,
) -> Tool:
    """
    Factory function that creates the knowledge graph query tool,
    injecting its dependencies.
    """
    # Use provided console or create a default one
    if console is None:
        console = Console(width=None, force_terminal=True)

    async def query_codebase_knowledge_graph(natural_language_query: str) -> GraphData:
        """
        Queries the codebase knowledge graph using natural language.

        **IMPORTANT**: For common structural queries, prefer using the pre-built
        specialized tools instead:
        - query_callers: Find functions that call a target function
        - query_hierarchy: Explore class inheritance hierarchies
        - query_dependencies: Analyze module/function dependencies
        - query_implementations: Find interface/base class implementations
        - query_module_exports: List public exports from a module
        - query_call_graph: Generate call graphs from entry points
        - query_cypher: Execute custom Cypher queries (expert mode)

        Use this natural language tool only for complex or uncommon queries that
        don't fit the pre-built patterns. The specialized tools are faster, more
        reliable, and provide better error messages.

        Provide your question in plain English about the codebase structure,
        functions, classes, dependencies, or relationships. The tool will
        automatically translate your natural language question into the
        appropriate database query and return the results.

        Examples of queries suitable for this tool:
        - "Find all functions with more than 5 callers sorted by complexity"
        - "Show me circular dependencies in the authentication module"
        - "Which classes have methods that are never called"
        - "Find functions that call multiple database-related functions"
        """
        logger.info(f"[Tool:QueryGraph] Received NL query: '{natural_language_query}'")
        cypher_query = "N/A"
        try:
            cypher_query = await cypher_gen.generate(natural_language_query)

            results = ingestor.fetch_all(cypher_query)

            if results:
                table = Table(
                    show_header=True,
                    header_style="bold magenta",
                )
                headers = results[0].keys()
                for header in headers:
                    table.add_column(header)

                for row in results:
                    renderable_values = []
                    for value in row.values():
                        if value is None:
                            renderable_values.append("")
                        elif isinstance(value, bool):
                            # Check bool first since bool is a subclass of int in Python
                            renderable_values.append("✓" if value else "✗")
                        elif isinstance(value, int | float):
                            # Let Rich handle number formatting by converting to string
                            renderable_values.append(str(value))
                        else:
                            renderable_values.append(str(value))
                    table.add_row(*renderable_values)

                console.print(
                    Panel(
                        table,
                        title="[bold blue]Cypher Query Results[/bold blue]",
                        expand=False,
                    )
                )

            summary = f"Successfully retrieved {len(results)} item(s) from the graph."
            return GraphData(query_used=cypher_query, results=results, summary=summary)
        except LLMGenerationError as e:
            return GraphData(
                query_used="N/A",
                results=[],
                summary=f"I couldn't translate your request into a database query. Error: {e}",
            )
        except Exception as e:
            logger.error(
                f"[Tool:QueryGraph] Error during query execution: {e}", exc_info=True
            )
            return GraphData(
                query_used=cypher_query,
                results=[],
                summary=f"There was an error querying the database: {e}",
            )

    return Tool(
        function=query_codebase_knowledge_graph,
        description="Query the codebase knowledge graph using natural language questions. Ask in plain English about classes, functions, methods, dependencies, or code structure. Examples: 'Find all functions that call each other', 'What classes are in the user module', 'Show me functions with the longest call chains'.",
    )
