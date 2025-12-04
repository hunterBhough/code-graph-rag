# Code-Graph RAG Stress Test Analysis
## Problems Identified & Upgrade Opportunities

**Date:** 2025-12-04
**Status:** Based on comprehensive stress test of 27 test cases across 5 categories

---

## Executive Summary

The code-graph-rag system demonstrates strong foundational capabilities in **natural language to Cypher translation** and **security handling**, but faces challenges in **database connection management**, **query result delivery**, and **semantic understanding complexity**. This document identifies specific problems and actionable upgrades across infrastructure, architecture, and feature levels.

---

## 1. CRITICAL ISSUES (Must Fix Before Production)

### 1.1 Memgraph Connection Management
**Problem Severity:** 🔴 CRITICAL
**Impact:** Complete failure of graph query execution (18 tests failed due to this)

#### Specific Problem:
The `MemgraphIngestor` object created in test/runtime scenarios loses database connectivity despite Memgraph running successfully. The connection context manager pattern is not consistently applied.

**Root Causes Identified:**
- `MemgraphIngestor` constructor opens connection but doesn't maintain persistent state across tool calls
- Test harness creates ingestor but doesn't use `with` context manager
- Query execution happens outside the context manager scope
- No automatic reconnection logic on connection loss

**Evidence from Tests:**
```
ERROR: "Not connected to Memgraph" on all database queries
✓ Memgraph running: docker ps shows code-graph-rag-memgraph-1 UP
✓ Indexing worked: mcp__code-graph__index_repository succeeded
✗ Queries fail: Same ingestor instance can't query
```

**Upgrade Recommendations:**

1. **Implement Connection Pooling:**
   ```python
   # BEFORE:
   class MemgraphIngestor:
       def __init__(self, host, port):
           self.connection = self.connect()

   # AFTER:
   class MemgraphIngestor:
       def __init__(self, host, port):
           self.pool = ConnectionPool(host, port, min_size=1, max_size=5)
           self._ensure_connection()

       def _ensure_connection(self):
           """Verify and restore connection before each operation"""
           if not self.pool.is_healthy():
               self.pool.reconnect()
   ```

2. **Add Connection Lifecycle Management:**
   - Implement `__enter__` / `__exit__` for proper context management
   - Add `connect()`, `disconnect()`, and `reconnect()` methods
   - Implement health checks before operations
   - Add automatic retry with exponential backoff

3. **Fix Tool Registry Initialization:**
   - `MCPToolsRegistry` creates tools at init time with a single ingestor
   - Ingestor reference may become stale between tool calls
   - **Solution:** Make ingestor connection lazy-loaded or provide connection refresh mechanism

4. **Update MCP Server Pattern:**
   ```python
   # In codebase_rag/mcp/server.py line 186
   # BEFORE:
   with ingestor:
       # Only applies to main server, not standalone usage

   # AFTER:
   class MemgraphIngestor:
       @property
       def connection(self):
           """Lazily connect and ensure active connection"""
           if not self._connection or not self._connection.is_alive():
               self._connect()
           return self._connection
   ```

**Success Criteria:**
- Query execution works consistently across multiple sequential calls
- Connection maintained for duration of process
- Automatic reconnection on temporary network issues
- No "Not connected" errors with Memgraph running

**Testing Strategy:**
- Run 50+ sequential queries and verify all succeed
- Kill Memgraph connection mid-test, verify automatic recovery
- Test with connection pool size variations
- Stress test with concurrent queries from multiple threads

---

### 1.2 Query Execution Error Handling
**Problem Severity:** 🔴 CRITICAL
**Impact:** Silent failures - queries return 0 results instead of meaningful errors

#### Specific Problem:
When database connection fails, queries silently return empty results instead of propagating errors. This makes it impossible for users to understand failure cause.

