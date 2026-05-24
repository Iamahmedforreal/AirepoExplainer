"""
Write code graph nodes and edges to Neo4j.
"""
from neo4j import GraphDatabase

from app.config.app_config import settings


class Neo4jGraphWriter:
    def __init__(self):
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    def close(self):
        self._driver.close()

    def clear_repo(self, repo_id: str) -> None:
        with self._driver.session() as session:
            session.run(
                "MATCH (r:Repo {repoId: $repoId}) DETACH DELETE r",
                repoId=repo_id,
            )

    def write_graph(
        self,
        repo_id: str,
        files: list[dict],
        chunks: list[dict],
        connections: list[dict],
    ) -> None:
        with self._driver.session() as session:
            session.run("MERGE (r:Repo {repoId: $repoId})", repoId=repo_id)

            for f in files:
                session.run(
                    """
                    MATCH (r:Repo {repoId: $repoId})
                    MERGE (file:File {repoId: $repoId, path: $path})
                    MERGE (r)-[:CONTAINS]->(file)
                    """,
                    repoId=repo_id,
                    path=f["path"],
                )

            for chunk in chunks:
                session.run(
                    """
                    MATCH (file:File {repoId: $repoId, path: $path})
                    MERGE (s:Symbol {repoId: $repoId, chunkId: $chunkId})
                    SET s.fullName = $fullName,
                        s.kind = $kind,
                        s.name = $name,
                        s.startLine = $startLine,
                        s.endLine = $endLine
                    MERGE (file)-[:DEFINES]->(s)
                    """,
                    repoId=repo_id,
                    path=chunk["path"],
                    chunkId=chunk["id"],
                    fullName=chunk["fullName"],
                    kind=chunk["type"],
                    name=chunk["name"],
                    startLine=chunk["startLine"],
                    endLine=chunk["endLine"],
                )

            for conn in connections:
                rel_type = "IMPORTS" if conn["connectionType"] == "import" else "CALLS"
                params = {
                    "repoId": repo_id,
                    "sourceChunkId": conn["sourceChunkId"],
                    "targetSymbol": conn["targetSymbol"],
                }
                if conn.get("targetChunkId"):
                    session.run(
                        f"""
                        MATCH (src:Symbol {{repoId: $repoId, chunkId: $sourceChunkId}})
                        MATCH (tgt:Symbol {{repoId: $repoId, chunkId: $targetChunkId}})
                        MERGE (src)-[rel:{rel_type}]->(tgt)
                        SET rel.resolved = true
                        """,
                        targetChunkId=conn["targetChunkId"],
                        **params,
                    )
                else:
                    session.run(
                        f"""
                        MATCH (src:Symbol {{repoId: $repoId, chunkId: $sourceChunkId}})
                        MERGE (tgt:Symbol {{repoId: $repoId, fullName: $targetSymbol}})
                        ON CREATE SET tgt.name = $targetSymbol, tgt.kind = 'unresolved'
                        MERGE (src)-[rel:{rel_type}]->(tgt)
                        SET rel.resolved = false
                        """,
                        **params,
                    )


def write_repo_graph(repo_id: str, files: list[dict], chunks: list[dict], connections: list[dict]) -> None:
    writer = Neo4jGraphWriter()
    try:
        writer.clear_repo(repo_id)
        writer.write_graph(repo_id, files, chunks, connections)
    finally:
        writer.close()
