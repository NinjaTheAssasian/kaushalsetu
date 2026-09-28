"""Phase 5 job-market intelligence: job postings and skill requirement mappings.

Revision ID: c9d4e5f6a7b8
Revises: 5f7a9c3d2e11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c9d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "5f7a9c3d2e11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_postings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("employer_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("role_family", sa.String(length=120), nullable=False),
        sa.Column("industry", sa.String(length=120), nullable=False),
        sa.Column("district", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=120), nullable=False),
        sa.Column("employment_type", sa.String(length=50), nullable=True),
        sa.Column("salary_band", sa.String(length=100), nullable=True),
        sa.Column("experience_min_years", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("posted_at", sa.Date(), server_default=sa.text("CURRENT_DATE"), nullable=False),
        sa.Column("closing_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["employer_id"], ["employers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_postings_employer_id", "job_postings", ["employer_id"])
    op.create_index("ix_job_postings_role_family", "job_postings", ["role_family"])
    op.create_index("ix_job_postings_industry", "job_postings", ["industry"])
    op.create_index("ix_job_postings_district", "job_postings", ["district"])
    op.create_index("ix_job_postings_state", "job_postings", ["state"])
    op.create_index("ix_job_postings_is_active", "job_postings", ["is_active"])

    op.create_table(
        "training_program_skills",
        sa.Column("training_program_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["training_program_id"], ["training_programs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("training_program_id", "skill_id"),
    )
    op.create_table(
        "job_posting_skills",
        sa.Column("job_posting_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["job_posting_id"], ["job_postings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("job_posting_id", "skill_id"),
    )
    op.create_index("ix_training_program_skills_skill_id", "training_program_skills", ["skill_id"])
    op.create_index("ix_job_posting_skills_skill_id", "job_posting_skills", ["skill_id"])


def downgrade() -> None:
    op.drop_index("ix_job_posting_skills_skill_id", table_name="job_posting_skills")
    op.drop_index("ix_training_program_skills_skill_id", table_name="training_program_skills")
    op.drop_table("job_posting_skills")
    op.drop_table("training_program_skills")
    op.drop_index("ix_job_postings_is_active", table_name="job_postings")
    op.drop_index("ix_job_postings_state", table_name="job_postings")
    op.drop_index("ix_job_postings_district", table_name="job_postings")
    op.drop_index("ix_job_postings_industry", table_name="job_postings")
    op.drop_index("ix_job_postings_role_family", table_name="job_postings")
    op.drop_index("ix_job_postings_employer_id", table_name="job_postings")
    op.drop_table("job_postings")