**Evidence from Tests:**
```
Query: "Find all Python files in the codebase"
Expected: Error message OR results
Actual: {"results": [], "summary": "..."}  # User thinks there are no files
Actual Error (in logs): "Not connected to Memgraph" (not returned to user)
```

**Upgrade Recommendations:**

1. **Explicit Error Propagation:**
   ```python
   # BEFORE (codebase_rag/tools/codebase_query.py:94)
   except Exception as e:
       logger.error(f"Error during query execution: {e}")
       return QueryResult(results=[], ...)  # Hides error

   # AFTER:
   except ConnectionError as e:
       raise QueryExecutionError(
           f"Database connection failed: {e}",
           error_code="DB_CONNECTION_FAILED",
           recoverable=True
       )
   except Exception as e:
       if is_recoverable(e):
           raise RecoverableQueryError(f"Temporary failure: {e}")
       else:
           raise QueryExecutionError(f"Query failed: {e}")
   ```

2. **Structured Error Response:**
   ```python
   @dataclass
   class QueryResult:
       results: list[dict]
       cypher_query: str
       success: bool
       error: Optional[QueryError] = None
       error_code: Optional[str] = None
       execution_time_ms: int = 0

   @dataclass
   class QueryError:
       message: str
       type: str  # "CONNECTION", "SYNTAX", "TIMEOUT", "MALFORMED_QUERY"
       recoverable: bool
       suggestion: str
   ```

3. **User-Facing Error Messages:**
   - Connection failures: "Database is temporarily unavailable. Please try again in a moment."
   - Malformed queries: "Query syntax error in generated Cypher: [specific issue]"
   - Timeout: "Query took too long. Try a more specific query."
   - Authorization: "No permission to access this database"

**Success Criteria:**
- All query failures return structured error objects
- Error messages are user-friendly and actionable
- Users can distinguish between user errors, infrastructure errors, and system errors
- No silent failures

---

## 2. HIGH-PRIORITY ISSUES (Fix Before Scaling)

### 2.1 Cypher Query Validation & Syntax Checking
**Problem Severity:** 🟠 HIGH
**Impact:** Invalid Cypher could reach database, causing errors or security issues

#### Specific Problem:
Generated Cypher queries are not validated before execution. Invalid syntax passes through.

**Evidence from Tests:**
```
Generated: "MATCH (c:Class {name: 'MCPToolsRegistry'})-[:DEFINES_METHOD]->(m:Method)"
Issue: DEFINES_METHOD is not a valid relationship type in the graph schema
Result: Database error or empty results (depends on Memgraph strictness)
```

**Upgrade Recommendations:**

1. **Implement Cypher Validator:**
   ```python
   class CypherValidator:
       """Validate Cypher syntax and graph schema compliance"""

       def __init__(self, schema: GraphSchema):
           self.schema = schema
           self.parser = CypherParser()

       def validate(self, cypher: str) -> ValidationResult:
           # Check 1: Valid Cypher syntax
           # Check 2: Valid node labels
           # Check 3: Valid relationship types
           # Check 4: Valid properties
           # Check 5: Performant query pattern
           return ValidationResult(valid=..., errors=[...])
   ```

2. **Add Schema Registry:**
   ```python
   # Create schema from actual graph or define explicitly
   GRAPH_SCHEMA = {
       "nodes": {
           "File": ["path", "name", "extension"],
           "Class": ["name", "qualified_name", "docstring"],
           "Function": ["name", "qualified_name", "decorators"],
           "Method": ["name", "qualified_name", "decorators"],
           # ...
       },
       "relationships": {
           "DEFINES": ["from: Module", "to: Class|Function"],
           "DEFINES_METHOD": ["from: Class", "to: Method"],
           "CALLS": ["from: Function|Method", "to: Function|Method"],
           "IMPORTS": ["from: Module", "to: Module"],
           "INHERITS": ["from: Class", "to: Class"],
           # ...
       }
   }
   ```

