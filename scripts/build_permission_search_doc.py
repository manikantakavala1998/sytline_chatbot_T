"""Build documentation/Permission_Aware_Knowledge_Search.docx — the design note on permission-aware
document search (one collection with permission labels vs one collection per module).

    python -m scripts.build_permission_search_doc

The measured numbers come from the development server on 2026-09-30 (877 vectors, one Milvus
collection; load tests with 6, 12 and 25 users asking at the same moment).
"""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

OUT = Path(__file__).resolve().parents[1] / "documentation" / "Permission_Aware_Knowledge_Search.docx"

INK = RGBColor(0x18, 0x20, 0x2E)
SOFT = RGBColor(0x4D, 0x58, 0x69)
FAINT = RGBColor(0x6F, 0x7A, 0x8B)
ACCENT = RGBColor(0x1F, 0x55, 0xA8)
ISSUE = RGBColor(0xA3, 0x43, 0x1A)
GOOD = RGBColor(0x1C, 0x74, 0x47)
FILL = {"head": "EEF2F7", "accent": "E6EEFA", "issue": "FBEEE7", "good": "E5F4EC", "box": "F5F7FA"}
FONT = "Calibri"
MONO = "Consolas"


# ── Low-level helpers ────────────────────────────────────────────────────

def shade(cell, fill: str) -> None:
    props = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    props.append(shd)


def borders(table, color: str = "DDE3EB", inside: bool = True) -> None:
    props = table._tbl.tblPr
    box = OxmlElement("w:tblBorders")
    edges = ["top", "left", "bottom", "right"] + (["insideH", "insideV"] if inside else [])
    for edge in edges:
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:color"), color)
        box.append(el)
    props.append(box)


def no_borders(table) -> None:
    props = table._tbl.tblPr
    box = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "nil")
        box.append(el)
    props.append(box)


def left_bar(cell, color: str) -> None:
    """A coloured bar on the left edge of a cell (used for issue and example boxes)."""
    props = cell._tc.get_or_add_tcPr()
    box = OxmlElement("w:tcBorders")
    for edge in ("top", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "nil")
        box.append(el)
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), "24")
    left.set(qn("w:color"), color)
    box.append(left)
    props.append(box)


def keep_row_together(table) -> None:
    """A box (one-row table) moves to the next page whole instead of splitting."""
    for row in table.rows:
        props = row._tr.get_or_add_trPr()
        el = OxmlElement("w:cantSplit")
        props.append(el)


def cell_margins(table, cm: float = 0.25) -> None:
    props = table._tbl.tblPr
    margins = OxmlElement("w:tblCellMar")
    for edge in ("top", "bottom", "left", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:w"), str(int(cm * 567)))
        el.set(qn("w:type"), "dxa")
        margins.append(el)
    props.append(margins)


def widths(table, cm_list: list[float]) -> None:
    table.autofit = False
    for row in table.rows:
        for cell, width in zip(row.cells, cm_list):
            cell.width = Cm(width)


def run(paragraph, text: str, *, bold=False, italic=False, color=None, size=None, mono=False):
    r = paragraph.add_run(text)
    r.bold, r.italic = bold, italic
    if color is not None:
        r.font.color.rgb = color
    if size:
        r.font.size = Pt(size)
    if mono:
        r.font.name = MONO
        r._element.rPr.rFonts.set(qn("w:eastAsia"), MONO)
    return r


def rich(paragraph, text: str, **kwargs) -> None:
    """Text with **bold** and `code` spans."""
    import re

    for part in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text):
        if not part:
            continue
        if part.startswith("**"):
            run(paragraph, part[2:-2], bold=True, **kwargs)
        elif part.startswith("`"):
            run(paragraph, part[1:-1], mono=True, size=9.5, **{k: v for k, v in kwargs.items() if k != "size"})
        else:
            run(paragraph, part, **kwargs)


def spacing(paragraph, before=0, after=6, line=1.15):
    fmt = paragraph.paragraph_format
    fmt.space_before, fmt.space_after, fmt.line_spacing = Pt(before), Pt(after), line


# ── Document building blocks ─────────────────────────────────────────────

