# Neo4j/MCP readiness, 11 November 2026

Current result: local installation discovered; live connection and MCP integration
not verified in this round. The installed kernel JAR is 2026.10.2. Previous
successful connection is historical evidence only. Do not create another instance.
No credentials, database contents, installation or permissions were changed.

The official [MCP README](https://github.com/neo4j/mcp) documents schema inspection,
read/write Cypher and GDS procedure discovery. `NEO4J_MCP_READ_ONLY=true` disables
the write tool. Read classification uses EXPLAIN; incorrectly classified custom
procedures can bypass it. This setting is not a substitute for database permissions.
The README documents PyPI package `neo4j-mcp-server` and Python module startup;
no package was installed here and no version has been selected or pinned.

The official [security guidance](https://neo4j.com/docs/mcp/current/security/)
recommends a restricted account and query review. Existing owner authorization
does not permit silently changing system/database permissions. A local STDIO
connection is the candidate bridge; no network exposure is needed for that choice.

The repository [NOTICE](https://github.com/neo4j/mcp/blob/main/NOTICE.txt) describes
GPLv3 and conditions under Neo4j cloud/software agreements; the
[LICENSE](https://github.com/neo4j/mcp/blob/main/LICENSE.txt) must accompany any
redistribution decision. This is the MCP repository's licensing information,
not confirmation of this installed Desktop Enterprise instance's entitlement.
Verify the applicable Desktop terms before a change or redistribution.

For the research, deterministic family-key-family traversal must be compared
with matched posting-list lookup. MCP is only a tool interface. Neither database
choice nor enabling MCP supplies a retrieval result or a novelty claim.

Next: map the existing installation to the owner's instance name, verify current
local startup and RETURN 1 within existing rights, then pin a bridge only if
needed. Import/write remains outside the approved two-job R3 first-stage package.