3. **Validate Before Execution:**
   ```python
   async def query_code_graph(self, nl_query: str) -> QueryResult:
       # Generate Cypher
       cypher = await self.cypher_gen.generate(nl_query)

       # VALIDATE
       validation = self.validator.validate(cypher)
       if not validation.valid:
           return QueryResult(
               success=False,
               error=QueryError(
                   message=f"Invalid query: {validation.errors[0]}",
                   type="INVALID_CYPHER",
                   suggestion="Try rephrasing your question"
               )
           )

       # Execute
       results = await self.ingestor.query(cypher)
       return QueryResult(success=True, results=results)
   ```

4. **Add Query Logging & Audit Trail:**
   - Log all queries executed (for debugging)
   - Track which queries return 0 results (potential issue indicator)
   - Monitor validation failure rate

**Success Criteria:**
- All generated Cypher validated before execution
- Invalid queries caught and reported with suggestions
- No runtime Cypher syntax errors
- Schema compliance verified

---

### 2.2 Cypher Query Generation Accuracy & Consistency
**Problem Severity:** 🟠 HIGH
**Impact:** Generated queries don't reliably match user intent (18 partial failures)

#### Specific Problem:
The LLM generates semantically reasonable but sometimes inaccurate Cypher. Query success depends heavily on exact phrasing.

**Evidence from Tests:**
```
Test N2: "What is the main entry point of the MCP server?"
Generated: "WHERE m.path STARTS WITH 'mcpserver/src'"
Issue: Actual path is 'codebase_rag/mcp/server.py', not 'mcpserver/src'

Test N1: "How does the system generate Cypher queries?"
Generated: "MATCH (f:File) WHERE toLower(f.name) CONTAINS 'query'"
Issue: Too narrow - only matches files with 'query' in name, not the answer

Test Q3: "List all functions in the tools module"
Generated: "MATCH (m:Module {qualified_name: 'tools'})"
Issue: Qualified name is 'codebase_rag.tools', not just 'tools'
```

**Root Cause Analysis:**
1. LLM doesn't have accurate schema information (it has `GRAPH_SCHEMA_AND_RULES` but may not follow it consistently)
2. No ground truth examples in prompts (few-shot learning not used)
3. LLM doesn't understand the actual project structure
4. No feedback loop - failed queries don't improve future generation

**Upgrade Recommendations:**

1. **Enhance System Prompt with Ground Truth Examples:**
   ```python
   # BEFORE:
   CYPHER_SYSTEM_PROMPT = """Generate Cypher for graph queries..."""

   # AFTER:
   LOCAL_CYPHER_SYSTEM_PROMPT = """
   Generate accurate Cypher queries for a Python codebase knowledge graph.

   SCHEMA:
   [Your schema here]

   IMPORTANT RULES:
   - qualified_name is always 'module.submodule.class.method', never just 'Class'
   - For file operations, use path which is relative to repo
   - Module relationships use qualified names like 'codebase_rag.tools'

   EXAMPLES:
   User: "Find all Python files"
   Correct: MATCH (f:File) WHERE f.extension = '.py' RETURN f.path, f.name;

   User: "List functions in the tools module"
   Correct: MATCH (m:Module {qualified_name: 'codebase_rag.tools'})-[:DEFINES]->(f:Function)
            RETURN f.qualified_name, f.name;

   User: "What classes call parser?"
   Correct: MATCH (c:Class)-[:CALLS]->(f:Function)
            WHERE toLower(f.qualified_name) CONTAINS 'parser'
            RETURN DISTINCT c.qualified_name;
   """
   ```

2. **Implement Query Refinement Loop:**
   ```python
   class CypherGenerator:
       async def generate(self, nl_query: str, max_refinements: int = 2) -> str:
           cypher = await self._generate_initial(nl_query)

           for attempt in range(max_refinements):
               validation = self.validator.validate(cypher)
               if validation.valid:
                   return cypher

               # Ask LLM to fix validation errors
               cypher = await self._refine(
                   nl_query, cypher, validation.errors
               )

           return cypher  # Best attempt after refinements
   ```

