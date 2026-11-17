"""Add nullable marks and policy without altering historical grades."""
from alembic import op
import sqlalchemy as sa

revision = "msr_0001"
down_revision = "bb83782c0e2d"
branch_labels = None
depends_on = None


def upgrade():
    for name in (
        "maximum_marks",
        "passing_marks",
        "marks_obtained",
    ):
        op.add_column(
            "subjects",
            sa.Column(
                name,
                sa.Numeric(10, 2),
                nullable=True,
            ),
        )

    op.add_column(
        "subjects",
        sa.Column(
            "master_managed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "subjects",
        sa.Column(
            "record_version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )

    op.create_table(
        "academic_policy",
        sa.Column(
            "id", sa.Integer(), primary_key=True
        ),
        sa.Column(
            "version", sa.Integer(), nullable=False
        ),
        sa.Column(
            "configuration", sa.JSON(), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False
        ),
    )

    policy_table = sa.table(
        "academic_policy",
        sa.column("id", sa.Integer()),
        sa.column("version", sa.Integer()),
        sa.column("configuration", sa.JSON()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )

    configuration = {
        "name": (
            "Illustrative 10-point policy "
            "— administrator must verify"
        ),
        "basis": "percentage",
        "boundary_max": 100,
        "max_point": 10,
        "conversion": "",
        "include_failed": True,
        "bands": [
            {
                "letter": label,
                "min": low,
                "max": high,
                "point": point,
                "passing": passed,
            }
            for label, low, high, point, passed in [
                ("F", 0, 40, 0, False),
                ("P", 40, 45, 4, True),
                ("C", 45, 50, 5, True),
                ("B", 50, 60, 6, True),
                ("B+", 60, 70, 7, True),
                ("A", 70, 80, 8, True),
                ("A+", 80, 90, 9, True),
                ("O", 90, 100, 10, True),
            ]
        ],
    }

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).replace(
        tzinfo=None
    )
    op.bulk_insert(
        policy_table,
        [
            {
                "id": 1,
                "version": 1,
                "configuration": configuration,
                "created_at": now,
                "updated_at": now,
            }
        ],
    )


def downgrade():
    raise RuntimeError(
        "Destructive downgrade disabled: it would delete "
        "saved marks and grading policy. "
        "Restore a reviewed backup instead."
    )
