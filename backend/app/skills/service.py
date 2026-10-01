from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.resumes.skill_extractor import ExtractedSkill
from backend.app.skills.models import (
    Skill,
    SkillEvidence,
    StudentSkill,
)


def get_or_create_skill(
    db: Session,
    canonical_name: str,
) -> Skill:
    statement = select(Skill).where(
        Skill.canonical_name == canonical_name
    )

    skill = db.scalar(statement)

    if skill is not None:
        return skill

    skill = Skill(
        canonical_name=canonical_name,
    )

    db.add(skill)
    db.flush()

    return skill


def get_or_create_student_skill(
    db: Session,
    user_id: UUID,
    skill_id: UUID,
) -> StudentSkill:
    statement = select(StudentSkill).where(
        StudentSkill.user_id == user_id,
        StudentSkill.skill_id == skill_id,
    )

    student_skill = db.scalar(statement)

    if student_skill is not None:
        return student_skill

    student_skill = StudentSkill(
        user_id=user_id,
        skill_id=skill_id,
    )

    db.add(student_skill)
    db.flush()

    return student_skill


def determine_resume_evidence_status(
    source_section: str,
    section_text: str,
) -> str:
    normalized_text = section_text.lower()

    planned_markers = (
        "planned stack",
        "planning ",
        "planned ",
        "in progress",
        "currently developing",
        "currently building",
    )

    if source_section == "projects":
        if any(
            marker in normalized_text
            for marker in planned_markers
        ):
            return "PLANNED"

    if source_section == "skills":
        return "CLAIMED"

    if source_section == "certifications":
        return "DETECTED"

    if source_section == "experience":
        return "DETECTED"

    if source_section == "projects":
        return "DETECTED"

    return "DETECTED"


def save_resume_skill_evidence(
    db: Session,
    user_id: UUID,
    resume_version_id: UUID,
    extracted_skills: list[ExtractedSkill],
    sections: dict[str, str],
) -> int:
    created_evidence_count = 0

    for extracted_skill in extracted_skills:
        skill = get_or_create_skill(
            db=db,
            canonical_name=extracted_skill.canonical_name,
        )

        student_skill = get_or_create_student_skill(
            db=db,
            user_id=user_id,
            skill_id=skill.id,
        )

        source_reference = str(resume_version_id)

        existing_statement = select(
            SkillEvidence
        ).where(
            SkillEvidence.student_skill_id
            == student_skill.id,
            SkillEvidence.source_type
            == "RESUME",
            SkillEvidence.source_reference
            == source_reference,
            SkillEvidence.source_section
            == extracted_skill.source_section,
        )

        existing_evidence = db.scalar(
            existing_statement
        )

        if existing_evidence is not None:
            continue

        section_text = sections.get(
            extracted_skill.source_section,
            "",
        )

        evidence_status = (
            determine_resume_evidence_status(
                source_section=(
                    extracted_skill.source_section
                ),
                section_text=section_text,
            )
        )

        evidence = SkillEvidence(
            student_skill_id=student_skill.id,
            source_type="RESUME",
            source_reference=source_reference,
            source_section=(
                extracted_skill.source_section
            ),
            evidence_text=(
                extracted_skill.matched_text
            ),
            evidence_status=evidence_status,
            evidence_strength=None,
        )

        db.add(evidence)

        created_evidence_count += 1

    return created_evidence_count
def get_student_skills_with_evidence(
    db: Session,
    user_id: UUID,
) -> list[StudentSkill]:
    statement = (
        select(StudentSkill)
        .where(
            StudentSkill.user_id == user_id
        )
        .order_by(
            StudentSkill.created_at.asc()
        )
    )

    return list(
        db.scalars(statement).all()
    )