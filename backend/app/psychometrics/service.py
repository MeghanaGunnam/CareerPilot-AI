import math
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.careers.models import (
    Career,
    CareerRiasecProfile,
)
from backend.app.psychometrics.models import (
    RiasecAnswer,
    RiasecAssessment,
    RiasecProfile,
)
from backend.app.psychometrics.questions import (
    QUESTION_BY_ID,
    RIASEC_QUESTIONS,
)
from backend.app.psychometrics.schemas import (
    CareerInterestMatchResponse,
    RiasecAnswerRequest,
    RiasecAssessmentResultResponse,
    RiasecProfileResponse,
    RiasecScoresResponse,
)


ASSESSMENT_VERSION = "careerpilot-v1"
SCORING_VERSION = "careerpilot-v1"

DIMENSION_FIELDS = {
    "R": "realistic",
    "I": "investigative",
    "A": "artistic",
    "S": "social",
    "E": "enterprising",
    "C": "conventional",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def validate_answers(
    answers: list[RiasecAnswerRequest],
) -> None:
    expected_ids = set(QUESTION_BY_ID.keys())

    submitted_ids = [
        answer.question_id
        for answer in answers
    ]

    submitted_id_set = set(submitted_ids)

    if len(answers) != len(RIASEC_QUESTIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Exactly {len(RIASEC_QUESTIONS)} "
                "answers are required."
            ),
        )

    if len(submitted_ids) != len(submitted_id_set):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate question IDs are not allowed.",
        )

    unknown_ids = submitted_id_set - expected_ids

    if unknown_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unknown question IDs: "
                + ", ".join(sorted(unknown_ids))
            ),
        )

    missing_ids = expected_ids - submitted_id_set

    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Missing question IDs: "
                + ", ".join(sorted(missing_ids))
            ),
        )


def calculate_scores(
    answers: list[RiasecAnswerRequest],
) -> dict[str, float]:
    totals = {
        "R": 0,
        "I": 0,
        "A": 0,
        "S": 0,
        "E": 0,
        "C": 0,
    }

    counts = {
        "R": 0,
        "I": 0,
        "A": 0,
        "S": 0,
        "E": 0,
        "C": 0,
    }

    for answer in answers:
        question = QUESTION_BY_ID[
            answer.question_id
        ]

        dimension = question["dimension"]

        totals[dimension] += answer.response_value
        counts[dimension] += 1

    scores: dict[str, float] = {}

    for dimension in DIMENSION_FIELDS:
        if counts[dimension] == 0:
            raise ValueError(
                f"No questions found for {dimension}."
            )

        # Each answer is 1–5.
        # Convert the dimension average to a 0–1 scale.
        average = (
            totals[dimension]
            / counts[dimension]
        )

        normalized = (
            average - 1.0
        ) / 4.0

        scores[dimension] = round(
            normalized,
            4,
        )

    return scores


def calculate_dominant_code(
    scores: dict[str, float],
) -> str:
    ordered = sorted(
        scores.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    )

    return "".join(
        dimension
        for dimension, _ in ordered[:3]
    )


def create_assessment(
    db: Session,
    user_id: UUID,
    answers: list[RiasecAnswerRequest],
) -> RiasecAssessmentResultResponse:
    validate_answers(answers)

    scores = calculate_scores(answers)

    dominant_code = calculate_dominant_code(
        scores
    )

    assessment = RiasecAssessment(
        user_id=user_id,
        assessment_version=ASSESSMENT_VERSION,
        status="COMPLETED",
        started_at=utc_now(),
        completed_at=utc_now(),
    )

    db.add(assessment)
    db.flush()

    for answer in answers:
        question = QUESTION_BY_ID[
            answer.question_id
        ]

        answer_record = RiasecAnswer(
            assessment_id=assessment.id,
            question_id=answer.question_id,
            dimension=question["dimension"],
            response_value=answer.response_value,
        )

        db.add(answer_record)

    profile = RiasecProfile(
        assessment_id=assessment.id,
        user_id=user_id,
        realistic=scores["R"],
        investigative=scores["I"],
        artistic=scores["A"],
        social=scores["S"],
        enterprising=scores["E"],
        conventional=scores["C"],
        dominant_code=dominant_code,
        scoring_version=SCORING_VERSION,
    )

    db.add(profile)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(assessment)
    db.refresh(profile)

    return build_assessment_response(
        assessment,
        profile,
    )


def build_scores_response(
    profile: RiasecProfile,
) -> RiasecScoresResponse:
    return RiasecScoresResponse(
        realistic=profile.realistic,
        investigative=profile.investigative,
        artistic=profile.artistic,
        social=profile.social,
        enterprising=profile.enterprising,
        conventional=profile.conventional,
    )


def build_profile_response(
    profile: RiasecProfile,
) -> RiasecProfileResponse:
    return RiasecProfileResponse(
        id=profile.id,
        assessment_id=profile.assessment_id,
        scores=build_scores_response(profile),
        dominant_code=profile.dominant_code,
        scoring_version=profile.scoring_version,
        created_at=profile.created_at,
    )