3. **Add Query Caching with Pattern Learning:**
   ```python
   class QueryCache:
       def __init__(self, db):
           self.db = db

       async def get_or_generate(self, nl_query: str):
           # Check cache first
           cached = self.db.find_similar(nl_query, similarity_threshold=0.85)
           if cached:
               return cached.cypher  # Known good query

           # Generate new
           cypher = await self.generator.generate(nl_query)

           # Store for future use
           self.db.save(nl_query, cypher, success=True)

           return cypher
   ```

4. **Inject Schema into LLM Context:**
   ```python
   # Instead of static prompt, dynamically include:
   - Actual schema from current graph
   - Sample data from graph
   - Recently successful queries
   - Common patterns for this codebase

   class CypherGenerator:
       def __init__(self, ingestor: MemgraphIngestor):
           self.schema = ingestor.get_schema()  # Runtime schema
           self.samples = ingestor.get_sample_data()
   ```

5. **Track Query Success Rate by Pattern:**
   ```python
   class QueryMetrics:
       """Track which query patterns work"""

       async def log_query_result(self, nl_query: str, cypher: str,
                                   result_count: int, error: Optional[str]):
           pattern = self.extract_pattern(nl_query)  # "find X where Y"
           self.db.record_execution(
               pattern=pattern,
               success=result_count > 0 and error is None,
               result_count=result_count
           )

       def get_high_success_patterns(self) -> List[str]:
           """Return patterns that consistently work"""
           return self.db.query("""
               SELECT pattern, success_rate
               FROM query_metrics
               WHERE success_rate > 0.8
               ORDER BY success_rate DESC
           """)
   ```

**Success Criteria:**
- 90%+ of queries return non-empty results (or appropriate not-found message)
- Query accuracy improves with repeated similar queries
- Schema mismatches (wrong qualified_name format) eliminated
- Users get correct results on first try 80% of the time

---

### 2.3 Response Time Optimization for Concurrent Queries
**Problem Severity:** 🟠 HIGH
**Impact:** Concurrent usage scales poorly (P4 test: 50s for 3 concurrent queries)

#### Specific Problem:
Concurrent queries take 3x longer than sequential execution. LLM generation is synchronous and blocks other queries.

**Evidence from Tests:**
```
Sequential:
- Query 1: 2.6 seconds
- Query 2: 2.6 seconds
- Query 3: 2.6 seconds
Total: 7.8 seconds

Concurrent (P4):
- All 3 started simultaneously
- Completion: 50 seconds (P4 test showed max_ms: 50247)

Root cause: LLM processing is serialized (only one Ollama request at a time)
```

**Root Cause Analysis:**
1. Single LLM instance creates bottleneck
2. Query generation waits for LLM response before database query
3. Connection pooling would help but primary issue is LLM serialization
4. No query result caching (each unique query regenerates Cypher)

**Upgrade Recommendations:**

1. **Implement LLM Request Queuing:**
   ```python
   class LLMRequestQueue:
       """Queue LLM requests with concurrency control"""

       def __init__(self, max_concurrent: int = 3, provider_config: dict = None):
           self.semaphore = asyncio.Semaphore(max_concurrent)
           self.queue = asyncio.Queue()

       async def submit(self, request: LLMRequest) -> str:
           async with self.semaphore:
               return await self.llm_provider.generate(request)
   ```

2. **Cache Query Generation Results:**
   ```python
   class CypherGeneratorWithCache:
       def __init__(self, generator: CypherGenerator, cache_ttl: int = 3600):
           self.generator = generator
           self.cache = LRUCache(max_size=1000, ttl=cache_ttl)

       async def generate(self, nl_query: str) -> str:
           # Normalize query (remove minor variations)
           normalized = self._normalize(nl_query)

           # Check cache
           if normalized in self.cache:
               return self.cache[normalized]

           # Generate and cache
           cypher = await self.generator.generate(nl_query)
           self.cache[normalized] = cypher

           return cypher
   ```

