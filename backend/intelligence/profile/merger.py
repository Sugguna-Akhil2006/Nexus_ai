"""Aggregator merging separate candidate profiles into a single canonical record."""

from datetime import datetime

from backend.intelligence.profile.models import KnowledgeProfile, ProfilePersonalInfo
from backend.intelligence.profile.resolver import ConflictResolver


class ProfileMerger:
    """Combines profile schemas, deduplicates timelines, and updates source metrics."""

    def __init__(self) -> None:
        self.resolver = ConflictResolver()

    def merge_profiles(self, base: KnowledgeProfile, incoming: KnowledgeProfile) -> KnowledgeProfile:
        """Merges incoming profile changes into a base canonical profile.

        Args:
            base: The current target profile.
            incoming: The incoming parsed profile metadata to merge.

        Returns:
            KnowledgeProfile: A unified KnowledgeProfile record.
        """
        # Merge personal contact details
        b_info = base.personal_info
        i_info = incoming.personal_info

        full_name = i_info.full_name or b_info.full_name
        email = i_info.email or b_info.email
        phone = i_info.phone or b_info.phone
        location = i_info.location or b_info.location
        github = i_info.github or b_info.github
        linkedin = i_info.linkedin or b_info.linkedin
        portfolio = i_info.portfolio or b_info.portfolio

        # Merge personal info source attribution
        sources = dict(b_info.source_attribution)
        for k, v in i_info.source_attribution.items():
            sources[k] = self.resolver.resolve_source(sources.get(k), v)

        # Merge skills mappings
        skills = dict(base.skills)
        for k, v in incoming.skills.items():
            skills[k] = self.resolver.resolve_skill(skills.get(k), v)

        # Merge experience lists (deduplicate matching company + role)
        exp_list = list(base.experience)
        for exp in incoming.experience:
            match = next((
                e for e in exp_list 
                if e.company.lower() == exp.company.lower() and e.role.lower() == exp.role.lower()
            ), None)
            if match:
                match.sources = list(set(match.sources + exp.sources))
                match.responsibilities = list(set(match.responsibilities + exp.responsibilities))
            else:
                exp_list.append(exp)

        # Merge education lists
        edu_list = list(base.education)
        for edu in incoming.education:
            match = next((
                e for e in edu_list 
                if e.institution.lower() == edu.institution.lower() 
                and (e.degree or "").lower() == (edu.degree or "").lower()
            ), None)
            if match:
                match.sources = list(set(match.sources + edu.sources))
            else:
                edu_list.append(edu)

        # Merge projects
        proj_list = list(base.projects)
        for proj in incoming.projects:
            match = next((p for p in proj_list if p.name.lower() == proj.name.lower()), None)
            if match:
                match.sources = list(set(match.sources + proj.sources))
                match.technologies = list(set(match.technologies + proj.technologies))
            else:
                proj_list.append(proj)

        # Append contributors list items
        repos = list(base.repositories) + [r for r in incoming.repositories if r not in base.repositories]
        pubs = list(base.publications) + [p for p in incoming.publications if p not in base.publications]
        interests = list(set(base.research_interests + incoming.research_interests))

        return KnowledgeProfile(
            workspace_id=base.workspace_id,
            user_id=base.user_id,
            personal_info=ProfilePersonalInfo(
                full_name=full_name,
                email=email,
                phone=phone,
                location=location,
                github=github,
                linkedin=linkedin,
                portfolio=portfolio,
                source_attribution=sources
            ),
            skills=skills,
            experience=exp_list,
            education=edu_list,
            projects=proj_list,
            repositories=repos,
            publications=pubs,
            research_interests=interests,
            knowledge_graph=base.knowledge_graph,
            last_updated=datetime.utcnow().isoformat()
        )