class Doc:
    def __init__(self):
        self.d = Document()
        section = self.d.sections[0]
        section.page_width, section.page_height = Cm(21), Cm(29.7)
        section.left_margin = section.right_margin = Cm(2.2)
        section.top_margin, section.bottom_margin = Cm(2), Cm(2)
        normal = self.d.styles["Normal"]
        normal.font.name, normal.font.size = FONT, Pt(11)
        normal.font.color.rgb = INK
        normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        for name, size, color in (("Heading 1", 16, INK), ("Heading 2", 13, INK), ("Title", 24, INK)):
            style = self.d.styles[name]
            style.font.name, style.font.size, style.font.color.rgb, style.font.bold = FONT, Pt(size), color, True
            style.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
            rfonts = style.element.rPr.rFonts
            rfonts.set(qn("w:ascii"), FONT)
            rfonts.set(qn("w:hAnsi"), FONT)
        self.d.styles["Heading 1"].paragraph_format.space_before = Pt(18)
        self.d.styles["Heading 1"].paragraph_format.space_after = Pt(6)
        self.d.styles["Heading 2"].paragraph_format.space_before = Pt(12)
        self.d.styles["Heading 2"].paragraph_format.space_after = Pt(4)
        self._footer()

    def _footer(self):
        footer = self.d.sections[0].footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run(footer, "Permission-aware knowledge search · page ", color=FAINT, size=9)
        field = OxmlElement("w:fldSimple")
        field.set(qn("w:instr"), "PAGE")
        r = OxmlElement("w:r")
        rpr = OxmlElement("w:rPr")
        sz = OxmlElement("w:sz")
        sz.set(qn("w:val"), "18")
        rpr.append(sz)
        t = OxmlElement("w:t")
        t.text = "1"
        r.append(rpr)
        r.append(t)
        field.append(r)
        footer._p.append(field)

    def h1(self, text):
        self.d.add_heading(text, level=1)

    def h2(self, text):
        self.d.add_heading(text, level=2)

    def p(self, text, *, color=None, size=None, after=6, italic=False):
        para = self.d.add_paragraph()
        rich(para, text, color=color, size=size, italic=italic)
        spacing(para, after=after)
        return para

    def bullets(self, items):
        for item in items:
            para = self.d.add_paragraph(style="List Bullet")
            rich(para, item)
            spacing(para, after=3)

    def code(self, text):
        table = self.d.add_table(rows=1, cols=1)
        cell = table.cell(0, 0)
        shade(cell, FILL["head"])
        cell_margins(table, 0.3)
        keep_row_together(table)
        para = cell.paragraphs[0]
        for n, line in enumerate(text.splitlines()):
            if n:
                para.add_run().add_break(WD_BREAK.LINE)
            run(para, line, mono=True, size=9.5)
        self.gap()

    def gap(self, pt=4):
        spacing(self.d.add_paragraph(), after=pt)

    def box(self, title, lines, *, kind="issue"):
        """A tinted box with a coloured bar: examples (issue colour) or fixes (good colour)."""
        color = {"issue": ("A3431A", ISSUE, FILL["issue"]), "good": ("1C7447", GOOD, FILL["good"]),
                 "accent": ("1F55A8", ACCENT, FILL["accent"])}[kind]
        table = self.d.add_table(rows=1, cols=1)
        cell = table.cell(0, 0)
        shade(cell, color[2])
        left_bar(cell, color[0])
        cell_margins(table, 0.3)
        keep_row_together(table)
        first = cell.paragraphs[0]
        run(first, title.upper(), bold=True, color=color[1], size=9)
        spacing(first, after=3)
        for line in lines:
            if line.startswith("• "):
                para = cell.add_paragraph(style="List Bullet")
                rich(para, line[2:], size=10.5)
            else:
                para = cell.add_paragraph()
                rich(para, line, size=10.5)
            spacing(para, after=3)
        self.gap()

    def table(self, header, rows, cm, *, highlight_row=None, num_cols=(), decision_colors=False):
        table = self.d.add_table(rows=1, cols=len(header))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        borders(table)
        cell_margins(table, 0.18)
        for cell, text in zip(table.rows[0].cells, header):
            shade(cell, FILL["head"])
            para = cell.paragraphs[0]
            run(para, text, bold=True, color=SOFT, size=9.5)
        for index, values in enumerate(rows):
            cells = table.add_row().cells
            for col, (cell, text) in enumerate(zip(cells, values)):
                para = cell.paragraphs[0]
                bold = index == highlight_row
                rich(para, text, size=10)
                if bold:
                    for r in para.runs:
                        r.bold = True
                    shade(cell, FILL["accent"])
                if col in num_cols:
                    para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                if decision_colors and col == 0:
                    tone = {"Required": GOOD, "Recommended": ACCENT, "Not recommended": ISSUE}.get(text)
                    for r in para.runs:
                        r.bold, r.font.color.rgb = True, tone
        widths(table, cm)
        self.gap()

    def flow(self, title, steps, *, fill="box"):
        """A left-to-right flow drawn as a table: boxes with arrows between them (editable in Word)."""
        self.p(f"**{title}**", color=SOFT, size=10, after=3).paragraph_format.keep_with_next = True
        cols = len(steps) * 2 - 1
        table = self.d.add_table(rows=1, cols=cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        no_borders(table)
        cell_margins(table, 0.12)
        keep_row_together(table)
        box_w = (16.6 - 0.6 * (len(steps) - 1)) / len(steps)
        for i, cell in enumerate(table.rows[0].cells):
            para = cell.paragraphs[0]
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if i % 2:
                run(para, "→", bold=True, color=ACCENT, size=14)
                cell.width = Cm(0.6)
            else:
                step = steps[i // 2]
                shade(cell, FILL["accent"] if step.get("key") else FILL[fill])
                run(para, step["text"], bold=bool(step.get("key")), size=9.5)
                cell.width = Cm(box_w)
        table.autofit = False
        self.gap()

    def issue(self, number, title, intro, example_lines, fix=None):
        label = self.d.add_paragraph()
        run(label, f"ISSUE {number}", bold=True, color=ISSUE, size=9)
        spacing(label, before=10, after=0)
        label.paragraph_format.keep_with_next = True
        self.h2(title)
        if intro:
            self.p(intro).paragraph_format.keep_with_next = True
        self.box("Example", example_lines, kind="issue")
        if fix:
            self.box("With one collection and a filter", [fix], kind="good")

    def save(self):
        OUT.parent.mkdir(parents=True, exist_ok=True)
        self.d.save(OUT)
        return OUT


# ── Content ──────────────────────────────────────────────────────────────

def build() -> Path:
    doc = Doc()
    d = doc.d

    eyebrow = d.add_paragraph()
    run(eyebrow, "SYTELINE PROSPECT-TO-CASH ASSISTANT · DESIGN NOTE", bold=True, color=FAINT, size=9)
    spacing(eyebrow, after=2)
    title = d.add_paragraph(style="Title")
    run(title, "Permission-aware knowledge search")
    spacing(title, after=6)
    doc.p("How the assistant should limit document search to what each user is allowed to see in SyteLine, and "
          "why one collection with permission labels works better than one collection per module.",
          color=SOFT, size=12, after=6)
    doc.p("30 September 2026   ·   Status: proposal for review   ·   Applies to: document and Q&A search",
          color=FAINT, size=9.5, after=12)

    # Summary
    doc.h1("Summary")
    doc.table(
        ["Decision", "Topic", "Conclusion"],
        [["Required", "Search follows SyteLine authorization",
          "Answers must only use knowledge about the modules, forms and files the user may open. Today anyone "
          "allowed to use search can get answers from every document."],
         ["Recommended", "One collection + permission labels + filter",
          "Label every piece of text with module, form and allowed roles, and filter each search by the user's "
          "permissions."],
         ["Not recommended", "One collection per module",
          "Breaks questions that span modules, can't express form-level access, and doesn't make search faster "
          "(the vector search is only 15 ms of each question)."]],
        [3.0, 4.6, 9.0], decision_colors=True)

    # Today
    doc.h1("What the system does today")
    doc.p("All knowledge sits in one Milvus collection, `ptc_knowledge`, with **877 vectors**: 148 document "
          "sections, 201 table rows and 528 Excel Q&A wordings. Each question is searched by meaning (vectors) and "
          "by keywords, the best matches are re-ranked, and the AI writes the answer from the top matches.")
    doc.p("Before searching, the assistant checks one permission: “may this user use document search?”. If yes, "
          "the whole collection is searched.")
    doc.box("The gap, with an example", [
        "A sales rep has access to the **Customers** and **Customer Orders** forms, but not to **A/R Posted "
        "Transactions**. They ask “How do I write off a small balance on an invoice?”.",
        "Today the search can return the Accounts Receivable write-off procedure, and the AI will explain it. The "
        "user learns a process that SyteLine itself hides from them.",
    ])
    doc.p("Answers must follow the same rules as SyteLine: a user only gets knowledge about the modules, forms and "
          "files they are allowed to open.")

    # Options
    doc.h1("Two ways to add permissions to search")
    doc.flow("Option A — one collection per module", [
        {"text": "Question"}, {"text": "User's allowed modules"},
        {"text": "Search Order Entry, Credit and Shipping collections (3 searches)", "key": True},
        {"text": "Merge the 3 result lists"}, {"text": "Re-rank → AI answer"}])
    doc.flow("Option B — one collection, permission labels and a filter (recommended)", [
        {"text": "Question"}, {"text": "User's SyteLine permissions: modules, forms, roles"},
        {"text": "One search, filtered to permitted text only", "key": True},
        {"text": "Re-rank → AI answer from permitted text"}, {"text": "Audit: documents used"}])
    doc.p("Both options keep unauthorized text away from the AI. The difference is how well they handle real "
          "SyteLine questions and permissions, and how much work they create.")

    # Issues
    doc.h1("Issues with one collection per module")
    doc.issue(1, "Prospect-to-Cash questions cross modules",
              "The Prospect-to-Cash process runs across several modules. Most real problems touch two or three of them.",
              ["“Why is customer order CO1001 not shipping?” The answer needs the **credit hold** rules (Credit / "
               "A/R), the **order status** rules (Order Entry) and the **pick and ship** steps (Shipping).",
               "• One collection per module: three separate searches, then the results must be merged.",
               "• One collection with a filter: one search across everything the user may see."])
    doc.issue(2, "Scores from different collections can't be compared fairly",
              "Keyword scores depend on how rare a word is inside the collection being searched. The same word scores "
              "very differently in different collections.",
              ["The word **“credit”** appears in almost every section of a Credit collection, so it scores low there. "
               "In an Order Entry collection it is rare, so a single passing mention scores high.",
               "When the results are merged, a weak Order Entry section can outrank the correct Credit section. The "
               "user gets the wrong document."],
              "All text is scored on the same scale in one search, so rankings stay comparable.")
    doc.issue(3, "SyteLine permissions are per form, not per module",
              "SyteLine grants access to individual forms. A collection per module can only say “all of this module” "
              "or “none of it”.",
              ["A sales rep may open **Customer Credit Hold** (to see why an order is blocked) but not **A/R Posted "
               "Transactions** or **Write-offs**, even though all three belong to Accounts Receivable.",
               "• One collection per module must give the whole A/R collection (too much) or none of it (too little).",
               "• To be exact it would need a collection per module and per form. With, for example, 8 modules of "
               "8–10 forms each, that is 60–80 collections."],
              "Each piece of text carries its form, so the filter can allow Customer Credit Hold and block Write-offs "
              "in the same module.")
    doc.issue(4, "One document often belongs to several modules", None,
              ["The **Credit Hold** procedure is needed by Order Entry users (orders are blocked) and by A/R users "
               "(who release the hold). With one collection per module it is copied into two collections.",
               "• When the procedure changes, both copies must be updated. If one is missed, the two teams get "
               "different answers.",
               "• A user with both modules gets the same section twice in their results."],
              "The document is stored once, labelled with both modules: `modules = [\"Order Entry\", \"Accounts Receivable\"]`.")
    doc.issue(5, "A permission change means moving data", None,
              ["The business decides sales reps may now see **Price Books**.",
               "• One collection per module or role: that text has to be copied or re-indexed into another collection.",
               "• One collection with a filter: nothing is re-indexed; the next search uses the user's new "
               "permissions from SyteLine."])
    doc.issue(6, "Every change is repeated per collection",
              "Each collection has its own schema, vector index, keyword index, loading step and monitoring.",
              ["Adding one new field (for example an `allowed_roles` label) or switching to a better embedding model "
               "means changing, re-loading and testing every collection: 8 or more instead of 1. The Excel Q&A would "
               "need the same split."])

    label = d.add_paragraph()
    run(label, "ISSUE 7", bold=True, color=ISSUE, size=9)
    spacing(label, before=10, after=0)
    label.paragraph_format.keep_with_next = True
    doc.h2("It does not make answers faster")
    doc.p("Measured on the current server, per question, for the document-search step:")
    doc.table(
        ["Part of the search", "Time", "Share"],
        [["Turn the question into a vector (embedding model)", "22 ms", "7%"],
         ["Milvus vector search — the only part collections would affect", "15 ms", "4%"],
         ["Keyword search (BM25)", "0.4 ms", "0%"],
         ["Re-rank the best matches (cross-encoder model)", "294 ms", "89%"],
         ["Total document search", "331 ms", ""]],
        [11.6, 2.5, 2.5], highlight_row=1, num_cols=(1, 2))
    doc.p("A full answer takes 5–8 seconds. Almost all of that is the OpenAI calls (understanding the question, "
          "writing and checking the answer) and the re-ranking. Splitting 877 vectors into several collections could "
          "save a few milliseconds of the 15 ms; with several collections to search per question it can even be slower.")
    doc.box("What actually speeds it up", [
        "Running the re-ranking one question at a time instead of all at once under load. Measured: with 25 users "
        "asking at once, the document step grew from about 3 s to 26 s, while the OpenAI steps stayed the same.",
        "Later: a GPU for the models, or more servers.",
    ], kind="good")

    # When collections are right
    doc.h1("When separate collections are the right choice")
    doc.p("Separate collections make sense when data must be **physically separated**, not only filtered:")
    doc.bullets(["Different companies or customers on the same server (multi-tenant hosting).",
                 "A legal or contract rule that one group's documents may never be stored with another's.",
                 "Collections that use different embedding models or languages."])
    doc.p("None of these apply to one company's Prospect-to-Cash knowledge, where roles overlap and questions cross modules.")

    # Recommended design
    doc.h1("Recommended design")
    doc.h2("1. Label every piece of text")
    doc.p("Add permission fields to each vector in the existing collection:")
    doc.table(
        ["Field", "Example", "Filled from"],
        [["`modules`", "[\"Order Entry\", \"Accounts Receivable\"]", "Document metadata (Module)"],
         ["`forms`", "[\"Customer Orders\", \"Customer Credit Hold\"]", "Document metadata (Form)"],
         ["`allowed_roles`", "[\"SALES_REP\", \"AR_CLERK\", \"CREDIT_MANAGER\"]", "New “Allowed roles” field in the data template"],
         ["`source_file`", "credit_hold.md", "Already stored"]],
        [3.4, 7.2, 6.0])
    doc.h2("2. Filter every search by the user's permissions")
    doc.p("The assistant already reads the user's SyteLine session. From it we take the forms and roles they may use "
          "and build a Milvus filter, so the search never sees anything else:")
    doc.code('array_contains_any(allowed_roles, ["SALES_REP"])\n'
             'and array_contains_any(forms, ["Customers", "Customer Orders", "Customer Credit Hold"])')
    doc.p("The keyword search and the Excel Q&A get the same filter. Text the user may not see is never re-ranked, "
          "never sent to the AI and never quoted.")
    doc.h2("3. Speed as the data grows")
    doc.p("If the knowledge base grows to many thousands of documents, Milvus **partition keys** (for example on "
          "`module`) let a filtered search skip whole groups of data inside the same collection. That gives the speed "
          "benefit expected from separate collections, without the issues above.")
    doc.h2("4. Field-level security")
    doc.p("Field-level rules (for example “this role cannot see Credit Limit”) matter most for **live SyteLine data**. "
          "In Phase 4 the assistant reads live data through SyteLine's own API (IDOs) with the user's own session, so "
          "SyteLine applies its field security itself. For documents, a section about a restricted field is labelled "
          "with that form and field, and the same filter applies.")
    doc.h2("5. Audit")
    doc.p("Every answer already records which documents were used. With the filter in place, the audit also shows "
          "that only permitted documents were searched.")

    # Steps
    doc.h1("Implementation steps")
    doc.table(
        ["Step", "What", "Details"],
        [["1", "Data template", "Add an “Allowed roles” field next to Module and Form. The data team fills it for each "
                                "document and each Excel row."],
         ["2", "Indexing", "Store `modules`, `forms` and `allowed_roles` on every vector and keyword entry. Re-index once."],
         ["3", "Search", "Build the filter from the user's permissions and apply it to vector search, keyword search "
                         "and Excel Q&A."],
         ["4", "Test with test roles", "Sales rep, AR clerk, support admin: each role must only get answers from its "
                                       "own documents, including cross-module questions."],
         ["5", "Phase 4", "Replace the test roles with the real role-to-form mapping from SyteLine."]],
        [1.4, 3.6, 11.6], num_cols=())
    doc.p("**Needed from others:** the data team labels documents with allowed roles, and the SyteLine team confirms "
          "how roles map to forms (part of the Phase 4 API questions).")

    note = doc.p("Measurements taken on 30 September 2026 on the development server: 877 vectors in one Milvus "
                 "collection; timings are averages over 18 searches; the load test used 6, 12 and 25 users asking at "
                 "the same moment.", color=FAINT, size=9)
    spacing(note, before=14)
    return doc.save()


if __name__ == "__main__":
    print(f"written {build()}")