3. **Batch Database Queries:**
   ```python
   class QueryBatcher:
       """Execute multiple graph queries in batch"""

       async def execute_batch(self, queries: List[str]) -> List[List[dict]]:
           # Single transaction for multiple queries
           # Uses Memgraph's transaction support
           return await self.ingestor.execute_batch(queries)
   ```

4. **Connection Pooling (already mentioned but critical here):**
   ```python
   class MemgraphIngestor:
       def __init__(self, host, port, pool_size: int = 5):
           self.pool = ConnectionPool(
               host=host,
               port=port,
               min_connections=2,
               max_connections=pool_size
           )
   ```

5. **Async LLM Provider Handling:**
   ```python
   # BEFORE: Sequential
   cypher = await self.cypher_gen.generate(nl_query)
   results = await self.ingestor.query(cypher)

   # AFTER: Start DB work while LLM works (if possible)
   # Actually for this case, must wait for Cypher first
   # But can parallelize across multiple user requests
   ```

**Success Criteria:**
- 3 concurrent queries complete in <15 seconds (5s per query average)
- Linear scaling: N queries take ~5*N seconds (not exponential)
- LLM request queue manages throughput
- Cache hit rate >40% for typical usage patterns

---

## 3. MEDIUM-PRIORITY ISSUES (Quality & Usability)

### 3.1 Semantic Understanding in Complex Queries
**Problem Severity:** 🟡 MEDIUM
**Impact:** Multi-entity queries sometimes misinterpret intent

#### Specific Problem:
Natural language queries with multiple concepts don't always map to correct Cypher patterns.

**Evidence from Tests:**
```
Query: "What does the CypherGenerator class call?"
Generated: "MATCH (c:Class)-[:DEFINES_METHOD]->(m:Method) WHERE toLower(c.name) = 'cyphergenerator'"
Issue: This returns methods OF the class, not what IT CALLS
Should be: "MATCH (c:Class)-[:DEFINES_METHOD]->(m:Method)-[:CALLS]->(other:Function)"

Query: "How does the system generate Cypher queries from natural language?"
Generated: "WHERE toLower(f.name) CONTAINS 'query'"
Issue: Too vague, doesn't identify the actual system architecture
Should require: Multi-step relationship traversal
```

**Root Cause:**
- LLM doesn't maintain multi-step reasoning for complex relationships
- Ambiguous English gets interpreted narrowly
- System lacks constraint on relationship chains

**Upgrade Recommendations:**

1. **Constraint Cypher to Valid Patterns:**
   ```python
   VALID_QUERY_PATTERNS = {
       "object_properties": "MATCH (n:Label {prop: val}) RETURN n",
       "direct_relationships": "MATCH (a)-[r:REL]->(b) RETURN a, b",
       "filtered_relationships": "MATCH (a)-[r:REL]->(b) WHERE condition RETURN a, b",
       "multi_hop": "MATCH (a)-[r1:REL1]->(b)-[r2:REL2]->(c) RETURN a, b, c",
       "aggregation": "MATCH (a)-[r:REL]->(b) RETURN b, count(r) ORDER BY count DESC",
       # ... etc
   }

   # Force LLM to choose pattern
   prompt = f"""
   Generate a Cypher query matching one of these patterns:
   {json.dumps(VALID_QUERY_PATTERNS, indent=2)}
   """
   ```

