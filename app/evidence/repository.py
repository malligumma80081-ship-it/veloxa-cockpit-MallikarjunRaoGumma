"""SQLite repository for source files, evidence, entities, conflicts, decisions, assumptions, and risks."""
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.config import DB_PATH
from app.evidence.models import (
    Assumption,
    CockpitResponse,
    Conflict,
    EmployeeProfile,
    Entity,
    EntityAlias,
    Evidence,
    EvidenceCitation,
    ReconciliationDecision,
    RiskItem,
    SourceFile,
)


class EvidenceRepository:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.init_schema()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript("""
            CREATE TABLE IF NOT EXISTS source_files (
                source_id TEXT PRIMARY KEY,
                relative_path TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                release_day TEXT NOT NULL,
                release_date TEXT NOT NULL,
                document_date TEXT,
                content_hash TEXT NOT NULL,
                source_description TEXT,
                ingestion_status TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS evidence (
                evidence_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                source_file TEXT NOT NULL,
                locator TEXT NOT NULL,
                claim TEXT NOT NULL,
                claim_type TEXT NOT NULL,
                entity_ids TEXT NOT NULL, -- JSON array
                event_date TEXT,
                release_date TEXT NOT NULL,
                sensitivity TEXT NOT NULL,
                confidence TEXT NOT NULL,
                attribution TEXT,
                raw_value TEXT,
                normalized_value TEXT,
                normalization_note TEXT,
                FOREIGN KEY(source_id) REFERENCES source_files(source_id)
            );

            CREATE TABLE IF NOT EXISTS entities (
                entity_id TEXT PRIMARY KEY,
                canonical_name TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                department TEXT,
                title TEXT,
                email TEXT,
                location TEXT,
                manager_id TEXT,
                join_date TEXT,
                exit_date TEXT,
                status TEXT
            );

            CREATE TABLE IF NOT EXISTS entity_aliases (
                alias_id TEXT PRIMARY KEY,
                alias_text TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                source_id TEXT NOT NULL,
                seen_in TEXT NOT NULL,
                kind TEXT NOT NULL,
                confidence TEXT NOT NULL,
                reason TEXT,
                FOREIGN KEY(entity_id) REFERENCES entities(entity_id)
            );

            CREATE TABLE IF NOT EXISTS conflicts (
                conflict_id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                entity_id TEXT,
                competing_claims TEXT NOT NULL, -- JSON array
                evidence_ids TEXT NOT NULL, -- JSON array
                status TEXT NOT NULL,
                resolution_decision_id TEXT
            );

            CREATE TABLE IF NOT EXISTS reconciliation_decisions (
                decision_id TEXT PRIMARY KEY,
                conflict_id TEXT NOT NULL,
                chosen_interpretation TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                decision_date TEXT NOT NULL,
                decision_author TEXT NOT NULL,
                confidence TEXT NOT NULL,
                what_would_change_mind TEXT NOT NULL,
                revisit_condition TEXT,
                FOREIGN KEY(conflict_id) REFERENCES conflicts(conflict_id)
            );

            CREATE TABLE IF NOT EXISTS assumptions (
                assumption_id TEXT PRIMARY KEY,
                date_recorded TEXT NOT NULL,
                assumption_text TEXT NOT NULL,
                supporting_locator TEXT NOT NULL,
                evidence_ids TEXT NOT NULL, -- JSON array
                confidence TEXT NOT NULL,
                status TEXT NOT NULL,
                what_would_change_mind TEXT NOT NULL,
                is_invented_agent_detail INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS employee_profiles (
                employee_id TEXT PRIMARY KEY,
                canonical_name TEXT NOT NULL,
                department TEXT NOT NULL,
                title TEXT NOT NULL,
                email TEXT NOT NULL,
                manager_id TEXT,
                location TEXT NOT NULL,
                status TEXT NOT NULL,
                join_date TEXT NOT NULL,
                exit_date TEXT,
                verified_facts TEXT NOT NULL, -- JSON array
                workload_evidence_ids TEXT NOT NULL, -- JSON array
                history_evidence_ids TEXT NOT NULL, -- JSON array
                unknown_fields TEXT NOT NULL, -- JSON array
                simulated_persona TEXT, -- JSON object
                as_of_date TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS risks (
                risk_id TEXT PRIMARY KEY,
                risk_title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT NOT NULL,
                likelihood TEXT NOT NULL,
                evidence_ids TEXT NOT NULL, -- JSON array
                locators TEXT NOT NULL, -- JSON array
                potential_impact TEXT NOT NULL,
                mitigation_or_next_check TEXT NOT NULL,
                rank_score REAL NOT NULL,
                rank_explanation TEXT NOT NULL,
                as_of_date TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS answer_audit (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                as_of_date TEXT NOT NULL,
                status TEXT NOT NULL,
                confidence TEXT NOT NULL,
                answer TEXT NOT NULL,
                citations_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            conn.commit()

    def upsert_source_file(self, sf: SourceFile) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO source_files (source_id, relative_path, filename, file_type, release_day, release_date, document_date, content_hash, source_description, ingestion_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
                content_hash=excluded.content_hash,
                ingestion_status=excluded.ingestion_status,
                document_date=excluded.document_date
            """, (sf.source_id, sf.relative_path, sf.filename, sf.file_type, sf.release_day, sf.release_date, sf.document_date, sf.content_hash, sf.source_description, sf.ingestion_status))
            conn.commit()

    def upsert_evidence(self, e: Evidence) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO evidence (evidence_id, source_id, source_file, locator, claim, claim_type, entity_ids, event_date, release_date, sensitivity, confidence, attribution, raw_value, normalized_value, normalization_note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(evidence_id) DO UPDATE SET
                claim=excluded.claim,
                locator=excluded.locator,
                confidence=excluded.confidence,
                sensitivity=excluded.sensitivity,
                raw_value=excluded.raw_value,
                normalized_value=excluded.normalized_value
            """, (e.evidence_id, e.source_id, e.source_file, e.locator, e.claim, e.claim_type, json.dumps(e.entity_ids), e.event_date, e.release_date, e.sensitivity, e.confidence, e.attribution, e.raw_value, e.normalized_value, e.normalization_note))
            conn.commit()

    def upsert_entity(self, ent: Entity) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO entities (entity_id, canonical_name, entity_type, department, title, email, location, manager_id, join_date, exit_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(entity_id) DO UPDATE SET
                canonical_name=excluded.canonical_name,
                title=excluded.title,
                department=excluded.department,
                status=excluded.status
            """, (ent.entity_id, ent.canonical_name, ent.entity_type, ent.department, ent.title, ent.email, ent.location, ent.manager_id, ent.join_date, ent.exit_date, ent.status))
            conn.commit()

    def upsert_entity_alias(self, alias: EntityAlias) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO entity_aliases (alias_id, alias_text, entity_id, source_id, seen_in, kind, confidence, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(alias_id) DO UPDATE SET
                alias_text=excluded.alias_text,
                entity_id=excluded.entity_id,
                confidence=excluded.confidence,
                reason=excluded.reason
            """, (alias.alias_id, alias.alias_text, alias.entity_id, alias.source_id, alias.seen_in, alias.kind, alias.confidence, alias.reason))
            conn.commit()

    def upsert_conflict(self, conf: Conflict) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO conflicts (conflict_id, topic, entity_id, competing_claims, evidence_ids, status, resolution_decision_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(conflict_id) DO UPDATE SET
                competing_claims=excluded.competing_claims,
                evidence_ids=excluded.evidence_ids,
                status=excluded.status,
                resolution_decision_id=excluded.resolution_decision_id
            """, (conf.conflict_id, conf.topic, conf.entity_id, json.dumps(conf.competing_claims), json.dumps(conf.evidence_ids), conf.status, conf.resolution_decision_id))
            conn.commit()

    def upsert_reconciliation_decision(self, dec: ReconciliationDecision) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO reconciliation_decisions (decision_id, conflict_id, chosen_interpretation, reasoning, decision_date, decision_author, confidence, what_would_change_mind, revisit_condition)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(decision_id) DO UPDATE SET
                chosen_interpretation=excluded.chosen_interpretation,
                reasoning=excluded.reasoning,
                confidence=excluded.confidence,
                what_would_change_mind=excluded.what_would_change_mind
            """, (dec.decision_id, dec.conflict_id, dec.chosen_interpretation, dec.reasoning, dec.decision_date, dec.decision_author, dec.confidence, dec.what_would_change_mind, dec.revisit_condition))
            conn.commit()

    def upsert_assumption(self, asm: Assumption) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO assumptions (assumption_id, date_recorded, assumption_text, supporting_locator, evidence_ids, confidence, status, what_would_change_mind, is_invented_agent_detail)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(assumption_id) DO UPDATE SET
                assumption_text=excluded.assumption_text,
                confidence=excluded.confidence,
                status=excluded.status,
                what_would_change_mind=excluded.what_would_change_mind
            """, (asm.assumption_id, asm.date_recorded, asm.assumption_text, asm.supporting_locator, json.dumps(asm.evidence_ids), asm.confidence, asm.status, asm.what_would_change_mind, 1 if asm.is_invented_agent_detail else 0))
            conn.commit()

    def upsert_employee_profile(self, p: EmployeeProfile) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO employee_profiles (employee_id, canonical_name, department, title, email, manager_id, location, status, join_date, exit_date, verified_facts, workload_evidence_ids, history_evidence_ids, unknown_fields, simulated_persona, as_of_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(employee_id) DO UPDATE SET
                department=excluded.department,
                title=excluded.title,
                verified_facts=excluded.verified_facts,
                workload_evidence_ids=excluded.workload_evidence_ids,
                history_evidence_ids=excluded.history_evidence_ids,
                unknown_fields=excluded.unknown_fields,
                simulated_persona=excluded.simulated_persona,
                as_of_date=excluded.as_of_date
            """, (p.employee_id, p.canonical_name, p.department, p.title, p.email, p.manager_id, p.location, p.status, p.join_date, p.exit_date, json.dumps(p.verified_facts), json.dumps(p.workload_evidence_ids), json.dumps(p.history_evidence_ids), json.dumps(p.unknown_fields), json.dumps(p.simulated_persona or {}), p.as_of_date))
            conn.commit()

    def upsert_risk(self, r: RiskItem) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO risks (risk_id, risk_title, category, description, severity, likelihood, evidence_ids, locators, potential_impact, mitigation_or_next_check, rank_score, rank_explanation, as_of_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(risk_id) DO UPDATE SET
                risk_title=excluded.risk_title,
                description=excluded.description,
                severity=excluded.severity,
                likelihood=excluded.likelihood,
                rank_score=excluded.rank_score,
                rank_explanation=excluded.rank_explanation
            """, (r.risk_id, r.risk_title, r.category, r.description, r.severity, r.likelihood, json.dumps(r.evidence_ids), json.dumps(r.locators), r.potential_impact, r.mitigation_or_next_check, r.rank_score, r.rank_explanation, r.as_of_date))
            conn.commit()

    # Query methods
    def get_evidence_point_in_time(self, as_of_date: str, exclude_restricted: bool = True) -> List[Evidence]:
        """Fetch evidence eligible as of a specific release date cutoff."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM evidence WHERE release_date <= ?"
            params: List[Any] = [as_of_date]
            if exclude_restricted:
                query += " AND sensitivity != 'restricted'"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [
                Evidence(
                    evidence_id=r["evidence_id"],
                    source_id=r["source_id"],
                    source_file=r["source_file"],
                    locator=r["locator"],
                    claim=r["claim"],
                    claim_type=r["claim_type"],
                    entity_ids=json.loads(r["entity_ids"]),
                    event_date=r["event_date"],
                    release_date=r["release_date"],
                    sensitivity=r["sensitivity"],
                    confidence=r["confidence"],
                    attribution=r["attribution"],
                    raw_value=r["raw_value"],
                    normalized_value=r["normalized_value"],
                    normalization_note=r["normalization_note"],
                )
                for r in rows
            ]

    def get_all_entities(self) -> List[Entity]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM entities")
            return [Entity(**dict(r)) for r in cursor.fetchall()]

    def get_entity_by_id(self, entity_id: str) -> Optional[Entity]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM entities WHERE entity_id = ?", (entity_id,))
            r = cursor.fetchone()
            return Entity(**dict(r)) if r else None

    def get_aliases(self) -> List[EntityAlias]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM entity_aliases")
            return [EntityAlias(**dict(r)) for r in cursor.fetchall()]

    def get_conflicts(self) -> List[Conflict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM conflicts")
            rows = cursor.fetchall()
            return [
                Conflict(
                    conflict_id=r["conflict_id"],
                    topic=r["topic"],
                    entity_id=r["entity_id"],
                    competing_claims=json.loads(r["competing_claims"]),
                    evidence_ids=json.loads(r["evidence_ids"]),
                    status=r["status"],
                    resolution_decision_id=r["resolution_decision_id"],
                )
                for r in rows
            ]

    def get_decisions(self) -> List[ReconciliationDecision]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reconciliation_decisions")
            return [ReconciliationDecision(**dict(r)) for r in cursor.fetchall()]

    def get_assumptions(self) -> List[Assumption]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM assumptions")
            rows = cursor.fetchall()
            return [
                Assumption(
                    assumption_id=r["assumption_id"],
                    date_recorded=r["date_recorded"],
                    assumption_text=r["assumption_text"],
                    supporting_locator=r["supporting_locator"],
                    evidence_ids=json.loads(r["evidence_ids"]),
                    confidence=r["confidence"],
                    status=r["status"],
                    what_would_change_mind=r["what_would_change_mind"],
                    is_invented_agent_detail=bool(r["is_invented_agent_detail"]),
                )
                for r in rows
            ]

    def get_employee_profiles(self) -> List[EmployeeProfile]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employee_profiles")
            rows = cursor.fetchall()
            return [
                EmployeeProfile(
                    employee_id=r["employee_id"],
                    canonical_name=r["canonical_name"],
                    department=r["department"],
                    title=r["title"],
                    email=r["email"],
                    manager_id=r["manager_id"],
                    location=r["location"],
                    status=r["status"],
                    join_date=r["join_date"],
                    exit_date=r["exit_date"],
                    verified_facts=json.loads(r["verified_facts"]),
                    workload_evidence_ids=json.loads(r["workload_evidence_ids"]),
                    history_evidence_ids=json.loads(r["history_evidence_ids"]),
                    unknown_fields=json.loads(r["unknown_fields"]),
                    simulated_persona=json.loads(r["simulated_persona"] or "{}"),
                    as_of_date=r["as_of_date"],
                )
                for r in rows
            ]

    def get_risks(self, as_of_date: str) -> List[RiskItem]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM risks WHERE as_of_date <= ? ORDER BY rank_score DESC", (as_of_date,))
            rows = cursor.fetchall()
            return [
                RiskItem(
                    risk_id=r["risk_id"],
                    risk_title=r["risk_title"],
                    category=r["category"],
                    description=r["description"],
                    severity=r["severity"],
                    likelihood=r["likelihood"],
                    evidence_ids=json.loads(r["evidence_ids"]),
                    locators=json.loads(r["locators"]),
                    potential_impact=r["potential_impact"],
                    mitigation_or_next_check=r["mitigation_or_next_check"],
                    rank_score=r["rank_score"],
                    rank_explanation=r["rank_explanation"],
                    as_of_date=r["as_of_date"],
                )
                for r in rows
            ]

    def log_audit(self, question: str, as_of_date: str, resp: CockpitResponse) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO answer_audit (question, as_of_date, status, confidence, answer, citations_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (question, as_of_date, resp.status, resp.confidence, resp.answer, json.dumps([c.model_dump() for c in resp.evidence])))
            conn.commit()
