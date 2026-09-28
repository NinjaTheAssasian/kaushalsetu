"""Phase 4 employer integration, employment verification, and skill feedback.

Revision ID: 5f7a9c3d2e11
Revises: 8b8d7b8f3a21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "5f7a9c3d2e11"
down_revision: Union[str, Sequence[str], None] = "8b8d7b8f3a21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ensure_enum(name: str, values: list[str]) -> None:
    rendered = ", ".join("%s" % sa.text(f"'{v}'").text for v in values)
    # Values are hard-coded by this migration, not user input.
    op.execute(
        f"""
        DO $$
        BEGIN
            CREATE TYPE {name} AS ENUM ({rendered});
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )


def upgrade() -> None:
    _ensure_enum(
        "employmenttype",
        ["FULL_TIME", "PART_TIME", "CONTRACT", "INTERNSHIP", "APPRENTICESHIP"],
    )
    _ensure_enum("employmentrecordstatus", ["ACTIVE", "ENDED"])
    _ensure_enum(
        "employmentverificationstatus",
        ["SELF_REPORTED", "PENDING", "EMPLOYER_VERIFIED", "REVOKED"],
    )

    employment_type = postgresql.ENUM(
        "FULL_TIME", "PART_TIME", "CONTRACT", "INTERNSHIP", "APPRENTICESHIP",
        name="employmenttype", create_type=False,
    )
    employment_record_status = postgresql.ENUM(
        "ACTIVE", "ENDED", name="employmentrecordstatus", create_type=False,
    )
    employment_verification_status = postgresql.ENUM(
        "SELF_REPORTED", "PENDING", "EMPLOYER_VERIFIED", "REVOKED",
        name="employmentverificationstatus", create_type=False,
    )

    op.create_table(
        "employment_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("learner_id", sa.Uuid(), nullable=False),
        sa.Column("employer_id", sa.Uuid(), nullable=True),
        sa.Column("role_title", sa.String(length=255), nullable=False),
        sa.Column("reported_employer_name", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=255), nullable=True),
        sa.Column("employment_type", employment_type, nullable=False),
        sa.Column("district", sa.String(length=255), nullable=True),
        sa.Column("state", sa.String(length=255), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("salary_band", sa.String(length=100), nullable=True),
        sa.Column("status", employment_record_status, nullable=False),
        sa.Column("verification_status", employment_verification_status, nullable=False),
        sa.Column("verification_code_hash", sa.String(length=128), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["learner_id"], ["learner_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employer_id"], ["employers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("verification_code_hash", name="uq_employment_verification_hash"),
    )
    op.create_index("ix_employment_records_learner_id", "employment_records", ["learner_id"])
    op.create_index("ix_employment_records_employer_id", "employment_records", ["employer_id"])
    op.create_index("ix_employment_records_verification_code_hash", "employment_records", ["verification_code_hash"], unique=True)
    op.create_index(
        "uq_active_employment_per_learner",
        "employment_records",
        ["learner_id"],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )

    op.create_table(
        "employer_skill_feedback",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("employment_record_id", sa.Uuid(), nullable=False),
        sa.Column("employer_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Uuid(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comments", sa.String(length=2000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("rating >= 0 AND rating <= 100", name="ck_employer_skill_feedback_rating"),
        sa.ForeignKeyConstraint(["employment_record_id"], ["employment_records.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employer_id"], ["employers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employment_record_id", "skill_id", name="uq_employment_skill_feedback"),
    )
    op.create_index("ix_employer_skill_feedback_employment_record_id", "employer_skill_feedback", ["employment_record_id"])
    op.create_index("ix_employer_skill_feedback_employer_id", "employer_skill_feedback", ["employer_id"])
    op.create_index("ix_employer_skill_feedback_skill_id", "employer_skill_feedback", ["skill_id"])


def downgrade() -> None:
    op.drop_index("ix_employer_skill_feedback_skill_id", table_name="employer_skill_feedback")
    op.drop_index("ix_employer_skill_feedback_employer_id", table_name="employer_skill_feedback")
    op.drop_index("ix_employer_skill_feedback_employment_record_id", table_name="employer_skill_feedback")
    op.drop_table("employer_skill_feedback")

    op.drop_index("uq_active_employment_per_learner", table_name="employment_records")
    op.drop_index("ix_employment_records_verification_code_hash", table_name="employment_records")
    op.drop_index("ix_employment_records_employer_id", table_name="employment_records")
    op.drop_index("ix_employment_records_learner_id", table_name="employment_records")
    op.drop_table("employment_records")

    op.execute("DROP TYPE IF EXISTS employmentverificationstatus")
    op.execute("DROP TYPE IF EXISTS employmentrecordstatus")
    op.execute("DROP TYPE IF EXISTS employmenttype")