def build_assessment_response(
    assessment: RiasecAssessment,
    profile: RiasecProfile,
) -> RiasecAssessmentResultResponse:
    if assessment.completed_at is None:
        raise ValueError(
            "Completed assessment has no completion time."
        )

    return RiasecAssessmentResultResponse(
        assessment_id=assessment.id,
        assessment_version=(
            assessment.assessment_version
        ),
        status=assessment.status,
        completed_at=assessment.completed_at,
        profile=build_profile_response(profile),
    )


def get_latest_assessment(
    db: Session,
    user_id: UUID,
) -> RiasecAssessmentResultResponse | None:
    statement = (
        select(RiasecAssessment)
        .options(
            selectinload(
                RiasecAssessment.profile
            )
        )
        .where(
            RiasecAssessment.user_id == user_id,
            RiasecAssessment.status == "COMPLETED",
        )
        .order_by(
            RiasecAssessment.completed_at.desc()
        )
        .limit(1)
    )

    assessment = db.scalar(statement)

    if assessment is None:
        return None

    if assessment.profile is None:
        return None

    return build_assessment_response(
        assessment,
        assessment.profile,
    )


def get_latest_profile_model(
    db: Session,
    user_id: UUID,
) -> RiasecProfile | None:
    statement = (
        select(RiasecProfile)
        .join(
            RiasecAssessment,
            RiasecProfile.assessment_id
            == RiasecAssessment.id,
        )
        .where(
            RiasecProfile.user_id == user_id,
            RiasecAssessment.status == "COMPLETED",
        )
        .order_by(
            RiasecAssessment.completed_at.desc()
        )
        .limit(1)
    )

    return db.scalar(statement)


def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    if len(vector_a) != len(vector_b):
        raise ValueError(
            "Vectors must have the same length."
        )

    dot_product = sum(
        a * b
        for a, b in zip(
            vector_a,
            vector_b,
            strict=True,
        )
    )

    magnitude_a = math.sqrt(
        sum(
            value * value
            for value in vector_a
        )
    )

    magnitude_b = math.sqrt(
        sum(
            value * value
            for value in vector_b
        )
    )

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    similarity = (
        dot_product
        / (magnitude_a * magnitude_b)
    )

    return max(
        0.0,
        min(1.0, similarity),
    )


def career_profile_vector(
    profile: CareerRiasecProfile,
) -> list[float] | None:
    values = [
        profile.realistic,
        profile.investigative,
        profile.artistic,
        profile.social,
        profile.enterprising,
        profile.conventional,
    ]

    if any(
        value is None
        for value in values
    ):
        return None

    return [
        float(value)
        for value in values
        if value is not None
    ]


def student_profile_vector(
    profile: RiasecProfile,
) -> list[float]:
    return [
        profile.realistic,
        profile.investigative,
        profile.artistic,
        profile.social,
        profile.enterprising,
        profile.conventional,
    ]


def get_interest_matches(
    db: Session,
    user_id: UUID,
    limit: int = 10,
) -> list[CareerInterestMatchResponse]:
    student_profile = get_latest_profile_model(
        db,
        user_id,
    )

    if student_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Complete the RIASEC assessment "
                "before requesting career matches."
            ),
        )

    student_vector = student_profile_vector(
        student_profile
    )

    statement = (
        select(Career)
        .options(
            selectinload(
                Career.riasec_profile
            )
        )
        .where(
            Career.riasec_profile.has()
        )
    )

    careers = db.scalars(
        statement
    ).all()

    matches: list[
        CareerInterestMatchResponse
    ] = []

    for career in careers:
        career_profile = career.riasec_profile

        if career_profile is None:
            continue

        career_vector = career_profile_vector(
            career_profile
        )

        if career_vector is None:
            continue

        similarity = cosine_similarity(
            student_vector,
            career_vector,
        )

        career_scores = {
            "R": float(
                career_profile.realistic
            ),
            "I": float(
                career_profile.investigative
            ),
            "A": float(
                career_profile.artistic
            ),
            "S": float(
                career_profile.social
            ),
            "E": float(
                career_profile.enterprising
            ),
            "C": float(
                career_profile.conventional
            ),
        }

        career_dominant_code = (
            calculate_dominant_code(
                career_scores
            )
        )

        matches.append(
            CareerInterestMatchResponse(
                career_id=career.id,
                onet_soc_code=(
                    career.onet_soc_code
                ),
                title=career.title,
                description=career.description,
                job_zone=career.job_zone,
                interest_alignment=round(
                    similarity,
                    4,
                ),
                interest_alignment_percent=round(
                    similarity * 100,
                    2,
                ),
                career_riasec=(
                    RiasecScoresResponse(
                        realistic=career_scores["R"],
                        investigative=career_scores["I"],
                        artistic=career_scores["A"],
                        social=career_scores["S"],
                        enterprising=career_scores["E"],
                        conventional=career_scores["C"],
                    )
                ),
                dominant_code=(
                    career_dominant_code
                ),
            )
        )

    matches.sort(
        key=lambda match: (
            -match.interest_alignment,
            match.title,
        )
    )

    return matches[:limit]