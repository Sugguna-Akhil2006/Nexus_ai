"""Knowledge graph building relationships between skills, technologies, and projects."""

from typing import Dict, List

from backend.intelligence.profile.models import KnowledgeProfile


class SkillGraphBuilder:
    """Builds relational node connections (skills to categories, projects to tech stack)."""

    def build_graph(self, profile: KnowledgeProfile) -> Dict[str, List[str]]:
        """Maps relationships based on projects and categories.

        Args:
            profile: The KnowledgeProfile.

        Returns:
            Dict[str, List[str]]: Relational graph dictionary.
        """
        graph: Dict[str, List[str]] = {}

        # 1. Connect project nodes to technology nodes
        for proj in profile.projects:
            proj_key = f"project:{proj.name}"
            graph[proj_key] = [f"skill:{t}" for t in proj.technologies]

        # 2. Connect individual skills to their category folders
        for name, skill in profile.skills.items():
            skill_key = f"skill:{name}"
            if skill.category:
                cat_key = f"category:{skill.category}"
                if skill_key not in graph:
                    graph[skill_key] = []
                graph[skill_key].append(cat_key)

        # 3. Inject standard framework dependency taxonomies
        hierarchies = {
            "FastAPI": ["Python", "REST APIs", "Backend"],
            "Django": ["Python", "Backend"],
            "React": ["JavaScript", "TypeScript", "Frontend"],
            "Vue.js": ["JavaScript", "Frontend"],
            "TypeScript": ["JavaScript"],
            "Kubernetes": ["Docker", "DevOps"],
            "PyTorch": ["Python", "AI", "Machine Learning"],
            "TensorFlow": ["Python", "AI", "Machine Learning"]
        }
        for skill_name, parents in hierarchies.items():
            match = next((s for s in profile.skills if s.lower() == skill_name.lower()), None)
            if match:
                actual_key = f"skill:{match}"
                if actual_key not in graph:
                    graph[actual_key] = []
                for p in parents:
                    graph[actual_key].append(f"skill:{p}")

        return graph
