from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.core.database import get_db
from backend.app.students.schemas import (
    CareerGoalCreate,
    CareerGoalResponse,
    CareerGoalUpdate,
    CertificationCreate,
    CertificationResponse,
    CertificationUpdate,
    EducationCreate,
    EducationResponse,
    EducationUpdate,
    ExperienceCreate,
    ExperienceResponse,
    ExperienceUpdate,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    StudentProfileCreate,
    StudentProfileResponse,
    StudentProfileUpdate,
)
from backend.app.students.service import (
    create_career_goal,
    delete_career_goal,
    get_user_career_goal,
    get_user_career_goals,
    update_career_goal,
    create_certification,
    delete_certification,
    get_user_certification,
    get_user_certifications,
    update_certification,
    create_education,
    create_experience,
    create_project,
    create_student_profile,
    delete_education,
    delete_experience,
    delete_project,
    get_profile_by_user_id,
    get_user_education,
    get_user_educations,
    get_user_experience,
    get_user_experiences,
    get_user_project,
    get_user_projects,
    update_education,
    update_experience,
    update_project,
    update_student_profile,
)


router = APIRouter(
    prefix="/api/v1/students",
    tags=["Students"],
)


# =========================================================
# Student Profile
# =========================================================

@router.post(
    "/profile",
    response_model=StudentProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_profile(
    data: StudentProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentProfileResponse:
    existing_profile = get_profile_by_user_id(
        db=db,
        user_id=current_user.id,
    )

    if existing_profile is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student profile already exists.",
        )

    return create_student_profile(
        db=db,
        user_id=current_user.id,
        data=data,
    )


@router.get(
    "/profile",
    response_model=StudentProfileResponse,
    status_code=status.HTTP_200_OK,
)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentProfileResponse:
    profile = get_profile_by_user_id(
        db=db,
        user_id=current_user.id,
    )

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found.",
        )

    return profile


@router.patch(
    "/profile",
    response_model=StudentProfileResponse,
    status_code=status.HTTP_200_OK,
)
def update_profile(
    data: StudentProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentProfileResponse:
    profile = get_profile_by_user_id(
        db=db,
        user_id=current_user.id,
    )

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found.",
        )

    return update_student_profile(
        db=db,
        profile=profile,
        data=data,
    )


# =========================================================
# Education
# =========================================================