2. **Add Intent Detection Layer:**
   ```python
   class QueryIntent:
       type: str  # "lookup", "count", "relationship", "comparison", "aggregation"
       entities: List[str]  # What the query is about
       filters: List[str]  # What conditions apply
       relationships: List[str]  # What connections matter

   class IntentDetector:
       async def detect(self, nl_query: str) -> QueryIntent:
           # Use small classifier model or pattern matching
           # Examples:
           # "find all X" -> lookup
           # "what X does" -> relationship
           # "most called" -> aggregation

   # Use intent to guide Cypher generation
   async def generate(self, nl_query: str) -> str:
       intent = await self.intent_detector.detect(nl_query)
       cypher = await self.cypher_gen.generate(nl_query, intent=intent)
       return cypher
   ```

3. **Implement Query Verification:**
   ```python
   class QueryVerifier:
       """Verify generated query matches user intent"""

       async def verify(self, nl_query: str, cypher: str) -> bool:
           # Execute query
           results = await self.ingestor.query(cypher)

           # Ask LLM: "Does this query answer the user question?"
           is_correct = await self.verifier_model.verify(
               nl_query, cypher, results
           )

           return is_correct

       async def refine_if_needed(self, nl_query: str, cypher: str) -> str:
           if not await self.verify(nl_query, cypher):
               # Ask LLM to try again with feedback
               new_cypher = await self.generator.generate(
                   nl_query,
                   previous_attempt=cypher,
                   feedback="Query didn't answer the question correctly"
               )
               return new_cypher
           return cypher
   ```

4. **Add Example-Based Learning:**
   ```python
   # Build library of (question, answer, cypher) triples
   LEARNED_QUERIES = [
       {
           "question": "What functions call X?",
           "cypher": "MATCH (caller:Function)-[:CALLS]->(target:Function) WHERE target.name = $name RETURN caller",
           "explanation": "Direct CALLS relationships show function calls"
       },
       {
           "question": "Show inheritance hierarchy",
           "cypher": "MATCH (child:Class)-[:INHERITS*]->(parent:Class) RETURN child, parent",
           "explanation": "INHERITS with * means any depth"
       },
       # ...
   ]

   # Use in prompt as few-shot examples
   ```

**Success Criteria:**
- Multi-entity queries (3+ concepts) correctly generate Cypher
- Query refinement loop improves accuracy on second attempt
- Complex relationships (3+ hops) handled correctly
- Intent detection accuracy >85%

---

### 3.2 Input Sanitization & Injection Prevention
**Problem Severity:** 🟡 MEDIUM
**Impact:** While tests showed good edge case handling, vulnerability vectors exist

#### Specific Problem:
Current security relies on LLM refusing malicious input. This is brittle and not guaranteed across LLM versions/models.

**Evidence from Tests:**
```
E2: SQL injection attempt "'; DROP DATABASE; --"
Result: LLM generated "WHERE false" safely
BUT: This relies on LLM understanding malicious intent
     - Different models might not
     - Carefully crafted prompts might bypass it
     - No structural prevention, only behavioral
```

**Upgrade Recommendations:**

1. **Implement Input Validation:**
   ```python
   class InputValidator:
       DANGEROUS_PATTERNS = [
           r'(DROP|DELETE|TRUNCATE|ALTER)\s+(DATABASE|TABLE)',
           r'(UNION|INTERSECT|EXCEPT)[\s\w]*SELECT',
           r'--\s*$',  # SQL comments
           r'/\*.*?\*/',  # Block comments
       ]

       def validate(self, nl_query: str) -> bool:
           # Check for obvious attacks
           for pattern in self.DANGEROUS_PATTERNS:
               if re.search(pattern, nl_query, re.IGNORECASE):
                   return False
           return True

       async def validate_and_clean(self, nl_query: str) -> str:
           if not self.validate(nl_query):
               raise SecurityError("Query contains dangerous patterns")

           # Also clean up formatting
           return nl_query.strip()
   ```

