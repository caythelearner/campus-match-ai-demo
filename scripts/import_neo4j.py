from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def batched(rows: list[dict[str, str]], batch_size: int):
    for idx in range(0, len(rows), batch_size):
        yield rows[idx : idx + batch_size]


def safe_token(value: str) -> str:
    if not value.replace("_", "").isalnum():
        raise ValueError(f"Unsafe Cypher token: {value}")
    return value


def import_nodes_by_label(tx, label: str, rows: list[dict[str, str]]) -> None:
    label = safe_token(label)
    tx.run(
        f"""
        UNWIND $rows AS row
        MERGE (n:CampusMatchNode {{node_id: row.node_id}})
        SET n:{label}
        SET n += row,
            n.node_label = row.label
        """,
        rows=rows,
    )


def import_relationships_by_type(tx, relation: str, rows: list[dict[str, str]]) -> None:
    relation = safe_token(relation)
    query = f"""
    UNWIND $rows AS row
    MATCH (s:CampusMatchNode {{node_id: row.source_id}})
    MATCH (t:CampusMatchNode {{node_id: row.target_id}})
    MERGE (s)-[r:{relation} {{rel_id: row.rel_id}}]->(t)
    SET r += row
    """
    tx.run(query, rows=rows)


def create_constraint(tx) -> None:
    tx.run(
        """
        CREATE CONSTRAINT campus_match_node_id IF NOT EXISTS
        FOR (n:CampusMatchNode) REQUIRE n.node_id IS UNIQUE
        """
    )


def clear_previous_trace(tx) -> None:
    tx.run(
        """
        MATCH (n:CampusMatchNode {source: 'campus_match_ai'})
        DETACH DELETE n
        """
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Campus Match AI knowledge graph into Neo4j.")
    parser.add_argument("--uri", default=os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    parser.add_argument("--user", default=os.getenv("NEO4J_USER", "neo4j"))
    parser.add_argument("--password", default=os.getenv("NEO4J_PASSWORD", "password"))
    parser.add_argument("--database", default=os.getenv("NEO4J_DATABASE", "neo4j"))
    parser.add_argument("--trace-dir", default=str(ROOT / "outputs/neo4j"))
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--clear", action="store_true", help="Delete previous Campus Match AI nodes before import.")
    args = parser.parse_args()

    try:
        from neo4j import GraphDatabase
    except ImportError as exc:
        raise SystemExit("Missing dependency: pip install neo4j") from exc

    trace_dir = Path(args.trace_dir)
    nodes_path = trace_dir / "campus_match_ai_nodes.csv"
    relationships_path = trace_dir / "campus_match_ai_relationships.csv"
    if not nodes_path.exists() or not relationships_path.exists():
        raise SystemExit("Neo4j trace files not found. Run scripts/run_pipeline.py first.")

    nodes = read_csv(nodes_path)
    relationships = read_csv(relationships_path)
    by_label: dict[str, list[dict[str, str]]] = {}
    for row in nodes:
        by_label.setdefault(row["label"], []).append(row)
    by_relation: dict[str, list[dict[str, str]]] = {}
    for row in relationships:
        by_relation.setdefault(row["relation"], []).append(row)

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    with driver:
        with driver.session(database=args.database) as session:
            session.execute_write(create_constraint)
            if args.clear:
                session.execute_write(clear_previous_trace)
            for label, node_rows in sorted(by_label.items()):
                for batch in batched(node_rows, args.batch_size):
                    session.execute_write(import_nodes_by_label, label, batch)
            for relation, rel_rows in sorted(by_relation.items()):
                for batch in batched(rel_rows, args.batch_size):
                    session.execute_write(import_relationships_by_type, relation, batch)

    print("Neo4j import completed.")
    print(f"nodes: {len(nodes)}")
    print(f"relationships: {len(relationships)}")
    print(f"uri: {args.uri}")
    print(f"database: {args.database}")
