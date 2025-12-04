# Code-Graph RAG - Upgrade Priorities (Quick Reference)

## Problem Severity Summary

| Priority | Category | Impact | Current State | Target State |
|----------|----------|--------|---|---|
| 🔴 CRITICAL | Memgraph Connection | 18/27 tests fail | No persistent connection | Auto-reconnect with pooling |
| 🔴 CRITICAL | Query Error Reporting | Silent failures | Empty results on error | Structured error objects |
| 🟠 HIGH | Cypher Validation | Invalid queries pass | No validation | Pre-execution validation |
| 🟠 HIGH | Query Accuracy | ~40% work first try | LLM guessing | Schema-informed generation |
| 🟠 HIGH | Concurrent Performance | 50s for 3 queries | No queuing/caching | <15s with caching |
| 🟡 MEDIUM | Semantic Understanding | Multi-step queries fail | Basic LLM | Intent-aware generation |
| 🟡 MEDIUM | Security | Relies on LLM | Behavioral | Structural validation |
| 🟡 MEDIUM | Error Recovery | Complete failure | No fallbacks | Graceful degradation |
| 🔵 LOW | Monitoring | No visibility | No logs/metrics | Full analytics dashboard |

---

## Critical Path to Production (8 weeks)

### Week 1-2: Fix Core Issues
**Deliverable:** Move from 29.6% to >90% pass rate

**Work Items:**
- [ ] Fix `MemgraphIngestor` connection persistence
- [ ] Add connection pooling
- [ ] Implement `_ensure_connection()` health checks
- [ ] Change silent failures to structured error responses
- [ ] Add `error`, `error_code`, `success` fields to `QueryResult`

**Estimated Effort:** 40 hours
**Files to Modify:**
- `codebase_rag/services/graph_service.py` (MemgraphIngestor)
- `codebase_rag/tools/codebase_query.py` (QueryResult)
- `codebase_rag/mcp/tools.py` (error handling)

**Testing:** Run stress test again, expect 25 passes

---

### Week 3-4: Improve Query Generation
**Deliverable:** 80%+ query accuracy, better error messages

**Work Items:**
- [ ] Create `CypherValidator` class
- [ ] Build `GRAPH_SCHEMA` registry with actual node/relationship types
- [ ] Add validation before query execution
- [ ] Enhance `CYPHER_SYSTEM_PROMPT` with schema details and examples
- [ ] Implement `CypherGeneratorWithCache` for result caching
- [ ] Add schema injection into LLM context

**Estimated Effort:** 45 hours
**Files to Create:**
- `codebase_rag/services/cypher_validator.py` (new)
- `codebase_rag/schema.py` (new)
- `codebase_rag/services/query_cache.py` (new)

**Files to Modify:**
- `codebase_rag/services/llm.py` (enhance system prompt)
- `codebase_rag/prompts.py` (add examples, schema)

**Testing:** Queries N1-N5 should show improved accuracy, cache should have >40% hit rate

---

### Week 5-6: Handle Concurrency & Performance
**Deliverable:** 3 concurrent queries complete in <15s

**Work Items:**
- [ ] Implement `LLMRequestQueue` with semaphore
- [ ] Add request batching for database
- [ ] Implement `QueryBatcher` for multi-query transactions
- [ ] Add exponential backoff retry logic
- [ ] Tune connection pool size (start with 5)

**Estimated Effort:** 35 hours
**Files to Create:**
- `codebase_rag/services/llm_queue.py` (new)
- `codebase_rag/services/query_batcher.py` (new)

**Files to Modify:**
- `codebase_rag/services/llm.py` (use queue)
- `codebase_rag/services/graph_service.py` (connection pooling)

**Testing:** P4 concurrent test should drop from 50s to <15s

---

### Week 7-8: Robustness & Polish
**Deliverable:** >95% of requests return meaningful response

**Work Items:**
- [ ] Implement fallback query patterns
- [ ] Add comprehensive input validation
- [ ] Implement rate limiting
- [ ] Add timeout handling with graceful degradation
- [ ] Create monitoring dashboard (basic)
- [ ] Document security measures

**Estimated Effort:** 40 hours
**Files to Create:**
- `codebase_rag/security/input_validator.py` (new)
- `codebase_rag/services/fallback_executor.py` (new)
- `codebase_rag/middleware/rate_limiter.py` (new)

**Files to Modify:**
- `codebase_rag/tools/codebase_query.py` (fallback logic)
- `codebase_rag/mcp/server.py` (rate limiting)

**Testing:** All 5 edge case tests + all error scenarios

---

## Quick Fix Guide (Start Here)

### Issue #1: "Not connected to Memgraph" Error
**Root Cause:** `MemgraphIngestor` loses connection between tool calls

**Quick Fix (30 min):**
```python
# In codebase_rag/services/graph_service.py
class MemgraphIngestor:
    def __init__(self, host, port, batch_size=1000):
        self.host = host
        self.port = port
        self.batch_size = batch_size
        self._connection = None  # Add this

    def _get_connection(self):
        """Get or create connection"""
        if self._connection is None or not self._connection.is_alive():
            self._connection = self._connect()
        return self._connection

    # Update all query methods to use _get_connection()
    # BEFORE: self.connection.query(cypher)
    # AFTER:  self._get_connection().query(cypher)
```

**Proper Fix (4 hours):**
- Implement connection pooling
- Add health checks
- Add automatic reconnection
- See Week 1-2 items above

