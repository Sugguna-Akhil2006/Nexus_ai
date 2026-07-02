"""Resume Intelligence Package.

Exposes the core agent, exception models, and structured schemas.
"""

from backend.intelligence.resume.agent import ResumeAgent
from backend.intelligence.resume.services import ResumeService
from backend.intelligence.resume.exceptions import (
    ResumeIntelligenceError,
    ResumeParsingError,
    ATSAnalysisError,
    SkillExtractionError,
    JDMatchingError,
    ReportGenerationError
)
from backend.intelligence.resume.models import (
    ContactInfo,
    EducationInfo,
    WorkExperience,
    ProjectInfo,
    CertificationInfo,
    ResumeData,
    CategorizedSkills,
    ATSResult,
    JDMatchResult,
    ResumeAnalysis,
    ResumeReport
)

# Register with global framework registry
from backend.intelligence.core.registry import IntelligenceRegistry
from backend.intelligence.resume.module import ResumeModule
IntelligenceRegistry().register(ResumeModule())
