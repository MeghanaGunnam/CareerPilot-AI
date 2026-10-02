import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.career_twin.models import (
    CareerTwin,
    CareerTwinEvent,
    CareerTwinSnapshot,
)
from backend.app.psychometrics.models import RiasecProfile
from backend.app.skills.models import (
    Skill,
    SkillEvidence,
    StudentSkill,
)
from backend.app.students.models import (
    CareerGoal,
    Certification,
    Education,
    Experience,
    Project,
    StudentProfile,
)


SCHEMA_VERSION = "1.0"


def iso_or_none(value: datetime | None) -> str | None:
    if value is None:
        return None

    return value.isoformat()


def get_or_create_career_twin(
    db: Session,
    user_id: uuid.UUID,
) -> CareerTwin:
    twin = db.scalar(
        select(CareerTwin).where(
            CareerTwin.user_id == user_id
        )
    )

    if twin is not None:
        return twin

    twin = CareerTwin(
        user_id=user_id,
        current_version=0,
    )

    db.add(twin)
    db.flush()

    return twin


def build_profile_state(
    db: Session,
    user_id: uuid.UUID,
) -> dict | None:
    profile = db.scalar(
        select(StudentProfile).where(
            StudentProfile.user_id == user_id
        )
    )

    if profile is None:
        return None

    # Phone is deliberately excluded from the analytical twin.
    return {
        "full_name": profile.full_name,
        "city": profile.city,
        "state": profile.state,
        "country": profile.country,
        "headline": profile.headline,
        "bio": profile.bio,
    }


def build_education_state(
    db: Session,
    user_id: uuid.UUID,
) -> list[dict]:
    records = list(
        db.scalars(
            select(Education)
            .where(Education.user_id == user_id)
            .order_by(Education.created_at.asc())
        ).all()
    )

    return [
        {
            "id": str(item.id),
            "institution_name": item.institution_name,
            "degree": item.degree,
            "field_of_study": item.field_of_study,
            "start_year": item.start_year,
            "end_year": item.end_year,
            "grade": item.grade,
        }
        for item in records
    ]


def build_experience_state(
    db: Session,
    user_id: uuid.UUID,
) -> list[dict]:
    records = list(
        db.scalars(
            select(Experience)
            .where(Experience.user_id == user_id)
            .order_by(Experience.created_at.asc())
        ).all()
    )

    return [
        {
            "id": str(item.id),
            "company_name": item.company_name,
            "job_title": item.job_title,
            "employment_type": item.employment_type,
            "location": item.location,
            "start_date": iso_or_none(item.start_date),
            "end_date": iso_or_none(item.end_date),
            "is_current": item.is_current,
            "description": item.description,
        }
        for item in records
    ]


def build_project_state(
    db: Session,
    user_id: uuid.UUID,
) -> list[dict]:
    records = list(
        db.scalars(
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.created_at.asc())
        ).all()
    )

    return [
        {
            "id": str(item.id),
            "title": item.title,
            "description": item.description,
            "role": item.role,
            "technologies": item.technologies,
            "start_date": iso_or_none(item.start_date),
            "end_date": iso_or_none(item.end_date),
            "is_ongoing": item.is_ongoing,
        }
        for item in records
    ]


def build_certification_state(
    db: Session,
    user_id: uuid.UUID,
) -> list[dict]:
    records = list(
        db.scalars(
            select(Certification)
            .where(Certification.user_id == user_id)
            .order_by(Certification.created_at.asc())
        ).all()
    )

    return [
        {
            "id": str(item.id),
            "name": item.name,
            "issuing_organization": (
                item.issuing_organization
            ),
            "issue_date": iso_or_none(item.issue_date),
            "expiration_date": iso_or_none(
                item.expiration_date
            ),
            "description": item.description,
        }
        for item in records
    ]


def build_goal_state(
    db: Session,
    user_id: uuid.UUID,
) -> list[dict]:
    goals = list(
        db.scalars(
            select(CareerGoal)
            .where(
                CareerGoal.user_id == user_id,
                CareerGoal.is_active.is_(True),
            )
            .order_by(
                CareerGoal.is_primary.desc(),
                CareerGoal.priority.asc(),
                CareerGoal.created_at.asc(),
            )
        ).all()
    )

    return [
        {
            "id": str(goal.id),
            "target_role": goal.target_role,
            "onet_soc_code": goal.onet_soc_code,
            "target_industry": goal.target_industry,
            "target_location": goal.target_location,
            "employment_type": goal.employment_type,
            "target_timeline_months": (
                goal.target_timeline_months
            ),
            "priority": goal.priority,
            "is_active": goal.is_active,
            "is_primary": goal.is_primary,
        }
        for goal in goals
    ]


