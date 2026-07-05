"""Builds directed relationship edges between identified entity nodes."""

import re
from typing import List, Dict, Tuple, Any
from backend.intelligence.document.models import EntityNode, RelationshipEdge


class RelationshipExtractor:
    """Extracts directed semantic linkages between entity pairs occurring in document sentences."""

    def extract_relationships(self, text: str, entities: List[EntityNode]) -> List[RelationshipEdge]:
        """Scans sentences to discover entity co-occurrences and assign relationship edges.

        Args:
            text: Raw input string.
            entities: Pre-extracted EntityNodes.

        Returns:
            List[RelationshipEdge]: Discovered relationship linkages.
        """
        relationships = []
        if len(entities) < 2:
            return relationships

        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        found_pairs = set()

        # Build category map for quick lookup
        cat_map = {e.name.lower(): e.category for e in entities}
        name_map = {e.name.lower(): e.name for e in entities}

        for sent in sentences:
            sent_lower = sent.lower()
            # Find entities present in this sentence
            present = [e_name for e_name in cat_map if e_name in sent_lower]
            if len(present) < 2:
                continue

            # Check pairs
            for i, name1_lbl in enumerate(present):
                for name2_lbl in present[i+1:]:
                    cat1 = cat_map[name1_lbl]
                    cat2 = cat_map[name2_lbl]
                    
                    # Prevent duplicates in both directions
                    pair_key = tuple(sorted([name1_lbl, name2_lbl]))
                    if pair_key in found_pairs:
                        continue

                    source = name_map[name1_lbl]
                    target = name_map[name2_lbl]
                    rel_type = "associated_with"
                    confidence = 0.7

                    # Apply semantic matching rules based on category combinations
                    # Rule 1: Framework -> Language (e.g. FastAPI -> Python)
                    if cat1 == "Frameworks" and cat2 == "Programming Languages":
                        source = name_map[name1_lbl]
                        target = name_map[name2_lbl]
                        rel_type = "written_in"
                        confidence = 0.95
                    elif cat2 == "Frameworks" and cat1 == "Programming Languages":
                        source = name_map[name2_lbl]
                        target = name_map[name1_lbl]
                        rel_type = "written_in"
                        confidence = 0.95
                    
                    # Rule 2: Technology -> Technology (e.g. Docker -> Kubernetes)
                    elif cat1 == "Technologies" and cat2 == "Technologies":
                        if "deploy" in sent_lower or "run" in sent_lower or "cluster" in sent_lower:
                            source = name_map[name1_lbl] if "docker" in name1_lbl else name_map[name2_lbl]
                            target = name_map[name2_lbl] if "kubernetes" in name2_lbl else name_map[name1_lbl]
                            rel_type = "deploys_to"
                            confidence = 0.9
                    
                    # Rule 3: People -> Project / Org (e.g. Bob -> Project Alpha)
                    elif cat1 == "People" and cat2 in ("Projects", "Organizations"):
                        source = name_map[name1_lbl]
                        target = name_map[name2_lbl]
                        rel_type = "member_of" if cat2 == "Organizations" else "works_on"
                        confidence = 0.85
                    elif cat2 == "People" and cat1 in ("Projects", "Organizations"):
                        source = name_map[name2_lbl]
                        target = name_map[name1_lbl]
                        rel_type = "member_of" if cat1 == "Organizations" else "works_on"
                        confidence = 0.85

                    # Rule 4: Organization -> Product
                    elif cat1 == "Organizations" and cat2 == "Products":
                        source = name_map[name1_lbl]
                        target = name_map[name2_lbl]
                        rel_type = "develops"
                        confidence = 0.9
                    elif cat2 == "Organizations" and cat1 == "Products":
                        source = name_map[name2_lbl]
                        target = name_map[name1_lbl]
                        rel_type = "develops"
                        confidence = 0.9

                    # Rule 5: Framework/Language -> Standards (e.g. Python -> REST API)
                    elif cat1 in ("Frameworks", "Programming Languages") and cat2 == "Standards":
                        source = name_map[name1_lbl]
                        target = name_map[name2_lbl]
                        rel_type = "implements"
                        confidence = 0.8
                    elif cat2 in ("Frameworks", "Programming Languages") and cat1 == "Standards":
                        source = name_map[name2_lbl]
                        target = name_map[name1_lbl]
                        rel_type = "implements"
                        confidence = 0.8

                    relationships.append(RelationshipEdge(
                        source=source,
                        target=target,
                        relationship_type=rel_type,
                        confidence=confidence
                    ))
                    found_pairs.add(pair_key)

        return relationships
