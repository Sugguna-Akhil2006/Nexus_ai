"""Flagship Intelligent Document Ingestion and Graph Orchestrator."""

import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.document.models import (
    DocumentKnowledgeReport,
    DocumentGraph,
    SemanticIndex,
    ConfidenceScores,
    KnowledgeObject,
    EntityNode,
    RelationshipEdge
)
from backend.intelligence.document.document_model import (
    DocumentMetadata,
    SummaryDetail,
    Topic,
    Citation
)
from backend.intelligence.document.chunk_manager import ChunkManager, TextChunk
from backend.intelligence.document.summary_engine import SummaryEngine
from backend.intelligence.document.document_metadata import MetadataExtractor
from backend.intelligence.document.entity_extractor import EntityExtractor
from backend.intelligence.document.topic_classifier import TopicClassifier
from backend.intelligence.document.relationship_extractor import RelationshipExtractor
from backend.intelligence.document.knowledge_extractor import KnowledgeExtractor
from backend.intelligence.document.semantic_index import SemanticIndexBuilder
from backend.intelligence.document.similarity_engine import DocumentSimilarityEngine
from backend.intelligence.document.document_graph import DocumentGraphBuilder
from backend.intelligence.document.document_workflow import DocumentStageNames, StageExecutionError


class DocumentProcessor:
    """Coordinates the advanced Intelligent Document Processing (IDP) workflow pipelines."""

    def __init__(self) -> None:
        self.chunk_manager = ChunkManager()
        self.summary_engine = SummaryEngine()
        self.metadata_extractor = MetadataExtractor()
        self.entity_extractor = EntityExtractor()
        self.topic_classifier = TopicClassifier()
        self.relationship_extractor = RelationshipExtractor()
        self.knowledge_extractor = KnowledgeExtractor()
        self.semantic_index_builder = SemanticIndexBuilder()
        self.similarity_engine = DocumentSimilarityEngine()
        self.graph_builder = DocumentGraphBuilder()
        self.event_bus = EventBus()

    def process_documents(
        self,
        workspace_id: str,
        documents: Dict[str, Tuple[str, str]],  # key: document_id -> (filename, raw_content)
        options: Optional[Dict[str, Any]] = None
    ) -> DocumentKnowledgeReport:
        """Executes the complete reasoning pipeline, returning a compiled DocumentKnowledgeReport.

        Args:
            workspace_id: Tenant workspace context ID.
            documents: Ingested document inputs.
            options: Execution configurations.

        Returns:
            DocumentKnowledgeReport: Compiled reasoning metrics.
        """
        opts = options or {}
        custom_prompt = opts.get("custom_prompt")

        if not documents:
            raise StageExecutionError(DocumentStageNames.LOADER, "No documents provided for processing.")

        metadata_map: Dict[str, DocumentMetadata] = {}
        all_chunks: List[TextChunk] = []
        doc_chunks_map: Dict[str, List[TextChunk]] = {}
        doc_texts: Dict[str, str] = {}
        doc_names: Dict[str, str] = {}
        doc_keywords: Dict[str, List[str]] = {}

        # 1. Metadata & Chunking Stage
        for doc_id, (filename, content) in documents.items():
            if not content.strip():
                raise StageExecutionError(DocumentStageNames.LOADER, f"File content of '{filename}' is empty.")
            
            doc_texts[doc_id] = content
            doc_names[doc_id] = filename

            try:
                meta = self.metadata_extractor.extract_metadata(content, filename, opts.get("custom_meta"))
                metadata_map[doc_id] = meta
                doc_keywords[doc_id] = meta.keywords
            except Exception as e:
                raise StageExecutionError(DocumentStageNames.ANALYSIS, f"Metadata parse failed: {str(e)}")

            try:
                chunks = self.chunk_manager.chunk_document(
                    content=content,
                    file_format=meta.format,
                    chunk_size=opts.get("chunk_size", 800),
                    chunk_overlap=opts.get("chunk_overlap", 150)
                )
                for c in chunks:
                    c.chunk_id = f"{doc_id}-{c.chunk_id}"
                doc_chunks_map[doc_id] = chunks
                all_chunks.extend(chunks)
            except Exception as e:
                raise StageExecutionError(DocumentStageNames.CHUNKING, f"Chunking failed: {str(e)}")

        full_merged_text = "\n\n".join(doc_texts.values())

        # 2. Entity Extraction
        try:
            entities = self.entity_extractor.extract_entities(full_merged_text)
            self._publish_event("document.entities.extracted", workspace_id, {"count": len(entities)})
        except Exception as e:
            raise StageExecutionError(DocumentStageNames.ANALYSIS, f"Entity extraction failed: {str(e)}")

        # 3. Topic Classification
        try:
            topics = self.topic_classifier.classify_topics(full_merged_text, opts.get("custom_categories"))
            self._publish_event("document.topics.classified", workspace_id, {"topics": [t.name for t in topics]})
        except Exception as e:
            raise StageExecutionError(DocumentStageNames.ANALYSIS, f"Topic classification failed: {str(e)}")

        # 4. Relationship Extraction & Graph Building
        try:
            raw_relationships = self.relationship_extractor.extract_relationships(full_merged_text, entities)
            graph = self.graph_builder.build_graph(entities, raw_relationships)
            self._publish_event("document.relationships.created", workspace_id, {"edges_count": len(graph.edges)})
        except Exception as e:
            raise StageExecutionError(DocumentStageNames.ANALYSIS, f"Graph relationship extraction failed: {str(e)}")

        # 5. Knowledge Extraction
        try:
            knowledge_objects = self.knowledge_extractor.extract_knowledge_objects(all_chunks)
            self._publish_event("document.knowledge.generated", workspace_id, {"objects_count": len(knowledge_objects)})
        except Exception as e:
            raise StageExecutionError(DocumentStageNames.KNOWLEDGE_PROFILE, f"Knowledge objects generation failed: {str(e)}")

        # 6. Semantic Indexing
        try:
            semantic_index = self.semantic_index_builder.build_index(all_chunks, entities, topics)
        except Exception as e:
            raise StageExecutionError(DocumentStageNames.REPORT, f"Semantic index construction failed: {str(e)}")

        # 7. Document Summary
        try:
            summary = self.summary_engine.summarize(all_chunks, custom_prompt)
        except Exception as e:
            raise StageExecutionError(DocumentStageNames.SUMMARIZATION, f"Summarization failed: {str(e)}")

        # 8. Jaccard Similarity overlaps
        try:
            similar_documents = self.similarity_engine.compute_similarity_mappings(
                doc_texts, doc_names, doc_keywords
            )
        except Exception as e:
            raise StageExecutionError(DocumentStageNames.SIMILARITY, f"Similarity engine failed: {str(e)}")

        # 9. Confidence Scores computation
        scores = self._calculate_confidence(entities, topics, graph.edges)

        report_id = f"rep-idp-{str(uuid.uuid4())[:8]}"

        return DocumentKnowledgeReport(
            report_id=report_id,
            workspace_id=workspace_id,
            document_ids=list(documents.keys()),
            metadata=metadata_map,
            entities=entities,
            topics=topics,
            relationships=graph.edges,
            knowledge_graph=graph,
            semantic_index=semantic_index,
            summary=summary,
            citations=[],
            confidence_scores=scores,
            knowledge_objects=knowledge_objects,
            extracted_knowledge=knowledge_objects,
            similar_documents=similar_documents,
            analyzed_at=datetime.utcnow()
        )

    def _calculate_confidence(
        self,
        entities: List[EntityNode],
        topics: List[Topic],
        relationships: List[RelationshipEdge]
    ) -> ConfidenceScores:
        """Heuristically computes validation scores based on extractors confidence rates."""
        meta_conf = 1.0
        
        ent_conf = sum(e.confidence for e in entities) / len(entities) if entities else 0.85
        top_conf = sum(t.weight for t in topics) / len(topics) if topics else 0.8
        rel_conf = sum(r.confidence for r in relationships) / len(relationships) if relationships else 0.75
        
        # Round scores
        ent_conf = round(ent_conf, 2)
        top_conf = round(top_conf, 2)
        rel_conf = round(rel_conf, 2)
        
        overall = round((meta_conf + ent_conf + top_conf + rel_conf) / 4.0, 2)

        return ConfidenceScores(
            metadata_confidence=meta_conf,
            entity_confidence=ent_conf,
            topic_confidence=top_conf,
            relationship_confidence=rel_conf,
            overall_score=overall
        )

    def _publish_event(self, event_name: str, workspace_id: str, payload: Dict[str, Any]) -> None:
        """Publishes event notifications to runtime event bus."""
        event_payload = {
            "event": event_name,
            "workspace_id": workspace_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        event_payload.update(payload)
        
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="DocumentProcessor",
            payload=event_payload
        )
        self.event_bus.publish(event)
