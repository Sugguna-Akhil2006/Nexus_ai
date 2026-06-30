"""Custom exceptions for the Resume Parser Engine."""

from backend.runtime.exceptions import NexusException


class ResumeIntelligenceError(NexusException):
    """Base exception for all Resume Intelligence related errors."""
    pass


class ResumeParsingError(ResumeIntelligenceError):
    """Base exception for all Resume Parser related errors."""
    pass


class ATSAnalysisError(ResumeIntelligenceError):
    """Raised when ATS scoring fails."""
    pass


class SkillExtractionError(ResumeIntelligenceError):
    """Raised when skill classification or inference fails."""
    pass


class JDMatchingError(ResumeIntelligenceError):
    """Raised when JD matching fails."""
    pass


class ReportGenerationError(ResumeIntelligenceError):
    """Raised when consolidating report fails."""
    pass


class UnsupportedFormatError(ResumeParsingError):
    """Raised when the uploaded resume file format is not supported."""
    pass


class EmptyResumeError(ResumeParsingError):
    """Raised when the resume document contains no readable text."""
    pass


class CorruptedDocumentError(ResumeParsingError):
    """Raised when the document is malformed or corrupted and cannot be read."""
    pass


class ParsingFailureError(ResumeParsingError):
    """Raised when structured LLM parsing or schema mapping fails."""
    pass


class ResumeValidationError(ResumeIntelligenceError):
    """Raised when canonical Resume validation constraints fail."""
    pass


class ResumeNormalizationError(ResumeIntelligenceError):
    """Raised when technology or text normalization attributes fail."""
    pass


class JDParserError(ResumeIntelligenceError):
    """Raised when parsing or extracting job description properties fails."""
    pass