@router.post(
    "/education",
    response_model=EducationResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_education(
    data: EducationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EducationResponse:
    return create_education(
        db=db,
        user_id=current_user.id,
        data=data,
    )


@router.get(
    "/education",
    response_model=list[EducationResponse],
    status_code=status.HTTP_200_OK,
)
def list_education(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EducationResponse]:
    return get_user_educations(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/education/{education_id}",
    response_model=EducationResponse,
    status_code=status.HTTP_200_OK,
)
def get_education(
    education_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EducationResponse:
    education = get_user_education(
        db=db,
        user_id=current_user.id,
        education_id=education_id,
    )

    if education is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Education record not found.",
        )

    return education


@router.patch(
    "/education/{education_id}",
    response_model=EducationResponse,
    status_code=status.HTTP_200_OK,
)
def edit_education(
    education_id: UUID,
    data: EducationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EducationResponse:
    education = get_user_education(
        db=db,
        user_id=current_user.id,
        education_id=education_id,
    )

    if education is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Education record not found.",
        )

    return update_education(
        db=db,
        education=education,
        data=data,
    )


@router.delete(
    "/education/{education_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_education(
    education_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    education = get_user_education(
        db=db,
        user_id=current_user.id,
        education_id=education_id,
    )

    if education is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Education record not found.",
        )

    delete_education(
        db=db,
        education=education,
    )


# =========================================================
# Experience
# =========================================================

@router.post(
    "/experiences",
    response_model=ExperienceResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_experience(
    data: ExperienceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExperienceResponse:
    return create_experience(
        db=db,
        user_id=current_user.id,
        data=data,
    )


@router.get(
    "/experiences",
    response_model=list[ExperienceResponse],
    status_code=status.HTTP_200_OK,
)
def list_experiences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ExperienceResponse]:
    return get_user_experiences(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/experiences/{experience_id}",
    response_model=ExperienceResponse,
    status_code=status.HTTP_200_OK,
)
def get_experience(
    experience_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExperienceResponse:
    experience = get_user_experience(
        db=db,
        user_id=current_user.id,
        experience_id=experience_id,
    )

    if experience is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience record not found.",
        )

    return experience


@router.patch(
    "/experiences/{experience_id}",
    response_model=ExperienceResponse,
    status_code=status.HTTP_200_OK,
)
def edit_experience(
    experience_id: UUID,
    data: ExperienceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExperienceResponse:
    experience = get_user_experience(
        db=db,
        user_id=current_user.id,
        experience_id=experience_id,
    )

    if experience is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience record not found.",
        )

    return update_experience(
        db=db,
        experience=experience,
        data=data,
    )


@router.delete(
    "/experiences/{experience_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_experience(
    experience_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    experience = get_user_experience(
        db=db,
        user_id=current_user.id,
        experience_id=experience_id,
    )

    if experience is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience record not found.",
        )

    delete_experience(
        db=db,
        experience=experience,
    )


# =========================================================
# Projects
# =========================================================

@router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    return create_project(
        db=db,
        user_id=current_user.id,
        data=data,
    )


@router.get(
    "/projects",
    response_model=list[ProjectResponse],
    status_code=status.HTTP_200_OK,
)
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectResponse]:
    return get_user_projects(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    project = get_user_project(
        db=db,
        user_id=current_user.id,
        project_id=project_id,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    return project


@router.patch(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
)
def edit_project(
    project_id: UUID,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    project = get_user_project(
        db=db,
        user_id=current_user.id,
        project_id=project_id,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    try:
        return update_project(
            db=db,
            project=project,
            data=data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    project = get_user_project(
        db=db,
        user_id=current_user.id,
        project_id=project_id,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    delete_project(
        db=db,
        project=project,
    )
# =========================================================
# Certifications
# =========================================================


@router.post(
    "/certifications",
    response_model=CertificationResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_certification(
    data: CertificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CertificationResponse:
    return create_certification(
        db=db,
        user_id=current_user.id,
        data=data,
    )


@router.get(
    "/certifications",
    response_model=list[CertificationResponse],
    status_code=status.HTTP_200_OK,
)
def list_certifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CertificationResponse]:
    return get_user_certifications(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/certifications/{certification_id}",
    response_model=CertificationResponse,
    status_code=status.HTTP_200_OK,
)
def get_certification(
    certification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CertificationResponse:
    certification = get_user_certification(
        db=db,
        user_id=current_user.id,
        certification_id=certification_id,
    )

    if certification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found.",
        )

    return certification


@router.patch(
    "/certifications/{certification_id}",
    response_model=CertificationResponse,
    status_code=status.HTTP_200_OK,
)
def edit_certification(
    certification_id: UUID,
    data: CertificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CertificationResponse:
    certification = get_user_certification(
        db=db,
        user_id=current_user.id,
        certification_id=certification_id,
    )

    if certification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found.",
        )

    try:
        return update_certification(
            db=db,
            certification=certification,
            data=data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.delete(
    "/certifications/{certification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_certification(
    certification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    certification = get_user_certification(
        db=db,
        user_id=current_user.id,
        certification_id=certification_id,
    )

    if certification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found.",
        )

    delete_certification(
        db=db,
        certification=certification,
    )
# =========================================================
# Career Goals
# =========================================================


@router.post(
    "/career-goals",
    response_model=CareerGoalResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_career_goal_endpoint(
    data: CareerGoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_career_goal(
        db=db,
        user_id=current_user.id,
        data=data,
    )


@router.get(
    "/career-goals",
    response_model=list[CareerGoalResponse],
)
def list_career_goals_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_user_career_goals(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/career-goals/{career_goal_id}",
    response_model=CareerGoalResponse,
)
def get_career_goal_endpoint(
    career_goal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    career_goal = get_user_career_goal(
        db=db,
        user_id=current_user.id,
        career_goal_id=career_goal_id,
    )

    if career_goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career goal not found.",
        )

    return career_goal


@router.patch(
    "/career-goals/{career_goal_id}",
    response_model=CareerGoalResponse,
)
def update_career_goal_endpoint(
    career_goal_id: UUID,
    data: CareerGoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    career_goal = get_user_career_goal(
        db=db,
        user_id=current_user.id,
        career_goal_id=career_goal_id,
    )

    if career_goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career goal not found.",
        )

    return update_career_goal(
        db=db,
        career_goal=career_goal,
        data=data,
    )


@router.delete(
    "/career-goals/{career_goal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_career_goal_endpoint(
    career_goal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    career_goal = get_user_career_goal(
        db=db,
        user_id=current_user.id,
        career_goal_id=career_goal_id,
    )

    if career_goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career goal not found.",
        )

    delete_career_goal(
        db=db,
        career_goal=career_goal,
    )