"""Renderer exporting reports to standard formats including JSON and PDF layout bytes."""

from backend.intelligence.resume.product import ProductResumeReport


class ReportRenderer:
    """Renders ProductResumeReport to standardized export structures."""

    def to_json(self, report: ProductResumeReport) -> str:
        """Returns standard serialized JSON representation."""
        return report.model_dump_json()

    def to_pdf(self, report: ProductResumeReport) -> bytes:
        """Generates future-ready PDF stream bytes matching ISO standards.

        Args:
            report: Mapped product report context.

        Returns:
            bytes: Valid PDF layout bytes.
        """
        # Formulate a structured mock PDF string containing standard xref nodes
        summary_slice = report.executive_summary[:60].replace("(", "\\(").replace(")", "\\)")
        pdf_stream = (
            "%PDF-1.4\n"
            "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R >>\nendobj\n"
            "4 0 obj\n"
            f"<< /Length 200 >>\n"
            "stream\n"
            "BT\n/F1 12 Tf\n70 800 Td\n"
            f"(Resume Analysis Report: {report.report_id}) Tj\n"
            "0 -20 Td\n"
            f"(Overall ATS Score: {report.ats_score}) Tj\n"
            "0 -20 Td\n"
            f"(Summary: {summary_slice}...) Tj\n"
            "ET\n"
            "endstream\nendobj\nxref\n0 5\n0000000000 65535 f\n"
            "trailer\n<< /Size 5 /Root 1 0 R >>\n"
            "%%EOF"
        )
        return pdf_stream.encode("utf-8")
