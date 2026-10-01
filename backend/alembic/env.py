from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from backend.app.core.config import settings
from backend.app.core.database import Base

# Import every SQLAlchemy model before target_metadata is used.
# This allows Alembic to discover the tables during autogeneration.
from backend.app.auth.models import User  # noqa: F401

from backend.app.students.models import (
    CareerGoal,
    Certification,
    Education,
    Experience,
    Project,
    StudentProfile,
)  # noqa: F401

from backend.app.careers.models import (
    Career,
    CareerRiasecProfile,
    CareerSkillRequirement,
    CareerSoftwareRequirement,
)  # noqa: F401  # noqa: F401
from backend.app.psychometrics.models import (
    RiasecAnswer,
    RiasecAssessment,
    RiasecProfile,
)  # noqa: F401
from backend.app.resumes.models import (
    Resume,
    ResumeVersion,
)  # noqa: F401
from backend.app.skills.models import (
    Skill,
    StudentSkill,
    SkillEvidence,
)  # noqa: F401
from backend.app.assessments.models import (
    Assessment,
    AssessmentQuestion,
    AssessmentAttempt,
    AssessmentAnswer,
)  # noqa: F401
from backend.app.career_twin.models import (
    CareerTwin,
    CareerTwinEvent,
    CareerTwinSnapshot,
)  # noqa: F401
config = context.config

# Use the database URL from backend/.env.
config.set_main_option(
    "sqlalchemy.url",
    settings.database_url,
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Alembic reads all registered SQLAlchemy tables
# from this metadata object.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without creating a DB connection."""

    url = config.get_main_option(
        "sqlalchemy.url"
    )

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named"
        },
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using a database connection."""

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {},
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()