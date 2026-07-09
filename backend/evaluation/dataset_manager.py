"""Dataset manager providing pre-configured test scenarios and synthetic evaluation cases."""

from __future__ import annotations

from typing import List, Optional

from backend.evaluation.models import Dataset, TestCase


class DatasetManager:
    """Manages pre-seeded and dynamically generated benchmark datasets."""

    def __init__(self) -> None:
        self._datasets: List[Dataset] = []
        self._initialize_default_datasets()

    def _initialize_default_datasets(self) -> None:
        # 1. Resume Analysis Dataset
        resume_cases = [
            TestCase(
                case_id="tc-res-01",
                category="resume",
                input_query="Parse skills and history from resume",
                reference_output="Expected core profile containing Python and Web development experience.",
            )
        ]
        self._datasets.append(Dataset(dataset_id="ds-resume", name="Resume Analysis", cases=resume_cases))

        # 2. GitHub Repositories Dataset
        github_cases = [
            TestCase(
                case_id="tc-git-01",
                category="github",
                input_query="Analyze repository quality and language metrics",
                reference_output="Expected repository metrics detailing language splits and code health.",
            )
        ]
        self._datasets.append(Dataset(dataset_id="ds-github", name="GitHub Repositories", cases=github_cases))

        # 3. Technical Documents Dataset
        doc_cases = [
            TestCase(
                case_id="tc-doc-01",
                category="document",
                input_query="Extract configurations and reference citations",
                reference_output="Expected structured document summary with citations.",
            )
        ]
        self._datasets.append(Dataset(dataset_id="ds-documents", name="Technical Documents", cases=doc_cases))

        # 4. Mixed Professional Profiles Dataset
        mixed_cases = [
            TestCase(
                case_id="tc-mix-01",
                category="mixed",
                input_query="Synthesize complete workspace profile for user",
                reference_output="Expected unified professional overview with aggregated metrics.",
            )
        ]
        self._datasets.append(Dataset(dataset_id="ds-mixed", name="Mixed Professional Profiles", cases=mixed_cases))

    def get_dataset(self, dataset_name: str) -> Optional[Dataset]:
        """Retrieves a dataset by name."""
        for ds in self._datasets:
            if ds.name.lower() == dataset_name.lower() or ds.dataset_id.lower() == dataset_name.lower():
                return ds
        return None

    def list_datasets(self) -> List[Dataset]:
        """Lists all registered datasets."""
        return list(self._datasets)

    def generate_synthetic_dataset(self, size: int = 5) -> Dataset:
        """Generates synthetic test cases for general testing."""
        cases = []
        for i in range(1, size + 1):
            cases.append(
                TestCase(
                    case_id=f"tc-syn-{i:02d}",
                    category="synthetic",
                    input_query=f"Synthetic general test query {i}",
                    reference_output=f"Expected synthetic reference output answer {i}",
                )
            )
        return Dataset(
            dataset_id="ds-synthetic",
            name="Synthetic Test Cases",
            cases=cases,
        )