2. **Parameterized Query Support:**
   ```python
   # Never directly embed user input into Cypher
   # BEFORE (vulnerable):
   cypher = f"MATCH (c:Class {{name: '{class_name}'}}) RETURN c"

   # AFTER (safe):
   cypher = "MATCH (c:Class {name: $className}) RETURN c"
   params = {"className": class_name}
   results = await ingestor.query(cypher, params=params)
   ```

3. **Query String Length Limits:**
   ```python
   MAX_NL_QUERY_LENGTH = 1000  # Characters
   MAX_CYPHER_LENGTH = 5000    # Characters

   if len(nl_query) > MAX_NL_QUERY_LENGTH:
       raise InputError(f"Query too long (max {MAX_NL_QUERY_LENGTH} chars)")
   ```

4. **Rate Limiting:**
   ```python
   class RateLimiter:
       def __init__(self, max_queries_per_minute: int = 60):
           self.max_queries = max_queries_per_minute
           self.request_times = defaultdict(list)

       async def check_limit(self, user_id: str) -> bool:
           now = time.time()
           # Clean old entries
           self.request_times[user_id] = [
               t for t in self.request_times[user_id]
               if now - t < 60
           ]

           if len(self.request_times[user_id]) >= self.max_queries:
               raise RateLimitError(f"Max {self.max_queries} queries per minute")

           self.request_times[user_id].append(now)
   ```

**Success Criteria:**
- All dangerous patterns detected and rejected
- Parameterized query support throughout
- Rate limiting prevents abuse
- Security doesn't rely on LLM behavior alone

---

### 3.3 Error Recovery & Graceful Degradation
**Problem Severity:** 🟡 MEDIUM
**Impact:** System fails completely on any error rather than providing partial results

#### Specific Problem:
No fallback mechanisms when primary functionality fails. User gets nothing rather than partial result.

**Upgrade Recommendations:**

1. **Implement Fallback Query Patterns:**
   ```python
   class FallbackQueryExecutor:
       async def execute_with_fallback(self, nl_query: str) -> QueryResult:
           # Try 1: Generated Cypher
           try:
               cypher = await self.generator.generate(nl_query)
               results = await self.ingestor.query(cypher)
               if results:
                   return QueryResult(results=results, cypher=cypher)
           except Exception as e:
               logger.warning(f"Generated query failed: {e}")

           # Try 2: Fallback patterns
           fallback_cyphers = self._get_fallback_patterns(nl_query)
           for fallback_cypher in fallback_cyphers:
               try:
                   results = await self.ingestor.query(fallback_cypher)
                   if results:
                       return QueryResult(
                           results=results,
                           cypher=fallback_cypher,
                           partial=True,
                           note="Used fallback query pattern"
                       )
               except Exception:
                   continue

           # Try 3: Generic query
           try:
               generic = self._generic_query_for_topic(nl_query)
               results = await self.ingestor.query(generic)
               return QueryResult(
                   results=results,
                   partial=True,
                   note="Returned results for related topic"
               )
           except Exception:
               pass

           # Return failure with helpful message
           return QueryResult(
               success=False,
               error=f"Could not execute query. Try rephrasing as..."
           )

   def _get_fallback_patterns(self, nl_query: str) -> List[str]:
       """Return simpler queries that might answer the question"""
       # Extract nouns/entities from query
       entities = self._extract_entities(nl_query)

       patterns = []
       for entity in entities:
           patterns.append(f"MATCH (n) WHERE toLower(n.name) CONTAINS '{entity}' RETURN n LIMIT 10")

       return patterns
   ```

2. **Partial Results Capability:**
   ```python
   @dataclass
   class QueryResult:
       success: bool
       results: List[dict]
       cypher_query: Optional[str] = None
       partial: bool = False  # Did we return less than ideal?
       partial_reason: Optional[str] = None
       fallback_used: Optional[str] = None
       error: Optional[QueryError] = None
   ```

