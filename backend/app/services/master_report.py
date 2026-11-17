"""Private PDF and Excel reports generated from a saved-record snapshot."""
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.utils.timeutils import utcnow

HEADERS = [
    "Subject",
    "Course code",
    "Maximum",
    "Passing",
    "Obtained",
    "Credits",
    "Grade",
    "Point",
    "Result",
]
NAVY = "263D88"


def display(value):
    return "—" if value is None or value == "" else str(value)


def summary_rows(info, cumulative=None):
    rows = [
        ["SGPA / CGPA", display(info["gpa"])],
        ["Academic grade", display(info["grade"])],
        ["GPA credits", info["total_credits"]],
        [
            "Credits completed (passed)",
            info["completed_credits"],
        ],
        [
            "Raw marks percentage",
            display(info["raw_percentage"]),
        ],
        [
            "Institutionally converted percentage",
            display(info["converted_percentage"]),
        ],
        [
            "Pending / historical subjects",
            info["pending_subjects"],
        ],
        ["Failed subjects", info["failed_subjects"]],
    ]
    if cumulative:
        rows.append(
            ["Cumulative CGPA", display(cumulative["gpa"])]
        )
        rows.append(
            ["Cumulative grade", display(cumulative["grade"])]
        )
    return rows


def subject_row(subject):
    return [
        subject["name"],
        subject["code"],
        subject["maximum_marks"],
        subject["passing_marks"],
        subject["marks_obtained"],
        subject["credits"],
        subject["grade"] or subject["legacy_grade"],
        subject["grade_point"],
        subject["result"],
    ]


class NumberedCanvas(Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.setFont("SSSReport", 8)
            self.drawRightString(
                self._pagesize[0] - 30,
                18,
                f"Page {self._pageNumber} of {count}",
            )
            Canvas.showPage(self)
        Canvas.save(self)


def pdf_report(data):
    if "SSSReport" not in pdfmetrics.getRegisteredFontNames():
        font = (
            Path(reportlab.__file__).parent
            / "fonts"
            / "Vera.ttf"
        )
        pdfmetrics.registerFont(
            TTFont("SSSReport", str(font))
        )

    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = "SSSReport"

    cell = ParagraphStyle(
        "SSSCell",
        fontName="SSSReport",
        fontSize=8,
        leading=11,
        wordWrap="CJK",
    )

    def text(value):
        return Paragraph(escape(display(value)), cell)

    def table(rows, widths):
        result = Table(
            [
                [text(value) for value in row]
                for row in rows
            ],
            colWidths=widths,
            repeatRows=1,
            hAlign="LEFT",
        )
        result.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#" + NAVY),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.whitesmoke, colors.white],
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.3,
                        colors.lightgrey,
                    ),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        for paragraph in result._cellvalues[0]:
            paragraph.style = ParagraphStyle(
                "SSSHead",
                parent=cell,
                textColor=colors.white,
            )
        return result

    student = data["student"]
    policy = data["policy"]

    story = [
        Paragraph(
            "MASTER SEMESTER REPORT",
            styles["Title"],
        )
    ]

    for label, value in [
        ("Student", student["name"]),
        ("Student ID (SSS)", student["student_id"]),
        ("Course", student["course"]),
        ("Department", student["department"]),
        ("Generated (UTC)", utcnow().isoformat()),
        (
            "Grading policy",
            f"{policy['configuration']['name']} "
            f"— version {policy['version']}",
        ),
    ]:
        story.append(text(f"{label}: {display(value)}"))

    story += [
        Spacer(1, 10),
        text(
            "Provisional self-maintained academic record, "
            "not an institution-certified transcript. "
            "Empty, historical and incomplete records are excluded. "
            "GPAs are credit-weighted. Completed semesters require "
            "all subjects to pass."
        ),
    ]

    for semester in data["semesters"]:
        story.append(
            Paragraph(
                f"Semester {semester['number']}",
                styles["Heading2"],
            )
        )

        if semester["academic_year"]:
            story.append(
                text(
                    f"Academic year: "
                    f"{semester['academic_year']}"
                )
            )

        if semester["subjects"]:
            story.append(
                table(
                    [HEADERS]
                    + [
                        subject_row(subject)
                        for subject in semester["subjects"]
                    ],
                    [
                        154,
                        80,
                        60,
                        60,
                        60,
                        49,
                        45,
                        45,
                        129,
                    ],
                )
            )
        else:
            story.append(text("No saved subjects."))

        story += [
            Spacer(1, 6),
            table(
                [["Semester results", "Value"]]
                + summary_rows(
                    semester, semester["cumulative"]
                ),
                [260, 422],
            ),
            Spacer(1, 12),
        ]

    story.append(
        Paragraph("TOTAL CGPA", styles["Heading1"])
    )
    story.append(
        table(
            [["Overall result", "Value"]]
            + summary_rows(data["total"])
            + [
                [
                    "Completed semesters",
                    data["total"]["completed_semesters"],
                ]
            ],
            [260, 422],
        )
    )

    configuration = policy["configuration"]
    failed_rule = (
        "included in"
        if configuration["include_failed"]
        else "excluded from"
    )

    story += [
        Spacer(1, 12),
        text(
            "Raw percentage = total obtained / total maximum × 100. "
            f"Conversion: "
            f"{configuration['conversion'] or 'Not configured'}. "
            f"Failed subjects {failed_rule} GPA credits. "
            "Bands use inclusive minimum and exclusive maximum, "
            "except the highest maximum is inclusive. "
            "Aggregate grades use the greatest grade-point threshold "
            "not exceeding the unrounded GPA. "
            "Subject passing requires both the configured passing "
            "band and the subject minimum."
        ),
    ]

    buffer = BytesIO()
    SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=30,
        rightMargin=30,
        topMargin=30,
        bottomMargin=35,
        title="Master Semester Report",
    ).build(story, canvasmaker=NumberedCanvas)

    return buffer.getvalue()


