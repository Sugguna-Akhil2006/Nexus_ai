"""Orchestrates research ingestion, Knowledge Graph updates, and report building workflows."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.profile.models import KnowledgeProfile
from backend.intelligence.knowledge.knowledge_graph import KnowledgeGraphEngine
from backend.intelligence.knowledge.entity_node import EntityNode
from backend.intelligence.knowledge.relationship import Relationship
from backend.intelligence.knowledge.models import EntityType, RelationshipType
from backend.intelligence.research.models import ResearchAnalysisReport, ResearchPaperMetadata
from backend.intelligence.research.source_manager import SourceManager
from backend.intelligence.research.evidence_engine import EvidenceEngine
from backend.intelligence.research.comparison_engine import ComparisonEngine
from backend.intelligence.research.citation_manager import CitationManager
from backend.intelligence.research.research_report import ResearchReportBuilder
from backend.intelligence.research.research_agent import ResearchAgent


class ResearchWorkflow:
    """Orchestrates the entire multi-paper analysis, comparison, and semantic synthesis workflow."""

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        self.source_manager = SourceManager()
        self.evidence_engine = EvidenceEngine()
        self.comparison_engine = ComparisonEngine()
        self.citation_manager = CitationManager()
        self.report_builder = ResearchReportBuilder()
        self.agent = ResearchAgent()
        self.kg_engine = KnowledgeGraphEngine(db_path)
        self.event_bus = EventBus()

    def run_analysis(
        self,
        workspace_id: str,
        document_ids: List[str],
        profile: Optional[KnowledgeProfile] = None
    ) -> ResearchAnalysisReport:
        """Processes documents, updates Knowledge Graph, and compiles research reports."""
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ResearchWorkflow",
            payload={
                "event": "research.analysis.started",
                "workspace_id": workspace_id,
                "document_ids": document_ids,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))

        # 1. Load and parse sources metadata
        papers_meta = self.source_manager.get_sources_metadata(workspace_id, document_ids)
        
        # Gather raw texts for detailed sub-scanning
        raw_texts = {}
        for did in document_ids:
            doc_tuple = self.source_manager.doc_cache.get_document(did)
            if doc_tuple:
                raw_texts[did] = doc_tuple[1]

        # 2. Extract evidence claims and inline citations
        all_evidence = []
        all_citations = []
        all_suggested_reading = []
        
        for paper in papers_meta:
            text = raw_texts.get(paper.paper_id, "")
            
            # Claims
            evidence = self.evidence_engine.extract_evidence(paper, text)
            all_evidence.extend(evidence)
            
            # Citations & references
            citations, suggested = self.citation_manager.extract_citations_and_references(paper, text)
            all_citations.extend(citations)
            all_suggested_reading.extend(suggested)

        # 3. Multi-paper comparison analysis
        comparison_res = self.comparison_engine.compare_papers(papers_meta, all_evidence)

        # 4. Write summaries and findings via ResearchAgent
        exec_summary = self.agent.generate_executive_summary(papers_meta, all_evidence)
        key_findings = self.agent.generate_key_findings(papers_meta, all_evidence)
        research_gaps = self.agent.generate_research_gaps(papers_meta, all_evidence)

        # 5. Populate and Update the Knowledge Graph
        kg_updates = {}
        confidence_scores = {}
        
        for paper in papers_meta:
            # Register Research Paper node
            paper_node = EntityNode(
                node_id=f"paper-{paper.paper_id}",
                label=EntityType.RESEARCH_PAPER,
                name=paper.title,
                properties={
                    "venue": paper.venue or "Unknown Venue",
                    "published_date": paper.published_date or "2026"
                },
                confidence=1.0,
                evidence_sources=["ResearchPipeline"]
            )
            self.kg_engine.add_node(workspace_id, paper_node)
            confidence_scores[paper.title] = 1.0

            # Register Authors as Person nodes
            for author in paper.authors:
                author_slug = author.lower().replace(" ", "-")
                author_node = EntityNode(
                    node_id=f"person-{author_slug}",
                    label=EntityType.PERSON,
                    name=author,
                    confidence=1.0,
                    evidence_sources=["ResearchPipeline"]
                )
                self.kg_engine.add_node(workspace_id, author_node)

                # Link Person -> AUTHORED -> Research Paper
                self.kg_engine.add_relationship(workspace_id, Relationship(
                    relationship_id=f"rel-auth-{author_slug}-{paper.paper_id}",
                    source_id=f"person-{author_slug}",
                    target_id=f"paper-{paper.paper_id}",
                    relationship_type=RelationshipType.AUTHORED,
                    confidence=1.0,
                    evidence_sources=["ResearchPipeline"]
                ))

            # Register Keywords as Topic nodes
            for kw in paper.keywords:
                kw_slug = kw.lower().replace(" ", "-")
                topic_node = EntityNode(
                    node_id=f"topic-{kw_slug}",
                    label=EntityType.TOPIC,
                    name=kw,
                    confidence=0.9,
                    evidence_sources=["ResearchPipeline"]
                )
                self.kg_engine.add_node(workspace_id, topic_node)

                # Link Research Paper -> MENTIONS -> Topic
                self.kg_engine.add_relationship(workspace_id, Relationship(
                    relationship_id=f"rel-ment-{paper.paper_id}-{kw_slug}",
                    source_id=f"paper-{paper.paper_id}",
                    target_id=f"topic-{kw_slug}",
                    relationship_type=RelationshipType.MENTIONS,
                    confidence=0.9,
                    evidence_sources=["ResearchPipeline"]
                ))

        # Compile bibliography updates map
        kg_updates = {
            "papers": [f"paper-{p.paper_id}" for p in papers_meta],
            "topics": [f"topic-{kw.lower().replace(' ', '-')}" for p in papers_meta for kw in p.keywords]
        }

        # Run Knowledge Graph reasoning to infer missing links
        reasoning_res = self.kg_engine.run_reasoning(workspace_id)
        
        # 6. Synchronize with Unified Knowledge Profile (UKP)
        if profile:
            self.kg_engine.sync_profile(workspace_id, profile)

        # 7. Compile and build final ResearchAnalysisReport
        report = self.report_builder.compile_report(
            summary=exec_summary,
            findings=key_findings,
            evidence_matrix=all_evidence,
            comparison=comparison_res,
            topics=comparison_res.get("consensus_keywords", []),
            kg_updates=kg_updates,
            gaps=research_gaps,
            suggested_reading=sorted(list(set(all_suggested_reading))),
            citations=all_citations,
            confidence_scores=confidence_scores
        )

        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ResearchWorkflow",
            payload={
                "event": "research.analysis.completed",
                "workspace_id": workspace_id,
                "report_id": report.report_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))

        return report
