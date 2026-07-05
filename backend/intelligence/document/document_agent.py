"""Flagship Document Intelligence Agent orchestrating multi-document extraction pipelines."""

import uuid
import re
from typing import Dict, List, Tuple, Any, Optional
from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.document.document_model import (
    DocumentAnalysisReport,
    DocumentMetadata,
    SummaryDetail,
    Topic,
    Entity,
    Citation,
    SimilarityMapping,
    ExtractedKnowledgeItem
)
from backend.intelligence.document.chunk_manager import ChunkManager, TextChunk
from backend.intelligence.document.citation_engine import CitationEngine
from backend.intelligence.document.summary_engine import SummaryEngine
from backend.intelligence.document.document_metadata import MetadataExtractor
from backend.intelligence.document.document_workflow import DocumentStageNames, StageExecutionError
from backend.intelligence.document.report import DocumentReportBuilder


class DocumentAgent:
    """Orchestrates structured document loading, chunking, parsing, and similarities comparisons."""

    def __init__(self) -> None:
        self.chunk_manager = ChunkManager()
        self.citation_engine = CitationEngine()
        self.summary_engine = SummaryEngine()
        self.metadata_extractor = MetadataExtractor()
        self.report_builder = DocumentReportBuilder()
        self.event_bus = EventBus()

    def analyze_documents(
        self,
        workspace_id: str,
        documents: Dict[str, Tuple[str, str]],  # Key: document_id -> (filename, raw_content)
        options: Optional[Dict[str, Any]] = None
    ) -> DocumentAnalysisReport:
        """Runs the document analysis pipeline over single or multiple documents.

        Args:
            workspace_id: Associated workspace context.
            documents: Dict containing document filename and string contents.
            options: Ingestion parameter overrides.

        Returns:
            DocumentAnalysisReport: Compiled report results.
        """
        opts = options or {}
        custom_prompt = opts.get("custom_prompt")
        
        if not documents:
            raise StageExecutionError(DocumentStageNames.LOADER, "No documents provided for analysis.")

        # Stage 1 & 2: Load and extract Metadata and Chunks for each document
        metadata_map: Dict[str, DocumentMetadata] = {}
        all_chunks: List[TextChunk] = []
        doc_chunks_map: Dict[str, List[TextChunk]] = {}
        doc_names_map: Dict[str, str] = {}
        doc_keywords: Dict[str, List[str]] = {}

        for doc_id, (filename, content) in documents.items():
            if not content.strip():
                raise StageExecutionError(
                    DocumentStageNames.LOADER,
                    f"Document '{filename}' content is empty."
                )

            # Metadata Ingestion stage
            try:
                meta = self.metadata_extractor.extract_metadata(content, filename, opts.get("custom_meta"))
                metadata_map[doc_id] = meta
                doc_names_map[doc_id] = filename
                doc_keywords[doc_id] = meta.keywords
            except Exception as e:
                raise StageExecutionError(DocumentStageNames.ANALYSIS, f"Metadata extraction failed: {str(e)}")

            # Chunking Ingestion stage
            try:
                chunks = self.chunk_manager.chunk_document(
                    content=content,
                    file_format=meta.format,
                    chunk_size=opts.get("chunk_size", 800),
                    chunk_overlap=opts.get("chunk_overlap", 150)
                )
                
                # Associate chunks with this document
                for c in chunks:
                    c.chunk_id = f"{doc_id}-{c.chunk_id}"
                
                doc_chunks_map[doc_id] = chunks
                all_chunks.extend(chunks)
            except Exception as e:
                raise StageExecutionError(DocumentStageNames.CHUNKING, f"Text chunking failed: {str(e)}")

        # Stage 3: Summarization
        try:
            summary = self.summary_engine.summarize(all_chunks, custom_prompt)
        except Exception as e:
            raise StageExecutionError(DocumentStageNames.SUMMARIZATION, f"Summarization failed: {str(e)}")

        # Stage 4: Topics & Entities Extraction
        try:
            topics = self._extract_topics(all_chunks, metadata_map)
            entities = self._extract_entities(all_chunks)
        except Exception as e:
            raise StageExecutionError(DocumentStageNames.ANALYSIS, f"Topics/Entities extraction failed: {str(e)}")

        # Stage 5: Similarity mapping
        try:
            similar_documents = self._compute_similarity(doc_keywords, doc_names_map)
        except Exception as e:
            raise StageExecutionError(DocumentStageNames.SIMILARITY, f"Similarity computation failed: {str(e)}")

        # Stage 6: Knowledge extraction
        try:
            extracted_knowledge = self._extract_knowledge(all_chunks, list(documents.keys()))
        except Exception as e:
            raise StageExecutionError(DocumentStageNames.KNOWLEDGE_PROFILE, f"Knowledge extraction failed: {str(e)}")

        # Stage 7: Assemble report
        try:
            report = self.report_builder.build_report(
                workspace_id=workspace_id,
                document_ids=list(documents.keys()),
                metadata=metadata_map,
                summary=summary,
                topics=topics,
                entities=entities,
                citations=[],  # Empty for standard reports, generated during querying
                similar_documents=similar_documents,
                extracted_knowledge=extracted_knowledge
            )
        except Exception as e:
            raise StageExecutionError(DocumentStageNames.REPORT, f"Report assembly failed: {str(e)}")

        # Publish timeline event
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="DocumentAgent",
            payload={
                "event": "document.timeline.updated",
                "workspace_id": workspace_id,
                "report_id": report.report_id,
                "document_count": len(documents)
            }
        )
        self.event_bus.publish(event)

        return report

    def query_documents(
        self,
        query: str,
        document_chunks: Dict[str, List[TextChunk]],
        document_names: Dict[str, str],
        limit: int = 3
    ) -> Tuple[str, List[Citation]]:
        """Handles citation-aware querying of text chunks."""
        return self.citation_engine.search_and_cite(query, document_chunks, document_names, limit)

    def _extract_topics(self, chunks: List[TextChunk], meta_map: Dict[str, DocumentMetadata]) -> List[Topic]:
        """Extracts prominent topics based on keywords and chunk headings."""
        topic_counts = {}
        for meta in meta_map.values():
            for kw in meta.keywords:
                topic_counts[kw] = topic_counts.get(kw, 0) + 2  # Boost keyword weights
        
        for c in chunks:
            if c.section and c.section != "General":
                sect_name = c.section.lower()
                topic_counts[sect_name] = topic_counts.get(sect_name, 0) + 1

        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        topics = []
        max_score = sorted_topics[0][1] if sorted_topics else 1.0
        
        for name, score in sorted_topics[:5]:
            weight = min(1.0, score / max_score)
            topics.append(Topic(
                name=name.title(),
                weight=round(weight, 2),
                description=f"Theme surrounding '{name}' extracted from file headings and keywords."
            ))
            
        if not topics:
            topics.append(Topic(name="General", weight=0.5, description="General repository document content."))
            
        return topics

    def _extract_entities(self, chunks: List[TextChunk]) -> List[Entity]:
        """Scans chunks for named entities like Persons, Orgs, Locations, and Techs."""
        entities = []
        found = set()
        
        org_keywords = {"Google", "DeepMind", "Microsoft", "Nexus AI", "Amazon", "OpenAI", "Meta"}
        tech_keywords = {"Python", "FastAPI", "React", "Node.js", "SQLite", "Docker", "Pydantic", "Git", "Go", "Java"}
        loc_keywords = {"London", "New York", "San Francisco", "California", "Seattle"}
        
        # Merge text
        full_text = " ".join(c.text for c in chunks)
        
        # Simple lookup matcher
        for word in re.findall(r'\b[a-zA-Z\.\#\-\d]+\b', full_text):
            if word in org_keywords and ("ORG", word) not in found:
                entities.append(Entity(name=word, label="Organization", confidence=0.9))
                found.add(("ORG", word))
            elif word in tech_keywords and ("TECH", word) not in found:
                entities.append(Entity(name=word, label="Technology", confidence=0.95))
                found.add(("TECH", word))
            elif word in loc_keywords and ("LOC", word) not in found:
                entities.append(Entity(name=word, label="Location", confidence=0.855))
                found.add(("LOC", word))

        # Capture years as dates
        for year in re.findall(r'\b(19\d{2}|20\d{2})\b', full_text):
            if ("DATE", year) not in found:
                entities.append(Entity(name=year, label="Date", confidence=0.9))
                found.add(("DATE", year))

        return entities

    def _compute_similarity(self, doc_kws: Dict[str, List[str]], doc_names: Dict[str, str]) -> List[SimilarityMapping]:
        """Calculates pairwise document similarity scores using Jaccard overlap on keywords."""
        mappings = []
        doc_ids = list(doc_kws.keys())
        
        for id1 in doc_ids:
            for id2 in doc_ids:
                if id1 == id2:
                    continue
                kws1 = set(doc_kws[id1])
                kws2 = set(doc_kws[id2])
                union = kws1.union(kws2)
                intersection = kws1.intersection(kws2)
                score = len(intersection) / len(union) if union else 0.0
                
                mappings.append(SimilarityMapping(
                    target_document_id=id2,
                    target_document_name=doc_names.get(id2, "Unknown"),
                    similarity_score=round(score, 2),
                    common_topics=list(intersection)
                ))
        return mappings

    def _extract_knowledge(self, chunks: List[TextChunk], doc_ids: List[str]) -> List[ExtractedKnowledgeItem]:
        """Extracts facts, skills, projects, and experiences to feed the Professional Profile."""
        items = []
        full_text = " ".join(c.text for c in chunks)
        
        # Extract skills (using tech keywords found in text)
        tech_keywords = {"Python", "FastAPI", "React", "Node.js", "SQLite", "Docker", "Pydantic", "Go", "Java"}
        extracted_skills = []
        for word in re.findall(r'\b[a-zA-Z\.\#\-\d]+\b', full_text):
            if word in tech_keywords and word not in extracted_skills:
                extracted_skills.append(word)
                items.append(ExtractedKnowledgeItem(
                    key=f"skill.{word.lower()}",
                    value={"name": word, "category": "Technologies"},
                    category="Skill",
                    sources=doc_ids
                ))

        # Look for project descriptions (e.g. lines containing "built" or "developed")
        proj_idx = 1
        for line in full_text.splitlines():
            line = line.strip()
            if any(verb in line.lower() for verb in ["built a ", "developed a ", "designed a "]) and len(line) > 30:
                items.append(ExtractedKnowledgeItem(
                    key=f"project.doc_{proj_idx}",
                    value={"name": f"Project {proj_idx}", "description": line},
                    category="Project",
                    sources=doc_ids
                ))
                proj_idx += 1
                if proj_idx > 3:
                    break

        return items


