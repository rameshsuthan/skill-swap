"""Build the editable submission report from its Markdown source.

Run with the Codex document runtime Python (python-docx dependency).
Render and visually inspect the result with the document skill before delivery.
"""

import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/submission/SkillSwap-project-documentation.md"
TARGET = SOURCE.with_suffix(".docx")


def inline(paragraph, text):
    for part in re.split(r"(\*\*.*?\*\*|`[^`]+`)", text):
        run = paragraph.add_run(part[2:-2] if part.startswith("**") else part.strip("`"))
        if part.startswith("**"):
            run.bold = True
        if part.startswith("`"):
            run.font.name = "Consolas"
            run.font.size = Pt(9)


def build():
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = Inches(0.7)
    section.left_margin = section.right_margin = Inches(0.75)
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    normal.paragraph_format.space_after = Pt(7)
    normal.paragraph_format.line_spacing = 1.08
    normal.paragraph_format.keep_together = True
    for name, size in [("Title", 25), ("Heading 1", 15), ("Heading 2", 12)]:
        style = doc.styles[name]
        style.font.name = "Calibri"
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.space_before = Pt(12 if name != "Title" else 0)
        style.paragraph_format.space_after = Pt(8)
    footer = section.footer.paragraphs[0]
    footer.add_run("SkillSwap project submission  •  November 2, 2026")
    footer.runs[0].font.size = Pt(8)
    footer.add_run(" " * 8 + "Page ")
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)
    doc.core_properties.author = "Ramesh"
    doc.core_properties.title = "SkillSwap project documentation"
    doc.core_properties.subject = "The Gen Academy Week 3 submission"
    lines = SOURCE.read_text().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line == "<!-- pagebreak -->":
            doc.add_page_break()
            i += 1
            continue
        picture = re.fullmatch(r"!\[(.*?)\]\((.*?)\)", line)
        if picture:
            doc.add_picture(str(SOURCE.parent / picture.group(2)), width=Inches(7))
            p = doc.add_paragraph(picture.group(1))
            p.paragraph_format.space_after = Pt(8)
            for run in p.runs:
                run.italic = True
                run.font.size = Pt(9)
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [v.strip() for v in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[:\- ]+", c) for c in cells):
                    rows.append(cells)
                i += 1
            table = doc.add_table(rows=0, cols=len(rows[0]))
            table.autofit = False
            widths = [1.45, 2.0, 3.55] if len(rows[0]) == 3 else [7 / len(rows[0])] * len(rows[0])
            if rows[0][0] == "Teaching session":
                widths = [1.7, 2.65, 2.65]
            for col, width in zip(table.columns, widths):
                col.width = Inches(width)
            for j, row in enumerate(rows):
                cells = table.add_row().cells
                trpr = cells[0]._tc.getparent().get_or_add_trPr()
                trpr.append(OxmlElement("w:cantSplit"))
                if j == 0:
                    trpr.append(OxmlElement("w:tblHeader"))
                for k, value in enumerate(row):
                    cell = cells[k]
                    cell.width = Inches(widths[k])
                    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    pr = cell._tc.get_or_add_tcPr()
                    shade = OxmlElement("w:shd")
                    shade.set(qn("w:fill"), "E8EDF2" if j == 0 else "FFFFFF")
                    pr.append(shade)
                    borders = OxmlElement("w:tcBorders")
                    for edge in ["top", "left", "bottom", "right"]:
                        border = OxmlElement("w:" + edge)
                        for key, val in [("val", "single"), ("sz", "4"), ("color", "D9D9D9")]:
                            border.set(qn("w:" + key), val)
                        borders.append(border)
                    pr.append(borders)
                    margins = OxmlElement("w:tcMar")
                    for edge in ["top", "left", "bottom", "right"]:
                        margin = OxmlElement("w:" + edge)
                        margin.set(qn("w:w"), "100")
                        margin.set(qn("w:type"), "dxa")
                        margins.append(margin)
                    pr.append(margins)
                    p = cell.paragraphs[0]
                    if len(rows) <= 5 and j < len(rows) - 1:
                        p.paragraph_format.keep_with_next = True
                    p.paragraph_format.space_after = Pt(2)
                    p.paragraph_format.space_before = Pt(2)
                    inline(p, value)
                    for run in p.runs:
                        run.font.size = Pt(9)
                        run.bold = j == 0
            doc.add_paragraph().paragraph_format.space_after = Pt(0)
            continue
        if line.startswith("# "):
            inline(doc.add_paragraph(style="Title"), line[2:])
        elif line.startswith("## "):
            inline(doc.add_paragraph(style="Heading 1"), line[3:])
        elif line.startswith("> "):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.2)
            inline(p, line[2:])
            for run in p.runs:
                run.italic = True
        elif re.match(r"^\d+\. ", line):
            inline(doc.add_paragraph(style="List Number"), re.sub(r"^\d+\. ", "", line))
        else:
            inline(doc.add_paragraph(), line)
        i += 1
    doc.save(TARGET)
    print(TARGET)


if __name__ == "__main__":
    build()
