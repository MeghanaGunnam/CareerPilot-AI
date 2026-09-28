import csv
from pathlib import Path

from sqlalchemy import select

from backend.app.careers.models import Career, CareerRiasecProfile
from backend.app.core.database import SessionLocal


PROJECT_ROOT = Path(__file__).resolve().parents[3]

ONET_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "onet"
    / "31.0"
    / "db_31_0_csv"
)

OCCUPATION_FILE = ONET_DIRECTORY / "occupation_data.csv"
JOB_ZONE_FILE = ONET_DIRECTORY / "job_zones.csv"
INTEREST_FILE = ONET_DIRECTORY / "career_interest_types.csv"

ONET_VERSION = "31.0"

RIASEC_FIELDS = {
    "Realistic": "realistic",
    "Investigative": "investigative",
    "Artistic": "artistic",
    "Social": "social",
    "Enterprising": "enterprising",
    "Conventional": "conventional",
}


def validate_files() -> None:
    required_files = [
        OCCUPATION_FILE,
        JOB_ZONE_FILE,
        INTEREST_FILE,
    ]

    missing_files = [
        file_path
        for file_path in required_files
        if not file_path.exists()
    ]

    if missing_files:
        missing = "\n".join(
            str(file_path)
            for file_path in missing_files
        )

        raise FileNotFoundError(
            f"Missing O*NET files:\n{missing}"
        )


def load_job_zones() -> dict[str, int]:
    job_zones: dict[str, int] = {}

    with JOB_ZONE_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            onet_code = row["O*NET-SOC Code"].strip()
            job_zone_value = row["Job Zone"].strip()

            if not onet_code or not job_zone_value:
                continue

            try:
                job_zones[onet_code] = int(job_zone_value)
            except ValueError:
                continue

    return job_zones


def load_riasec_profiles() -> dict[str, dict[str, float]]:
    profiles: dict[str, dict[str, float]] = {}

    with INTEREST_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            # We only want the six numerical
            # Occupational Interest dimensions.
            if row["Scale ID"].strip() != "OI":
                continue

            element_name = row["Element Name"].strip()

            if element_name not in RIASEC_FIELDS:
                continue

            onet_code = row["O*NET-SOC Code"].strip()
            value_text = row["Data Value"].strip()

            if not onet_code or not value_text:
                continue

            try:
                value = float(value_text)
            except ValueError:
                continue

            if onet_code not in profiles:
                profiles[onet_code] = {}

            field_name = RIASEC_FIELDS[element_name]
            profiles[onet_code][field_name] = value

    return profiles


def load_occupations() -> list[dict]:
    occupations: list[dict] = []

    with OCCUPATION_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            onet_code = row["O*NET-SOC Code"].strip()
            title = row["Title"].strip()
            description = row["Description"].strip()

            if not onet_code or not title:
                continue

            occupations.append(
                {
                    "onet_soc_code": onet_code,
                    "title": title,
                    "description": description or None,
                }
            )

    return occupations


def import_onet_data() -> None:
    validate_files()

    print("Loading O*NET 31.0 files...")

    occupations = load_occupations()
    job_zones = load_job_zones()
    riasec_profiles = load_riasec_profiles()

    print(
        f"Occupations loaded from CSV: "
        f"{len(occupations)}"
    )
    print(
        f"Job Zones loaded from CSV: "
        f"{len(job_zones)}"
    )
    print(
        f"RIASEC profiles found: "
        f"{len(riasec_profiles)}"
    )

    created_careers = 0
    updated_careers = 0

    created_profiles = 0
    updated_profiles = 0
    incomplete_profiles = 0

    db = SessionLocal()

    try:
        for occupation in occupations:
            onet_code = occupation["onet_soc_code"]

            career = db.scalar(
                select(Career).where(
                    Career.onet_soc_code == onet_code
                )
            )

            job_zone = job_zones.get(onet_code)

            if career is None:
                career = Career(
                    onet_soc_code=onet_code,
                    title=occupation["title"],
                    description=occupation["description"],
                    job_zone=job_zone,
                    onet_version=ONET_VERSION,
                )

                db.add(career)
                db.flush()

                created_careers += 1

            else:
                career.title = occupation["title"]
                career.description = occupation["description"]
                career.job_zone = job_zone
                career.onet_version = ONET_VERSION

                updated_careers += 1

            profile_data = riasec_profiles.get(onet_code)

            if profile_data is None:
                continue

            # A usable RIASEC vector requires all six dimensions.
            if not all(
                field_name in profile_data
                for field_name in RIASEC_FIELDS.values()
            ):
                incomplete_profiles += 1
                continue

            existing_profile = db.scalar(
                select(CareerRiasecProfile).where(
                    CareerRiasecProfile.career_id
                    == career.id
                )
            )

            if existing_profile is None:
                profile = CareerRiasecProfile(
                    career_id=career.id,
                    realistic=profile_data["realistic"],
                    investigative=profile_data[
                        "investigative"
                    ],
                    artistic=profile_data["artistic"],
                    social=profile_data["social"],
                    enterprising=profile_data[
                        "enterprising"
                    ],
                    conventional=profile_data[
                        "conventional"
                    ],
                    source="O*NET",
                    onet_version=ONET_VERSION,
                )

                db.add(profile)
                created_profiles += 1

            else:
                existing_profile.realistic = (
                    profile_data["realistic"]
                )
                existing_profile.investigative = (
                    profile_data["investigative"]
                )
                existing_profile.artistic = (
                    profile_data["artistic"]
                )
                existing_profile.social = (
                    profile_data["social"]
                )
                existing_profile.enterprising = (
                    profile_data["enterprising"]
                )
                existing_profile.conventional = (
                    profile_data["conventional"]
                )
                existing_profile.source = "O*NET"
                existing_profile.onet_version = ONET_VERSION

                updated_profiles += 1

        db.commit()

        print()
        print("O*NET import completed successfully.")
        print(
            f"Careers created: {created_careers}"
        )
        print(
            f"Careers updated: {updated_careers}"
        )
        print(
            f"RIASEC profiles created: "
            f"{created_profiles}"
        )
        print(
            f"RIASEC profiles updated: "
            f"{updated_profiles}"
        )
        print(
            f"Incomplete RIASEC profiles skipped: "
            f"{incomplete_profiles}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    import_onet_data()