def excel_report(data):
    workbook = Workbook()
    overview = workbook.active
    overview.title = "Summary"

    def safe(value):
        if (
            isinstance(value, str)
            and value.lstrip().startswith(
                ("=", "+", "-", "@")
            )
        ):
            return "'" + value
        return value

    def append(worksheet, values):
        worksheet.append([safe(value) for value in values])

    append(
        overview,
        ["MASTER SEMESTER REPORT", "Value"],
    )

    for key, value in data["student"].items():
        append(
            overview,
            [key.replace("_", " ").title(), value],
        )

    append(
        overview,
        ["Generated (UTC)", utcnow().isoformat()],
    )
    append(
        overview,
        [
            "Policy",
            data["policy"]["configuration"]["name"],
        ],
    )
    append(
        overview,
        ["Policy version", data["policy"]["version"]],
    )
    append(
        overview,
        [
            "Conversion",
            data["policy"]["configuration"]["conversion"]
            or "Not configured",
        ],
    )

    for row in summary_rows(data["total"]) + [
        [
            "Completed semesters",
            data["total"]["completed_semesters"],
        ]
    ]:
        append(overview, row)

    for semester in data["semesters"]:
        worksheet = workbook.create_sheet(
            f"Semester {semester['number']}"
        )
        append(worksheet, HEADERS)

        for subject in semester["subjects"]:
            append(worksheet, subject_row(subject))

        append(worksheet, [])
        append(
            worksheet,
            ["Academic year", semester["academic_year"]],
        )

        for row in summary_rows(
            semester, semester["cumulative"]
        ):
            append(worksheet, row)

    for worksheet in workbook:
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions
        worksheet.sheet_properties.pageSetUpPr.fitToPage = True
        worksheet.page_setup.orientation = "landscape"
        worksheet.page_setup.paperSize = worksheet.PAPERSIZE_A4
        worksheet.page_setup.fitToWidth = 1
        worksheet.page_setup.fitToHeight = 0
        worksheet.print_title_rows = "1:1"
        worksheet.oddFooter.center.text = "Page &P of &N"

        for cell in worksheet[1]:
            cell.fill = PatternFill(
                "solid", fgColor=NAVY
            )
            cell.font = Font(
                color="FFFFFF", bold=True
            )

        for column in worksheet.columns:
            worksheet.column_dimensions[
                column[0].column_letter
            ].width = min(
                60,
                max(
                    14,
                    max(
                        len(str(cell.value or ""))
                        for cell in column
                    )
                    + 2,
                ),
            )
            for cell in column:
                cell.alignment = Alignment(
                    vertical="top",
                    wrap_text=True,
                )

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
