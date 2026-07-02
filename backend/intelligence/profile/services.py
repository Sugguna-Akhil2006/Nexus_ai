"""Profile Service coordinating profile aggregation, timeline builds, and semantic queries."""

from typing import Any, Dict, List, Optional
from datetime import datetime

from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.profile.models import (
    KnowledgeProfile,
    ProfilePersonalInfo,
    ProfileSkill,
    ProfileProject,
    ProfileExperience,
    ProfileEducation,
    ProfileSource,
    TimelineEvent
)
from backend.intelligence.profile.merger import ProfileMerger
from backend.intelligence.profile.timeline import TimelineEngine
from backend.intelligence.profile.knowledge_graph import SkillGraphBuilder
from backend.intelligence.resume.models import Resume


class ProfileService:
    """Consolidates candidate models into the canonical profile database."""

    def __init__(self) -> None:
        self.merger = ProfileMerger()
        self.timeline_engine = TimelineEngine()
        self.graph_builder = SkillGraphBuilder()
        self.event_bus = EventBus()

    def aggregate_resume(self, profile: KnowledgeProfile, resume: Resume) -> KnowledgeProfile:
        """Aggregates parsed resume details into the target profile.

        Args:
            profile: The base user profile.
            resume: Canonical Resume model details.

        Returns:
            KnowledgeProfile: The updated KnowledgeProfile.
        """
        # Map personal info
        info = resume.personal_info
        personal = ProfilePersonalInfo(
            full_name=info.full_name,
            email=info.email,
            phone=info.phone,
            github=info.github,
            linkedin=info.linkedin,
            portfolio=info.portfolio or info.website
        )
        personal.source_attribution["Resume"] = ProfileSource(
            source_name="Resume",
            confidence_score=1.0,
            evidence="Personal details block extraction"
        )

        # Map skills
        skills = {}
        for s in resume.skills:
            if s.name:
                skills[s.name] = ProfileSkill(
                    name=s.name,
                    category=s.category,
                    confidence_score=1.0,
                    sources=["Resume"],
                    evidence=["Resume skills listing"]
                )

        # Map experience
        experience = []
        for exp in resume.experience:
            experience.append(ProfileExperience(
                company=exp.company or "Unknown",
                role=exp.role or "Software Engineer",
                start_date=exp.start_date,
                end_date=exp.end_date,
                responsibilities=exp.responsibilities,
                sources=["Resume"]
            ))

        # Map education
        education = []
        for edu in resume.education:
            education.append(ProfileEducation(
                institution=edu.institution or "University",
                degree=edu.degree,
                branch=edu.branch,
                graduation_year=edu.graduation_year,
                sources=["Resume"]
            ))

        # Map projects
        projects = []
        for proj in resume.projects:
            projects.append(ProfileProject(
                name=proj.project_name or proj.name or "Project",
                description=proj.description,
                technologies=proj.technologies,
                github_url=proj.github_url,
                live_url=proj.live_url,
                sources=["Resume"]
            ))

        incoming = KnowledgeProfile(
            workspace_id=profile.workspace_id,
            user_id=profile.user_id,
            personal_info=personal,
            skills=skills,
            experience=experience,
            education=education,
            projects=projects
        )

        # Run merge
        merged = self.merger.merge_profiles(profile, incoming)

        # Re-build timelines and graph
        merged.timeline = self.timeline_engine.build_timeline(merged)
        merged.knowledge_graph = self.graph_builder.build_graph(merged)
        merged.last_updated = datetime.utcnow().isoformat()

        # Publish profile events
        self._publish_event("profile.updated", merged)
        self._publish_event("profile.timeline.updated", merged)

        return merged

    def aggregate_github(
        self,
        profile: KnowledgeProfile,
        repositories: List[Dict[str, Any]],
        languages: List[str]
    ) -> KnowledgeProfile:
        """Merges GitHub data into the profile.

        Args:
            profile: The base user profile.
            repositories: List of repository detail mappings.
            languages: Top language strings used.

        Returns:
            KnowledgeProfile: The updated profile.
        """
        # Map GitHub repositories
        incoming_skills = {}
        for lang in languages:
            incoming_skills[lang] = ProfileSkill(
                name=lang,
                category="Programming Languages",
                confidence_score=1.0,
                sources=["GitHub"],
                evidence=["Top GitHub languages list"]
            )

        incoming = KnowledgeProfile(
            workspace_id=profile.workspace_id,
            user_id=profile.user_id,
            skills=incoming_skills,
            repositories=repositories
        )

        merged = self.merger.merge_profiles(profile, incoming)
        merged.knowledge_graph = self.graph_builder.build_graph(merged)
        merged.last_updated = datetime.utcnow().isoformat()

        self._publish_event("profile.updated", merged)
        self._publish_event("profile.identity.merged", merged)

        return merged

    def search_profile(self, profile: KnowledgeProfile, query: str) -> Dict[str, Any]:
        """Answers user natural language queries by filtering relevant nodes.

        Args:
            profile: User profile record.
            query: Question string (e.g. 'What backend projects has this user built?').

        Returns:
            Dict[str, Any]: Matching skills, projects, and experiences.
        """
        query_lower = query.lower()
        results = {
            "matched_skills": [],
            "matched_projects": [],
            "matched_experience": []
        }

        # 1. Search skills
        for s in profile.skills.values():
            if s.name.lower() in query_lower or (s.category and s.category.lower() in query_lower):
                results["matched_skills"].append(s.model_dump())

        # 2. Search projects
        # Backend/Frontend keyword detection
        is_backend_query = "backend" in query_lower or "cloud" in query_lower or "database" in query_lower
        is_frontend_query = "frontend" in query_lower or "ui" in query_lower or "react" in query_lower or "design" in query_lower
        is_ai_query = "ai" in query_lower or "machine learning" in query_lower or "pytorch" in query_lower

        for p in profile.projects:
            tech_match = any(t.lower() in query_lower for t in p.technologies)
            desc_match = p.description and any(w in p.description.lower() for w in query_lower.split())
            
            # Semantic class matches
            match_found = tech_match or desc_match or (p.name.lower() in query_lower)
            if not match_found:
                if is_backend_query:
                    match_found = any(t.lower() in ["python", "fastapi", "django", "postgresql", "docker", "kubernetes", "go"] for t in p.technologies)
                elif is_frontend_query:
                    match_found = any(t.lower() in ["react", "vue.js", "html", "css", "typescript", "javascript"] for t in p.technologies)
                elif is_ai_query:
                    match_found = any(t.lower() in ["pytorch", "tensorflow", "openai", "transformers"] for t in p.technologies)

            if match_found:
                results["matched_projects"].append(p.model_dump())

        # 3. Search experience
        for exp in profile.experience:
            role_match = exp.role.lower() in query_lower
            resp_match = any(any(w in resp.lower() for w in query_lower.split()) for resp in exp.responsibilities)
            if role_match or resp_match:
                results["matched_experience"].append(exp.model_dump())

        return results

    def _publish_event(self, event_name: str, profile: KnowledgeProfile) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ProfileService",
            payload={
                "event": event_name,
                "workspace_id": profile.workspace_id,
                "user_id": profile.user_id,
                "skills_count": len(profile.skills),
                "experience_count": len(profile.experience),
                "timeline_count": len(profile.timeline)
            }
        )
        self.event_bus.publish(event)