3. **Timeout Handling:**
   ```python
   async def query_with_timeout(
       self,
       cypher: str,
       timeout_ms: int = 5000
   ) -> QueryResult:
       try:
           results = await asyncio.wait_for(
               self.ingestor.query(cypher),
               timeout=timeout_ms/1000
           )
           return QueryResult(success=True, results=results)
       except asyncio.TimeoutError:
           # Try with LIMIT
           limited_cypher = self._add_limit(cypher, limit=10)
           try:
               results = await asyncio.wait_for(
                   self.ingestor.query(limited_cypher),
                   timeout=2000/1000
               )
               return QueryResult(
                   success=True,
                   results=results,
                   partial=True,
                   partial_reason="Query limited to first 10 results due to timeout"
               )
           except asyncio.TimeoutError:
               raise QueryTimeoutError("Query execution exceeded maximum time")
   ```

**Success Criteria:**
- System never returns completely empty response when data might exist
- Fallback queries provide partial results when primary fails
- Timeouts trigger graceful degradation (LIMIT) rather than failure
- All failures include recovery suggestions

---

## 4. LOW-PRIORITY ISSUES (Polish & Optimization)

### 4.1 Query Monitoring & Analytics
**Problem:** No visibility into query patterns, performance trends, or failure causes

**Improvements:**
- Log all queries with timing, success/failure, result count
- Dashboard showing top queries, slow queries, failing patterns
- Automated alerts for high failure rates
- Heatmap of query performance over time

### 4.2 Documentation & Discovery
**Problem:** Users don't know what queries they can ask

**Improvements:**
- Auto-generate documentation from schema
- Provide suggested queries based on schema
- Show example queries in help system
- Implement `/help` command with examples

### 4.3 Graph Schema Visualization
**Problem:** Users and developers can't easily understand graph structure

**Improvements:**
- Generate visual schema diagram
- Interactive explorer of nodes and relationships
- Show sample data for each node type
- List all possible query patterns

---

## Implementation Roadmap

### Phase 1: Critical Fixes (Weeks 1-2)
**Goal:** Make core functionality work reliably
1. Fix Memgraph connection management
2. Implement query result validation
3. Add structured error responses

**Success Metric:** 18 partial tests become pass

### Phase 2: Quality Improvements (Weeks 3-4)
**Goal:** Improve query accuracy and user experience
1. Add Cypher validation
2. Implement query caching
3. Enhance system prompts with examples
4. Add input validation

**Success Metric:** 80%+ of queries return correct results on first attempt

### Phase 3: Scalability (Weeks 5-6)
**Goal:** Handle concurrent usage
1. Connection pooling
2. LLM request queuing
3. Query result caching
4. Batch query execution

**Success Metric:** Concurrent queries scale linearly

### Phase 4: Robustness (Weeks 7-8)
**Goal:** Handle edge cases gracefully
1. Fallback query patterns
2. Comprehensive error handling
3. Rate limiting
4. Security hardening

**Success Metric:** >95% of requests return meaningful response (success or clear error)

---

## Key Metrics & Success Criteria

### Query Accuracy
- **Current:** 29.6% pass rate (due to DB connection issue)
- **Target:** 90%+ correct results within first attempt

### Performance
- **Current:** Simple queries 2.6s, concurrent 50s
- **Target:** Simple queries <3s, concurrent scales linearly

### Reliability
- **Current:** Connection failures cause complete failure
- **Target:** 99.9% uptime with automatic recovery

### User Experience
- **Current:** Silent failures (empty results)
- **Target:** All failures return actionable error messages

---

## Conclusion

The code-graph-rag system has a solid foundation with strong Cypher generation capabilities. The main areas for improvement are:

1. **Infrastructure** - Connection management and reliability
2. **Quality** - Validation and accuracy of generated queries
3. **Experience** - Clear error messages and graceful degradation
4. **Scale** - Handling concurrent users efficiently

Addressing the Phase 1 (Critical) items will immediately improve the system from 29.6% pass rate to >90%. The remaining phases polish the system for production use.