---

### Issue #2: Silent Failures (Empty Results Instead of Error)
**Root Cause:** Exceptions caught and swallowed, user sees no results

**Quick Fix (1 hour):**
```python
# In codebase_rag/tools/codebase_query.py, around line 46-94
# BEFORE:
except Exception as e:
    logger.error(f"Error during query execution: {e}")
    return QueryResult(results=[], summary="Error")

# AFTER:
except ConnectionError as e:
    return QueryResult(
        results=[],
        summary=f"Database connection failed: {e}",
        success=False,
        error_code="DB_CONNECTION_ERROR"
    )
except Exception as e:
    return QueryResult(
        results=[],
        summary=f"Query failed: {e}",
        success=False,
        error_code="QUERY_FAILED"
    )
```

---

### Issue #3: Cypher Queries Don't Match Schema
**Root Cause:** LLM generates Cypher without schema knowledge

**Quick Fix (2 hours):**
```python
# In codebase_rag/prompts.py, enhance CYPHER_SYSTEM_PROMPT:

CYPHER_SYSTEM_PROMPT = """
...existing text...

IMPORTANT: Use these exact relationship types and node types:
- Nodes: File, Module, Class, Function, Method
- Relationships: DEFINES, DEFINES_METHOD, CALLS, IMPORTS, INHERITS
- Qualified names use full path: 'codebase_rag.mcp.tools.MCPToolsRegistry'

Examples of CORRECT queries:
1. Find Python files: MATCH (f:File) WHERE f.extension = '.py' RETURN f
2. Module functions: MATCH (m:Module {qualified_name: 'codebase_rag.tools'})-[:DEFINES]->(f:Function) RETURN f
3. Method calls: MATCH (m:Method)-[:CALLS]->(f:Function) RETURN m, f
"""
```

---

### Issue #4: Concurrent Queries Are Slow
**Root Cause:** Single-threaded LLM request handling

**Quick Fix (1 hour):**
```python
# In codebase_rag/mcp/tools.py
# Create a simple cache:
from functools import lru_cache

class MCPToolsRegistry:
    def __init__(self, ...):
        self.query_cache = {}

    async def query_code_graph(self, nl_query: str):
        # Check cache
        cache_key = nl_query.lower().strip()
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]

        # Generate & cache
        result = await self._query_uncached(nl_query)
        self.query_cache[cache_key] = result
        return result
```

**Proper Fix:** See Week 3-4 items (implement `CypherGeneratorWithCache`)

---

## Testing Checklist

### Before Starting
- [ ] Memgraph running: `docker ps | grep memgraph`
- [ ] Codebase indexed: `mcp__code-graph__index_repository`
- [ ] Configuration set: `.env` file with `CYPHER_MODEL=qwen2.5-coder:32b`

### After Week 1-2 (Critical Fixes)
- [ ] Run stress test: `python stress_test.py`
- [ ] Expect: >20 passes (was 8)
- [ ] Check: All queries show errors OR results, never silent failure

### After Week 3-4 (Query Generation)
- [ ] Run stress test again
- [ ] Expect: >23 passes
- [ ] Check: N1-N5 queries return meaningful results
- [ ] Verify: Cache hit rate in logs

### After Week 5-6 (Concurrency)
- [ ] Run P4 test (concurrent): Should be <15s (was 50s)
- [ ] Check: P1-P3 still <target times
- [ ] Verify: Connection pool healthy

### After Week 7-8 (Robustness)
- [ ] Run all edge cases: 5/5 pass
- [ ] Check: Error messages are helpful
- [ ] Verify: Rate limiting works

### Final Validation
- [ ] All 27 tests pass (or have clear reason why partial)
- [ ] Pass rate: >90%
- [ ] No silent failures
- [ ] Clear error messages throughout

---

## Success Metrics

### Before (Current)
```
Total Tests: 27
Passed: 8 (29.6%)
Partial: 18 (66.7%)
Failed: 1 (3.7%)
User Experience: Silent failures, cryptic errors
```

### Target (End of Week 8)
```
Total Tests: 27
Passed: 25+ (>92%)
Partial: <2 (expected for very unusual queries)
Failed: 0
User Experience: Clear errors, helpful recovery suggestions
```

### Performance Targets
| Metric | Current | Target |
|--------|---------|--------|
| Simple query | 2.6s | <3s |
| Complex query | 5.8s | <10s |
| 3 concurrent | 50s | <15s |
| Cache hit rate | 0% | >40% |
| Error clarity | Silent | 100% clear messages |

---

## Questions & Support

### "Where do I start?"
1. Fix connection issue (Week 1, 30 min)
2. Fix error reporting (Week 1, 1 hour)
3. Run stress test to verify

### "Which files matter most?"
Priority by frequency of changes:
1. `codebase_rag/services/graph_service.py` (MemgraphIngestor)
2. `codebase_rag/services/llm.py` (CypherGenerator)
3. `codebase_rag/tools/codebase_query.py` (query execution)

### "How do I test changes?"
```bash
# Run full stress test
source .venv/bin/activate
python stress_test.py

# Run specific test category
# (Modify stress_test.py to run just one test)

# Check logs
tail -f /Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag/.codebase-intelligence/code-graph/update.log
```

### "What if I get stuck?"
1. Check STRESS_TEST_ANALYSIS.md for detailed explanation
2. Look at test output in infrastructure/benchmarks/
3. Review the specific "Upgrade Recommendations" section for that issue
