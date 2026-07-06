"""
report_generator.py
---------------------
Builds a downloadable PDF report summarizing the dataset overview,
key statistics, AI-generated insights, and recommendations.
"""

from fpdf import FPDF
from datetime import datetime
import re
import unicodedata


# fpdf2's built-in core fonts (Helvetica, etc.) only support Latin-1.
# AI-generated text (and even our own status messages) often contains
# "smart" unicode punctuation or emoji that would otherwise raise
# FPDFUnicodeEncodingException. We normalize common punctuation to
# plain ASCII first, then drop anything else that still can't be
# encoded (e.g. emoji) instead of crashing.
_UNICODE_REPLACEMENTS = {
    "\u2018": "'", "\u2019": "'",   # curly single quotes
    "\u201c": '"', "\u201d": '"',   # curly double quotes
    "\u2013": "-", "\u2014": "--",  # en dash, em dash
    "\u2026": "...",                # ellipsis
    "\u2022": "-", "\u25cf": "-", "\u25e6": "-", "\u2023": "-",  # bullets
    "\u00a0": " ",                  # non-breaking space
    "\u2192": "->", "\u2190": "<-",  # arrows
}


def _sanitize_text(text) -> str:
    """Make any string safe to render with fpdf2's core Latin-1 fonts."""
    if text is None:
        return ""
    text = str(text)
    for bad, good in _UNICODE_REPLACEMENTS.items():
        text = text.replace(bad, good)
    # Normalize remaining accented characters where possible (e.g. é -> e is NOT
    # done here since Latin-1 supports accented Latin letters directly).
    # Drop anything that still can't be encoded in Latin-1 (emoji, CJK, etc.)
    text = text.encode("latin-1", errors="ignore").decode("latin-1")
    return text


def _strip_markdown(text: str) -> str:
    """Remove common markdown symbols so text renders cleanly in the PDF."""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    return text


class ReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(30, 60, 114)
        self.cell(0, 10, "AI Data Analyst Agent - Report", ln=True, align="C")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 6, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(30, 60, 114)
        self.ln(4)
        self.cell(0, 8, _sanitize_text(title), ln=True)
        self.set_draw_color(30, 60, 114)
        self.line(self.get_x(), self.get_y(), self.get_x() + 190, self.get_y())
        self.ln(3)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        clean = _sanitize_text(_strip_markdown(_sanitize_text(text)))
        self.multi_cell(0, 6, clean)
        self.ln(2)


def generate_pdf_report(
    output_path: str,
    dataset_name: str,
    shape: tuple,
    cleaning_report: list,
    executive_summary: str,
    insights_text: str,
    chart_image_paths: list = None,
):
    """
    Build the full PDF report and save it to output_path.

    chart_image_paths: list of PNG file paths (e.g., exported via Plotly's
    fig.write_image) to embed in the report.
    """
    pdf = ReportPDF()
    pdf.add_page()

    pdf.section_title("Dataset Overview")
    pdf.body_text(
        f"File analyzed: {_sanitize_text(dataset_name)}\n"
        f"Rows: {shape[0]:,}   Columns: {shape[1]}"
    )

    if cleaning_report:
        pdf.section_title("Data Cleaning Summary")
        pdf.body_text("\n".join(f"- {line}" for line in cleaning_report))

    if executive_summary:
        pdf.section_title("Executive Summary")
        pdf.body_text(executive_summary)

    if insights_text:
        pdf.section_title("AI-Generated Insights & Recommendations")
        pdf.body_text(insights_text)

    if chart_image_paths:
        pdf.section_title("Visualizations")
        for path in chart_image_paths:
            try:
                pdf.image(path, w=180)
                pdf.ln(4)
            except Exception:
                continue

    pdf.output(output_path)
    return output_path
