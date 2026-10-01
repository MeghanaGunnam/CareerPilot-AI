import csv
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.app.careers.models import (
    Career,
    CareerSkillRequirement,
    CareerSoftwareRequirement,
)


ONET_VERSION = "31.0"

DATA_DIRECTORY = Path(
    "data/onet/31.0/db_31_0_csv"
)


def clean_text(value: str | None) -> str:
    return (value or "").strip()


def parse_float(value: str | None) -> float | None:
    text = clean_text(value)

    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def parse_onet_boolean(value: str | None) -> bool | None:
    text = clean_text(value).lower()

    if not text:
        return None

    if text in {
        "y",
        "yes",
        "true",
        "1",
    }:
        return True

    if text in {
        "n",
        "no",
        "false",
        "0",
    }:
        return False

    return None


def load_career_map(
    db: Session,
) -> dict[str, Career]:
    careers = db.scalars(
        select(Career)
    ).all()

    return {
        career.onet_soc_code.strip(): career
        for career in careers
    }


def import_skill_file(
    db: Session,
    file_path: Path,
    skill_type: str,
    career_map: dict[str, Career],
) -> tuple[int, int]:
    created = 0
    skipped = 0

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            onet_code = clean_text(
                row.get("O*NET-SOC Code")
            )

            career = career_map.get(onet_code)

            if career is None:
                skipped += 1
                continue

            element_id = clean_text(
                row.get("Element ID")
            )
            element_name = clean_text(
                row.get("Element Name")
            )
            scale_id = clean_text(
                row.get("Scale ID")
            )
            scale_name = clean_text(
                row.get("Scale Name")
            )

            data_value = parse_float(
                row.get("Data Value")
            )

            if (
                not element_id
                or not element_name
                or not scale_id
                or not scale_name
                or data_value is None
            ):
                skipped += 1
                continue

            requirement = CareerSkillRequirement(
                career_id=career.id,
                skill_type=skill_type,
                element_id=element_id,
                element_name=element_name,
                scale_id=scale_id,
                scale_name=scale_name,
                data_value=data_value,
                not_relevant=parse_onet_boolean(
                    row.get("Not Relevant")
                ),
                recommend_suppress=parse_onet_boolean(
                    row.get("RecommendSuppress")
                ),
                source_date=(
                    clean_text(row.get("Date"))
                    or None
                ),
                domain_source=(
                    clean_text(
                        row.get("Domain Source")
                    )
                    or None
                ),
                onet_version=ONET_VERSION,
            )

            db.add(requirement)
            created += 1

    return created, skipped


def import_software_file(
    db: Session,
    file_path: Path,
    career_map: dict[str, Career],
) -> tuple[int, int]:
    created = 0
    skipped = 0

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            onet_code = clean_text(
                row.get("O*NET-SOC Code")
            )

            career = career_map.get(onet_code)

            if career is None:
                skipped += 1
                continue

            element_id = clean_text(
                row.get("Element ID")
            )
            element_name = clean_text(
                row.get("Element Name")
            )
            workplace_example = clean_text(
                row.get("Workplace Example")
            )

            if (
                not element_id
                or not element_name
                or not workplace_example
            ):
                skipped += 1
                continue

            requirement = CareerSoftwareRequirement(
                career_id=career.id,
                element_id=element_id,
                element_name=element_name,
                workplace_example=workplace_example,
                hot_technology=(
                    parse_onet_boolean(
                        row.get("HotTechnology")
                    )
                    or False
                ),
                in_demand=(
                    parse_onet_boolean(
                        row.get("In Demand")
                    )
                    or False
                ),
                onet_version=ONET_VERSION,
            )

            db.add(requirement)
            created += 1

    return created, skipped


def import_onet_requirements(
    db: Session,
) -> dict[str, int]:
    essential_file = (
        DATA_DIRECTORY / "essential_skills.csv"
    )

    transferable_file = (
        DATA_DIRECTORY / "transferable_skills.csv"
    )

    software_file = (
        DATA_DIRECTORY / "software_skills.csv"
    )

    required_files = [
        essential_file,
        transferable_file,
        software_file,
    ]

    for file_path in required_files:
        if not file_path.exists():
            raise FileNotFoundError(
                f"O*NET file not found: {file_path}"
            )

    career_map = load_career_map(db)

    if not career_map:
        raise RuntimeError(
            "No careers exist in the database. "
            "Import O*NET careers first."
        )

    try:
        # Makes the importer repeatable during development.
        db.execute(
            delete(CareerSkillRequirement).where(
                CareerSkillRequirement.onet_version
                == ONET_VERSION
            )
        )

        db.execute(
            delete(CareerSoftwareRequirement).where(
                CareerSoftwareRequirement.onet_version
                == ONET_VERSION
            )
        )

        essential_created, essential_skipped = (
            import_skill_file(
                db=db,
                file_path=essential_file,
                skill_type="ESSENTIAL",
                career_map=career_map,
            )
        )

        transferable_created, transferable_skipped = (
            import_skill_file(
                db=db,
                file_path=transferable_file,
                skill_type="TRANSFERABLE",
                career_map=career_map,
            )
        )

        software_created, software_skipped = (
            import_software_file(
                db=db,
                file_path=software_file,
                career_map=career_map,
            )
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "essential_created": essential_created,
        "essential_skipped": essential_skipped,
        "transferable_created": transferable_created,
        "transferable_skipped": transferable_skipped,
        "software_created": software_created,
        "software_skipped": software_skipped,
    }