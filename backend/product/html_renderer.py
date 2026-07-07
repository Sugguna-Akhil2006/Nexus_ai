"""Premium dark-mode HTML exporter for the Product Experience Layer.

Provides HTMLRenderer which wraps the domain-specific HTML renderers under a
configurable design system. Supports pluggable CSS theme tokens and injects a
shared design system header into any domain report HTML output.

Classes
-------
- ThemeConfig  : Color tokens, typography, and spacing configuration.
- HTMLRenderer : Dispatcher calling domain HTML methods with theme injection.

Example usage::

    renderer = HTMLRenderer()
    html = renderer.render(resume_report)
    html = renderer.render(github_report, theme=ThemeConfig(primary="#7c3aed"))
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from backend.intelligence.resume.report_renderer import ReportRenderer as ResumeRenderer
from backend.intelligence.github.report_renderer import GitHubReportRenderer
from backend.intelligence.document.report_renderer import DocumentReportRenderer


@dataclass
class ThemeConfig:
    """CSS design token configuration for HTML report output.

    Attributes:
        bg: Page background color.
        surface: Card/panel background color.
        border: Default border color.
        text: Primary text color.
        text_muted: Secondary/muted text color.
        primary: Primary accent color (gradients, highlights).
        secondary: Secondary accent color.
        success: Success/positive indicator color.
        danger: Error/danger indicator color.
        warning: Warning indicator color.
        font_family: CSS font-family stack.
        border_radius: Default border-radius for cards.
    """

    bg: str = "#090a0f"
    surface: str = "#12131a"
    border: str = "#1e2130"
    text: str = "#e2e8f0"
    text_muted: str = "#64748b"
    primary: str = "#00f0ff"
    secondary: str = "#a855f7"
    success: str = "#22c55e"
    danger: str = "#ef4444"
    warning: str = "#eab308"
    font_family: str = "'Inter', 'Segoe UI', Roboto, sans-serif"
    border_radius: str = "12px"

    def to_css_vars(self) -> str:
        """Generates a CSS :root block with these theme tokens.

        Returns:
            CSS string containing custom property declarations.
        """
        return f"""
:root {{
  --bg: {self.bg};
  --surface: {self.surface};
  --border: {self.border};
  --text: {self.text};
  --text-muted: {self.text_muted};
  --primary: {self.primary};
  --secondary: {self.secondary};
  --success: {self.success};
  --danger: {self.danger};
  --warning: {self.warning};
  --font: {self.font_family};
  --radius: {self.border_radius};
}}
""".strip()


_GOOGLE_FONTS_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">'
)

_BASE_STYLES = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  padding: 40px 20px;
  min-height: 100vh;
}
.nx-badge {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 11px; font-weight: 600; letter-spacing: 0.5px;
  text-transform: uppercase; padding: 3px 10px; border-radius: 20px;
}
.nx-badge-primary {
  background: rgba(0, 240, 255, 0.12);
  border: 1px solid rgba(0, 240, 255, 0.25);
  color: var(--primary);
}
.nx-badge-secondary {
  background: rgba(168, 85, 247, 0.12);
  border: 1px solid rgba(168, 85, 247, 0.25);
  color: var(--secondary);
}
.nx-badge-success {
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(34, 197, 94, 0.25);
  color: var(--success);
}
.nx-badge-danger {
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.25);
  color: var(--danger);
}
"""


def _inject_theme(html: str, theme: ThemeConfig) -> str:
    """Injects theme CSS variables and base styles into an HTML document.

    Locates the first <style> tag and prepends the theme :root block and
    shared base styles. If no <style> tag is found, inserts one into <head>.

    Args:
        html: Raw HTML string from a domain renderer.
        theme: ThemeConfig to apply.

    Returns:
        HTML with injected theme styles.
    """
    theme_block = f"<style>\n{theme.to_css_vars()}\n{_BASE_STYLES}\n</style>\n"
    if "<head>" in html:
        return html.replace("<head>", f"<head>\n{_GOOGLE_FONTS_LINK}\n{theme_block}", 1)
    # No head tag – prepend at top
    return theme_block + html


class HTMLRenderer:
    """Premium HTML exporter wrapping domain-specific renderers.

    Dispatches rendering to the correct intelligence-domain renderer and
    optionally injects a unified design system CSS into the output.

    Attributes:
        inject_theme: When True, injects shared CSS variables into output.
    """

    def __init__(self, inject_theme: bool = True) -> None:
        """Initialises the renderer.

        Args:
            inject_theme: Whether to inject shared design-system CSS.
        """
        self._resume_renderer = ResumeRenderer()
        self._github_renderer = GitHubReportRenderer()
        self._document_renderer = DocumentReportRenderer()
        self.inject_theme = inject_theme

    def render(
        self,
        report: Any,
        theme: Optional[ThemeConfig] = None,
    ) -> str:
        """Detects the report domain and renders the appropriate HTML.

        Args:
            report: Any supported intelligence report object.
            theme: Optional ThemeConfig override. Defaults to the dark theme.

        Returns:
            Complete styled HTML document string.
        """
        cls_name = type(report).__name__
        if cls_name == "ProductResumeReport":
            return self.render_resume(report, theme=theme)
        if cls_name == "GitHubIntelligenceReport":
            return self.render_github(report, theme=theme)
        return self.render_document(report, theme=theme)

    def render_resume(
        self,
        report: Any,
        theme: Optional[ThemeConfig] = None,
    ) -> str:
        """Renders a ProductResumeReport to styled HTML.

        Args:
            report: ProductResumeReport instance.
            theme: Optional ThemeConfig override.

        Returns:
            HTML document string.
        """
        html = self._resume_renderer.to_html(report)
        if self.inject_theme:
            html = _inject_theme(html, theme or ThemeConfig())
        return html

    def render_github(
        self,
        report: Any,
        theme: Optional[ThemeConfig] = None,
    ) -> str:
        """Renders a GitHubIntelligenceReport to styled HTML.

        Args:
            report: GitHubIntelligenceReport instance.
            theme: Optional ThemeConfig override.

        Returns:
            HTML document string.
        """
        html = self._github_renderer.to_html(report)
        if self.inject_theme:
            html = _inject_theme(html, theme or ThemeConfig())
        return html

    def render_document(
        self,
        report: Any,
        theme: Optional[ThemeConfig] = None,
    ) -> str:
        """Renders a DocumentKnowledgeReport to styled HTML.

        Args:
            report: DocumentKnowledgeReport instance.
            theme: Optional ThemeConfig override.

        Returns:
            HTML document string.
        """
        html = self._document_renderer.render_html(report)
        if self.inject_theme:
            html = _inject_theme(html, theme or ThemeConfig())
        return html
