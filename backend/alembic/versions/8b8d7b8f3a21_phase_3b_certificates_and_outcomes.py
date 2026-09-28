"""Phase 3B/3C certificates and longitudinal outcomes

Revision ID: 8b8d7b8f3a21
Revises: 241b0c73b130
Create Date: 2026-09-28 15:40:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "8b8d7b8f3a21"
down_revision: Union[str, Sequence[str], None] = "241b0c73b130"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL enum values are separate types and require an explicit ALTER.
    op.execute("ALTER TYPE proficiencysource ADD VALUE IF NOT EXISTS 'CERTIFICATION'")

    # These are named PostgreSQL enum types. The original migration created the
    # types explicitly and then reused Enum objects in create_table(), causing
    # SQLAlchemy to attempt CREATE TYPE a second time on some PostgreSQL setups.
    # Create the types idempotently here, then tell the table columns not to
    # create them again. This also recovers cleanly if a previous failed run
    # left the enum types behind while the tables were not created.
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE certificatestatus AS ENUM ('ISSUED', 'REVOKED', 'EXPIRED');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE outcomeverificationstatus AS ENUM (
                'SELF_REPORTED', 'EMPLOYER_VERIFIED', 'DOCUMENT_VERIFIED'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE outcomeemploymentstatus AS ENUM (
                'EMPLOYED',
                'SELF_EMPLOYED',
                'FREELANCER',
                'ENTREPRENEUR',
                'APPRENTICESHIP',
                'HIGHER_STUDIES',
                'SEEKING_EMPLOYMENT',
                'NOT_CURRENTLY_WORKING'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    certificate_status = postgresql.ENUM(
        "ISSUED", "REVOKED", "EXPIRED",
        name="certificatestatus", create_type=False
    )
    outcome_verification_status = postgresql.ENUM(
        "SELF_REPORTED", "EMPLOYER_VERIFIED", "DOCUMENT_VERIFIED",
        name="outcomeverificationstatus", create_type=False
    )
    outcome_employment_status = postgresql.ENUM(
        "EMPLOYED",
        "SELF_EMPLOYED",
        "FREELANCER",
        "ENTREPRENEUR",
        "APPRENTICESHIP",
        "HIGHER_STUDIES",
        "SEEKING_EMPLOYMENT",
        "NOT_CURRENTLY_WORKING",
        name="outcomeemploymentstatus", create_type=False
    )

    op.create_table(
        "certificates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("certificate_number", sa.String(length=64), nullable=False),
        sa.Column("learner_id", sa.Uuid(), nullable=False),
        sa.Column("training_program_id", sa.Uuid(), nullable=False),
        sa.Column("enrollment_id", sa.Uuid(), nullable=False),
        sa.Column("certificate_name", sa.String(length=255), nullable=False),
        sa.Column("issue_date", sa.Date(), server_default=sa.text("CURRENT_DATE"), nullable=False),
        sa.Column("status", certificate_status, nullable=False),
        sa.Column("verification_code", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["enrollment_id"], ["training_enrollments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["learner_id"], ["learner_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["training_program_id"], ["training_programs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("certificate_number"),
        sa.UniqueConstraint("enrollment_id"),
        sa.UniqueConstraint("verification_code"),
    )
    op.create_index("ix_certificates_certificate_number", "certificates", ["certificate_number"], unique=True)
    op.create_index("ix_certificates_learner_id", "certificates", ["learner_id"], unique=False)
    op.create_index("ix_certificates_training_program_id", "certificates", ["training_program_id"], unique=False)
    op.create_index("ix_certificates_enrollment_id", "certificates", ["enrollment_id"], unique=True)
    op.create_index("ix_certificates_verification_code", "certificates", ["verification_code"], unique=True)

    op.create_table(
        "certificate_skills",
        sa.Column("certificate_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["certificate_id"], ["certificates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("certificate_id", "skill_id"),
    )

    op.create_table(
        "outcome_checkins",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("learner_id", sa.Uuid(), nullable=False),
        sa.Column("milestone_months", sa.Integer(), nullable=False),
        sa.Column("check_in_date", sa.Date(), server_default=sa.text("CURRENT_DATE"), nullable=False),
        sa.Column("employment_status", outcome_employment_status, nullable=False),
        sa.Column("employer_name", sa.String(length=255), nullable=True),
        sa.Column("role_title", sa.String(length=255), nullable=True),
        sa.Column("industry", sa.String(length=255), nullable=True),
        sa.Column("district", sa.String(length=255), nullable=True),
        sa.Column("state", sa.String(length=255), nullable=True),
        sa.Column("income_band", sa.String(length=100), nullable=True),
        sa.Column("same_employer", sa.Boolean(), nullable=True),
        sa.Column("training_relevance_score", sa.Integer(), nullable=True),
        sa.Column("using_training_skills", sa.Boolean(), nullable=True),
        sa.Column("skill_gap_notes", sa.String(length=2000), nullable=True),
        sa.Column("verification_status", outcome_verification_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["learner_id"], ["learner_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("learner_id", "milestone_months", name="uq_learner_outcome_milestone"),
    )
    op.create_index("ix_outcome_checkins_learner_id", "outcome_checkins", ["learner_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_outcome_checkins_learner_id", table_name="outcome_checkins")
    op.drop_table("outcome_checkins")
    op.drop_table("certificate_skills")
    op.drop_index("ix_certificates_verification_code", table_name="certificates")
    op.drop_index("ix_certificates_enrollment_id", table_name="certificates")
    op.drop_index("ix_certificates_training_program_id", table_name="certificates")
    op.drop_index("ix_certificates_learner_id", table_name="certificates")
    op.drop_index("ix_certificates_certificate_number", table_name="certificates")
    op.drop_table("certificates")

    op.execute("DROP TYPE IF EXISTS outcomeemploymentstatus")
    op.execute("DROP TYPE IF EXISTS outcomeverificationstatus")
    op.execute("DROP TYPE IF EXISTS certificatestatus")
    # PostgreSQL does not support removing an enum value safely in-place.
    # Keep the CERTIFICATION value in proficiencysource on downgrade.
