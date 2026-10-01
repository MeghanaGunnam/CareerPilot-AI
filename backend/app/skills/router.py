from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.core.database import get_db
from backend.app.skills.models import (
    Skill,
    SkillEvidence,
)
from backend.app.skills.schemas import (
    SkillEvidenceResponse,
    StudentSkillResponse,
    StudentSkillsSummaryResponse,
)
from backend.app.skills.service import (
    get_student_skills_with_evidence,
)


router = APIRouter(
    prefix="/api/v1/skills",
    tags=["Skills"],
)


@router.get(
    "/me",
    response_model=StudentSkillsSummaryResponse,
)
def get_my_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student_skills = (
        get_student_skills_with_evidence(
            db=db,
            user_id=current_user.id,
        )
    )

    response_skills: list[
        StudentSkillResponse
    ] = []

    total_evidence = 0

    for student_skill in student_skills:
        skill = db.scalar(
            select(Skill).where(
                Skill.id == student_skill.skill_id
            )
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

        total_evidence += len(evidence_records)

        response_skills.append(
            StudentSkillResponse(
                id=student_skill.id,
                skill_id=skill.id,
                canonical_name=skill.canonical_name,
                category=skill.category,
                claimed_proficiency=(
                    student_skill.claimed_proficiency
                ),
                estimated_proficiency=(
                    student_skill.estimated_proficiency
                ),
                evidence_confidence=(
                    student_skill.evidence_confidence
                ),
                freshness_score=(
                    student_skill.freshness_score
                ),
                last_verified_at=(
                    student_skill.last_verified_at
                ),
                evidence=[
                    SkillEvidenceResponse.model_validate(
                        evidence
                    )
                    for evidence in evidence_records
                ],
            )
        )

    response_skills.sort(
        key=lambda item: item.canonical_name.lower()
    )

    return StudentSkillsSummaryResponse(
        total_skills=len(response_skills),
        total_evidence=total_evidence,
        skills=response_skills,
    )