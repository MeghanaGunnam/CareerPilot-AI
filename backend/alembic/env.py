from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from backend.app.core.config import settings
from backend.app.core.database import Base
from backend.app.auth.models import User  # noqa: F401
from backend.app.students.models import (
    CareerGoal,
    Certification,
    Education,
    Experience,
    Project,
    StudentProfile,
)   # noqa: F401

config = context.config

# Use CareerPilot's environment configuration instead of
# hard-coding database credentials in alembic.ini.
config.set_main_option("sqlalchemy.url", settings.database_url)


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# All SQLAlchemy models will inherit from this Base.
# Alembic uses its metadata for autogeneration.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
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