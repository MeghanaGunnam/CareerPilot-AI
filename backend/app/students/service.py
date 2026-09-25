
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.students.models import (
    CareerGoal,
    Certification,
    Education,
    Experience,
    Project,
    StudentProfile,
)
from backend.app.students.schemas import (
    CareerGoalCreate,
    CareerGoalUpdate,
    CertificationCreate,
    CertificationUpdate,
    EducationCreate,
    EducationUpdate,
    ExperienceCreate,
    ExperienceUpdate,
    ProjectCreate,
    ProjectUpdate,
    StudentProfileCreate,
    StudentProfileUpdate,
)


# =========================================================
# Student Profile
# =========================================================

def get_profile_by_user_id(
    db: Session,
    user_id: uuid.UUID,
) -> StudentProfile | None:
    statement = select(StudentProfile).where(
        StudentProfile.user_id == user_id
    )

    return db.scalar(statement)


def create_student_profile(
    db: Session,
    user_id: uuid.UUID,
    data: StudentProfileCreate,
) -> StudentProfile:
    profile = StudentProfile(
        user_id=user_id,
        **data.model_dump(),
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile


def update_student_profile(
    db: Session,
    profile: StudentProfile,
    data: StudentProfileUpdate,
) -> StudentProfile:
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return profile


# =========================================================
# Education
# =========================================================

def create_education(
    db: Session,
    user_id: uuid.UUID,
    data: EducationCreate,
) -> Education:
    education = Education(
        user_id=user_id,
        **data.model_dump(),
    )

    db.add(education)
    db.commit()
    db.refresh(education)

    return education


def get_user_educations(
    db: Session,
    user_id: uuid.UUID,
) -> list[Education]:
    statement = (
        select(Education)
        .where(Education.user_id == user_id)
        .order_by(
            Education.end_year.desc().nullslast(),
            Education.start_year.desc().nullslast(),
        )
    )

    return list(db.scalars(statement).all())


def get_user_education(
    db: Session,
    user_id: uuid.UUID,
    education_id: uuid.UUID,
) -> Education | None:
    statement = select(Education).where(
        Education.id == education_id,
        Education.user_id == user_id,
    )

    return db.scalar(statement)


def update_education(
    db: Session,
    education: Education,
    data: EducationUpdate,
) -> Education:
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(education, field, value)

    db.commit()
    db.refresh(education)

    return education


def delete_education(
    db: Session,
    education: Education,
) -> None:
    db.delete(education)
    db.commit()


# =========================================================
# Experience
# =========================================================

def create_experience(
    db: Session,
    user_id: uuid.UUID,
    data: ExperienceCreate,
) -> Experience:
    experience = Experience(
        user_id=user_id,
        **data.model_dump(),
    )

    db.add(experience)
    db.commit()
    db.refresh(experience)

    return experience


def get_user_experiences(
    db: Session,
    user_id: uuid.UUID,
) -> list[Experience]:
    statement = (
        select(Experience)
        .where(Experience.user_id == user_id)
        .order_by(
            Experience.is_current.desc(),
            Experience.start_date.desc().nullslast(),
        )
    )

    return list(db.scalars(statement).all())


def get_user_experience(
    db: Session,
    user_id: uuid.UUID,
    experience_id: uuid.UUID,
) -> Experience | None:
    statement = select(Experience).where(
        Experience.id == experience_id,
        Experience.user_id == user_id,
    )

    return db.scalar(statement)


def update_experience(
    db: Session,
    experience: Experience,
    data: ExperienceUpdate,
) -> Experience:
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(experience, field, value)

    db.commit()
    db.refresh(experience)

    return experience


def delete_experience(
    db: Session,
    experience: Experience,
) -> None:
    db.delete(experience)
    db.commit()
# =========================================================
# Projects
# =========================================================

def create_project(
    db: Session,
    user_id: uuid.UUID,
    data: ProjectCreate,
) -> Project:
    project = Project(
        user_id=user_id,
        **data.model_dump(),
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


def get_user_projects(
    db: Session,
    user_id: uuid.UUID,
) -> list[Project]:
    statement = (
        select(Project)
        .where(Project.user_id == user_id)
        .order_by(
            Project.is_ongoing.desc(),
            Project.start_date.desc().nullslast(),
        )
    )

    return list(db.scalars(statement).all())


def get_user_project(
    db: Session,
    user_id: uuid.UUID,
    project_id: uuid.UUID,
) -> Project | None:
    statement = select(Project).where(
        Project.id == project_id,
        Project.user_id == user_id,
    )

    return db.scalar(statement)


def update_project(
    db: Session,
    project: Project,
    data: ProjectUpdate,
) -> Project:
    update_data = data.model_dump(exclude_unset=True)

    new_start_date = update_data.get(
        "start_date",
        project.start_date,
    )
    new_end_date = update_data.get(
        "end_date",
        project.end_date,
    )
    new_is_ongoing = update_data.get(
        "is_ongoing",
        project.is_ongoing,
    )

    if (
        new_start_date is not None
        and new_end_date is not None
        and new_end_date < new_start_date
    ):
        raise ValueError(
            "end_date cannot be earlier than start_date."
        )

    if new_is_ongoing and new_end_date is not None:
        raise ValueError(
            "Ongoing project cannot have an end_date."
        )

    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)

    return project


def delete_project(
    db: Session,
    project: Project,
) -> None:
    db.delete(project)
    db.commit()
# =========================================================
# Certifications
# =========================================================

def create_certification(
    db: Session,
    user_id: uuid.UUID,
    data: CertificationCreate,
) -> Certification:
    certification = Certification(
        user_id=user_id,
        **data.model_dump(),
    )

    db.add(certification)
    db.commit()
    db.refresh(certification)

    return certification


def get_user_certifications(
    db: Session,
    user_id: uuid.UUID,
) -> list[Certification]:
    statement = (
        select(Certification)
        .where(Certification.user_id == user_id)
        .order_by(
            Certification.issue_date.desc().nullslast(),
            Certification.created_at.desc(),
        )
    )

    return list(db.scalars(statement).all())


def get_user_certification(
    db: Session,
    user_id: uuid.UUID,
    certification_id: uuid.UUID,
) -> Certification | None:
    statement = select(Certification).where(
        Certification.id == certification_id,
        Certification.user_id == user_id,
    )

    return db.scalar(statement)


def update_certification(
    db: Session,
    certification: Certification,
    data: CertificationUpdate,
) -> Certification:
    update_data = data.model_dump(exclude_unset=True)

    new_issue_date = update_data.get(
        "issue_date",
        certification.issue_date,
    )

    new_expiration_date = update_data.get(
        "expiration_date",
        certification.expiration_date,
    )

    if (
        new_issue_date is not None
        and new_expiration_date is not None
        and new_expiration_date < new_issue_date
    ):
        raise ValueError(
            "expiration_date cannot be earlier than issue_date."
        )

    for field, value in update_data.items():
        setattr(certification, field, value)

    db.commit()
    db.refresh(certification)

    return certification


def delete_certification(
    db: Session,
    certification: Certification,
) -> None:
    db.delete(certification)
    db.commit()
# =========================================================
# Career Goals
# =========================================================


def create_career_goal(
    db: Session,
    user_id: uuid.UUID,
    data: CareerGoalCreate,
) -> CareerGoal:
    career_goal = CareerGoal(
        user_id=user_id,
        **data.model_dump(),
    )

    db.add(career_goal)
    db.commit()
    db.refresh(career_goal)

    return career_goal


def get_user_career_goals(
    db: Session,
    user_id: uuid.UUID,
) -> list[CareerGoal]:
    statement = (
        select(CareerGoal)
        .where(CareerGoal.user_id == user_id)
        .order_by(
            CareerGoal.is_active.desc(),
            CareerGoal.priority.asc(),
            CareerGoal.created_at.desc(),
        )
    )

    return list(db.scalars(statement).all())


def get_user_career_goal(
    db: Session,
    user_id: uuid.UUID,
    career_goal_id: uuid.UUID,
) -> CareerGoal | None:
    statement = select(CareerGoal).where(
        CareerGoal.id == career_goal_id,
        CareerGoal.user_id == user_id,
    )

    return db.scalar(statement)


def update_career_goal(
    db: Session,
    career_goal: CareerGoal,
    data: CareerGoalUpdate,
) -> CareerGoal:
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(career_goal, field, value)

    db.commit()
    db.refresh(career_goal)

    return career_goal


def delete_career_goal(
    db: Session,
    career_goal: CareerGoal,
) -> None:
    db.delete(career_goal)
    db.commit()