from backend.intelligence.core.base_intelligence import BaseIntelligenceModule
from backend.intelligence.core.context import IntelligenceContext
from backend.intelligence.core.report import IntelligenceExecutionReport
from typing import Set

class DocumentModule(BaseIntelligenceModule):
    """Document Intelligence adapter subclassing BaseIntelligenceModule for global orchestration."""

    @property
    def name(self) -> str:
        return "DocumentIntelligence"

    @property
    def capabilities(self) -> Set[str]:
        return {"DOCUMENT_INTELLIGENCE", "DOCUMENT_SUMMARY", "DOCUMENT_QUERY"}

    def execute_workflow(self, context: IntelligenceContext) -> IntelligenceExecutionReport:
        """Executes the Document Intelligence workflow on the context.

        Args:
            context: Context containing input workspaces and document links.

        Returns:
            IntelligenceExecutionReport: Telemetry execution report wrapper.
        """
        import time
        from backend.intelligence.document.document_service import DocumentProductService
        
        start_time = time.perf_counter()
        product_service = DocumentProductService()
        
        workspace_id = context.workspace_id
        doc_ids = context.document_ids or []
        user_id = context.user_id or "admin"
        options = context.metadata or {}
        
        try:
            report = product_service.analyze_sync(
                workspace_id=workspace_id,
                document_ids=doc_ids,
                user_id=user_id,
                options=options
            )
            
            duration = time.perf_counter() - start_time
            timeline = {
                "total_duration": duration,
                "ingestion": duration * 0.3,
                "chunking": duration * 0.3,
                "analysis": duration * 0.4
            }
            
            return IntelligenceExecutionReport(
                execution_id=report.report_id,
                module_name=self.name,
                status="completed",
                execution_timeline=timeline,
                stage_results={"report": report.model_dump()},
                errors={},
                warnings={},
                metrics={
                    "document_count": len(doc_ids),
                    "word_count": sum(m.word_count for m in report.metadata.values())
                },
                output_summary={
                    "report_id": report.report_id,
                    "document_count": len(doc_ids),
                    "summary": report.summary.executive
                }
            )
        except Exception as e:
            duration = time.perf_counter() - start_time
            return IntelligenceExecutionReport(
                execution_id="exec-doc-failed",
                module_name=self.name,
                status="failed",
                execution_timeline={"total_duration": duration},
                stage_results={},
                errors={"workflow": str(e)},
                warnings={},
                metrics={},
                output_summary={}
            )