def build_riasec_state(
    db: Session,
    user_id: uuid.UUID,
) -> dict | None:
    profile = db.scalar(
        select(RiasecProfile)
        .where(RiasecProfile.user_id == user_id)
        .order_by(RiasecProfile.created_at.desc())
    )

    if profile is None:
        return None

    return {
        "assessment_id": str(profile.assessment_id),
        "realistic": profile.realistic,
        "investigative": profile.investigative,
        "artistic": profile.artistic,
        "social": profile.social,
        "enterprising": profile.enterprising,
        "conventional": profile.conventional,
        "dominant_code": profile.dominant_code,
        "scoring_version": profile.scoring_version,
        "created_at": profile.created_at.isoformat(),
    }


def build_skill_state(
    db: Session,
    user_id: uuid.UUID,
) -> list[dict]:
    student_skills = list(
        db.scalars(
            select(StudentSkill)
            .where(StudentSkill.user_id == user_id)
            .order_by(StudentSkill.created_at.asc())
        ).all()
    )

    result: list[dict] = []

    for student_skill in student_skills:
        skill = db.get(
            Skill,
            student_skill.skill_id,
        )

        if skill is None:
            continue

        evidence_records = list(
            db.scalars(
                select(SkillEvidence)
                .where(
                    SkillEvidence.student_skill_id
                    == student_skill.id
                )
                .order_by(
                    SkillEvidence.created_at.asc()
                )
            ).all()
        )

        evidence = [
            {
                "id": str(item.id),
                "source_type": item.source_type,
                "source_reference": (
                    item.source_reference
                ),
                "source_section": item.source_section,
                "evidence_text": item.evidence_text,
                "evidence_status": (
                    item.evidence_status
                ),
                "evidence_strength": (
                    item.evidence_strength
                ),
                "observed_at": iso_or_none(
                    item.observed_at
                ),
            }
            for item in evidence_records
        ]

        result.append(
            {
                "student_skill_id": str(
                    student_skill.id
                ),
                "skill_id": str(skill.id),
                "name": skill.canonical_name,
                "category": skill.category,
                "claimed_proficiency": (
                    student_skill.claimed_proficiency
                ),
                "estimated_proficiency": (
                    student_skill.estimated_proficiency
                ),
                "evidence_confidence": (
                    student_skill.evidence_confidence
                ),
                "freshness_score": (
                    student_skill.freshness_score
                ),
                "last_verified_at": iso_or_none(
                    student_skill.last_verified_at
                ),
                "evidence": evidence,
            }
        )

    result.sort(
        key=lambda item: item["name"].lower()
    )

    return result


def build_current_state(
    db: Session,
    user_id: uuid.UUID,
) -> dict:
    return {
        "profile": build_profile_state(
            db,
            user_id,
        ),
        "education": build_education_state(
            db,
            user_id,
        ),
        "experience": build_experience_state(
            db,
            user_id,
        ),
        "projects": build_project_state(
            db,
            user_id,
        ),
        "certifications": build_certification_state(
            db,
            user_id,
        ),
        "career_goals": build_goal_state(
            db,
            user_id,
        ),
        "riasec": build_riasec_state(
            db,
            user_id,
        ),
        "skills": build_skill_state(
            db,
            user_id,
        ),
    }


def create_career_twin_snapshot(
    db: Session,
    user_id: uuid.UUID,
    trigger_type: str = "MANUAL_REFRESH",
    source_type: str = "SYSTEM",
    source_reference: str | None = None,
) -> CareerTwinSnapshot:
    twin = get_or_create_career_twin(
        db=db,
        user_id=user_id,
    )

    state_data = build_current_state(
        db=db,
        user_id=user_id,
    )

    next_version = twin.current_version + 1

    snapshot = CareerTwinSnapshot(
        career_twin_id=twin.id,
        version=next_version,
        trigger_type=trigger_type,
        state_data=state_data,
        schema_version=SCHEMA_VERSION,
    )

    event = CareerTwinEvent(
        career_twin_id=twin.id,
        event_type="SNAPSHOT_CREATED",
        source_type=source_type,
        source_reference=source_reference,
        event_data={
            "snapshot_version": next_version,
            "trigger_type": trigger_type,
        },
    )

    db.add(snapshot)
    db.add(event)

    twin.current_version = next_version
    twin.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(snapshot)

    return snapshot


def get_career_twin(
    db: Session,
    user_id: uuid.UUID,
) -> CareerTwin | None:
    return db.scalar(
        select(CareerTwin).where(
            CareerTwin.user_id == user_id
        )
    )


def get_latest_snapshot(
    db: Session,
    career_twin_id: uuid.UUID,
) -> CareerTwinSnapshot | None:
    return db.scalar(
        select(CareerTwinSnapshot)
        .where(
            CareerTwinSnapshot.career_twin_id
            == career_twin_id
        )
        .order_by(
            CareerTwinSnapshot.version.desc()
        )
    )


def get_snapshot_history(
    db: Session,
    career_twin_id: uuid.UUID,
) -> list[CareerTwinSnapshot]:
    return list(
        db.scalars(
            select(CareerTwinSnapshot)
            .where(
                CareerTwinSnapshot.career_twin_id
                == career_twin_id
            )
            .order_by(
                CareerTwinSnapshot.version.desc()
            )
        ).all()
    )