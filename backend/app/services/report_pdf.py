"""PDF generation (ReportLab): academic report and achievement portfolio."""
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models import Semester
from app.services.academic import summary
from app.services.achievement import list_for_user
from app.utils.timeutils import today_local

NAVY = colors.HexColor("#1e2a5a")
STYLES = getSampleStyleSheet()


def _doc(buffer, title):
    return SimpleDocTemplate(buffer, pagesize=A4, title=title, leftMargin=18 * mm, rightMargin=18 * mm,
                             topMargin=16 * mm, bottomMargin=16 * mm)


def _table(rows, widths=None):
    table = Table(rows, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9), ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f5f9")]),
    ]))
    return table


def _p(text):
    from xml.sax.saxutils import escape
    return Paragraph(escape(str(text or "")), STYLES["BodyText"])


def _header(user, title):
    name = user.profile.full_name if user.profile else user.email
    parts = [Paragraph(title, STYLES["Title"]), _p(f"{name} — generated {today_local():%d %b %Y}")]
    if user.profile and (user.profile.college or user.profile.degree):
        parts.append(_p(" · ".join(filter(None, [user.profile.degree, user.profile.branch, user.profile.college]))))
    return parts + [Spacer(1, 6 * mm)]


def academic_report(user) -> bytes:
    buffer = io.BytesIO()
    info = summary(user)
    story = _header(user, "Academic Report")
    cgpa = info["cgpa"] if info["cgpa"] is not None else "—"
    story.append(_p(f"CGPA: {cgpa}   Total credits: {info['total_credits']}"))
    if info["mixed_scales"]:
        story.append(_p("Note: semesters use different grading scales; the CGPA mixes scales."))
    story.append(Spacer(1, 4 * mm))
    for sem in Semester.query.filter_by(user_id=user.id).order_by(Semester.number).all():
        data = sem.to_dict()
        story.append(Paragraph(f"{data['title']} — SGPA {data['sgpa'] if data['sgpa'] is not None else '—'}",
                               STYLES["Heading3"]))
        rows = [["Code", "Subject", "Credits", "Grade", "Points"]]
        rows += [[s["code"] or "", _p(s["name"]), s["credits"], s["grade_label"],
                  s["grade_point"] if s["counts_in_gpa"] else "excluded"] for s in data["subjects"]]
        story += [_table(rows, [22 * mm, 80 * mm, 20 * mm, 20 * mm, 25 * mm]), Spacer(1, 4 * mm)]
    if info["semester_count"] == 0:
        story.append(_p("No semester records yet."))
    _doc(buffer, "Academic Report").build(story)
    return buffer.getvalue()


def portfolio(user) -> bytes:
    buffer = io.BytesIO()
    story = _header(user, "Achievement Portfolio")
    items = list_for_user(user)
    if not items:
        story.append(_p("No achievements recorded yet."))
    else:
        rows = [["Date", "Title", "Category", "Organization", "Rank"]]
        rows += [[a.achieved_on.strftime("%d %b %Y"), _p(a.title), a.category.title(),
                  _p(a.organization), _p(a.rank_position)] for a in items]
        story.append(_table(rows, [24 * mm, 60 * mm, 25 * mm, 45 * mm, 20 * mm]))
    _doc(buffer, "Achievement Portfolio").build(story)
    return buffer.getvalue()
