
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.careers.models import Career
from backend.app.career_twin.service import create_career_twin_snapshot
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
def validate_onet_career(
    db: Session,
    onet_soc_code: str | None,
) -> Career | None:
    if onet_soc_code is None:
        return None

    normalized_code = onet_soc_code.strip()

    if not normalized_code:
        raise ValueError("O*NET SOC code cannot be empty.")

    statement = select(Career).where(
        Career.onet_soc_code == normalized_code
    )

    career = db.scalar(statement)

    if career is None:
        raise ValueError(
            f"O*NET occupation '{normalized_code}' was not found."
        )

    return career
# =========================================================
# Career Goals
# =========================================================


def _unset_other_primary_career_goals(
    db: Session,
    user_id: uuid.UUID,
    exclude_goal_id: uuid.UUID | None = None,
) -> None:
    statement = select(CareerGoal).where(
        CareerGoal.user_id == user_id,
        CareerGoal.is_primary.is_(True),
    )

    if exclude_goal_id is not None:
        statement = statement.where(
            CareerGoal.id != exclude_goal_id
        )

    primary_goals = list(db.scalars(statement).all())

    for goal in primary_goals:
        goal.is_primary = False


def _create_career_goal_snapshot(
    db: Session,
    career_goal: CareerGoal,
) -> None:
    create_career_twin_snapshot(
        db=db,
        user_id=career_goal.user_id,
        trigger_type="CAREER_GOAL_UPDATED",
        source_type="CAREER_GOAL",
        source_reference=str(career_goal.id),
    )


def create_career_goal(
    db: Session,
    user_id: uuid.UUID,
    data: CareerGoalCreate,
) -> CareerGoal:
    create_data = data.model_dump()

    onet_soc_code = create_data.get("onet_soc_code")

    if onet_soc_code is not None:
        onet_soc_code = onet_soc_code.strip()

        validate_onet_career(
            db=db,
            onet_soc_code=onet_soc_code,
        )

        create_data["onet_soc_code"] = onet_soc_code

    is_primary = create_data.get("is_primary", False)
    is_active = create_data.get("is_active", True)

    if is_primary and not is_active:
        raise ValueError(
            "A primary career goal must be active."
        )

    if is_primary:
        _unset_other_primary_career_goals(
            db=db,
            user_id=user_id,
        )

    career_goal = CareerGoal(
        user_id=user_id,
        **create_data,
    )

    db.add(career_goal)
    db.commit()
    db.refresh(career_goal)

    if career_goal.is_primary and career_goal.is_active:
        _create_career_goal_snapshot(
            db=db,
            career_goal=career_goal,
        )

    return career_goal


def get_user_career_goals(
    db: Session,
    user_id: uuid.UUID,
) -> list[CareerGoal]:
    statement = (
        select(CareerGoal)
        .where(CareerGoal.user_id == user_id)
        .order_by(
            CareerGoal.is_primary.desc(),
            CareerGoal.is_active.desc(),
            CareerGoal.priority.asc(),
            CareerGoal.created_at.desc(),
        )
    )

    return list(db.scalars(statement).all())


def get_user_primary_career_goal(
    db: Session,
    user_id: uuid.UUID,
) -> CareerGoal | None:
    statement = (
        select(CareerGoal)
        .where(
            CareerGoal.user_id == user_id,
            CareerGoal.is_primary.is_(True),
            CareerGoal.is_active.is_(True),
        )
        .order_by(
            CareerGoal.updated_at.desc(),
            CareerGoal.created_at.desc(),
        )
        .limit(1)
    )

    return db.scalar(statement)


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

    if "onet_soc_code" in update_data:
        onet_soc_code = update_data["onet_soc_code"]

        if onet_soc_code is not None:
            onet_soc_code = onet_soc_code.strip()

            validate_onet_career(
                db=db,
                onet_soc_code=onet_soc_code,
            )

            update_data["onet_soc_code"] = onet_soc_code

    was_primary = (
        career_goal.is_primary
        and career_goal.is_active
    )

    old_target_state = (
        career_goal.target_role,
        career_goal.onet_soc_code,
        career_goal.target_industry,
        career_goal.target_location,
        career_goal.employment_type,
        career_goal.target_timeline_months,
        career_goal.is_active,
        career_goal.is_primary,
    )

    resulting_is_primary = update_data.get(
        "is_primary",
        career_goal.is_primary,
    )

    resulting_is_active = update_data.get(
        "is_active",
        career_goal.is_active,
    )

    if resulting_is_primary and not resulting_is_active:
        raise ValueError(
            "A primary career goal must be active."
        )

    if resulting_is_primary:
        _unset_other_primary_career_goals(
            db=db,
            user_id=career_goal.user_id,
            exclude_goal_id=career_goal.id,
        )

    for field, value in update_data.items():
        setattr(career_goal, field, value)

    db.commit()
    db.refresh(career_goal)

    is_primary_now = (
        career_goal.is_primary
        and career_goal.is_active
    )

    new_target_state = (
        career_goal.target_role,
        career_goal.onet_soc_code,
        career_goal.target_industry,
        career_goal.target_location,
        career_goal.employment_type,
        career_goal.target_timeline_months,
        career_goal.is_active,
        career_goal.is_primary,
    )

    primary_target_changed = (
        old_target_state != new_target_state
        and (was_primary or is_primary_now)
    )

    if primary_target_changed:
        _create_career_goal_snapshot(
            db=db,
            career_goal=career_goal,
        )

    return career_goal


def delete_career_goal(
    db: Session,
    career_goal: CareerGoal,
) -> None:
    user_id = career_goal.user_id
    goal_id = career_goal.id

    was_primary = (
        career_goal.is_primary
        and career_goal.is_active
    )

    db.delete(career_goal)
    db.commit()

    if was_primary:
        create_career_twin_snapshot(
            db=db,
            user_id=user_id,
            trigger_type="CAREER_GOAL_UPDATED",
            source_type="CAREER_GOAL",
            source_reference=str(goal_id),
        )