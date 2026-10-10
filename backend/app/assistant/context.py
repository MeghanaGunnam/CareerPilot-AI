"""Bounded owner-scoped structured retrieval, NOT semantic/vector RAG."""
import json
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.assistant.schemas import AssistantRequest, GroundingSource
from backend.app.acif.service import get_current_skill_states, get_minimum_action_path
from backend.app.assessments.recommendations import get_my_assessment_recommendations
from backend.app.assessments.service import get_user_attempts
from backend.app.applications.service import get_application, list_applications
from backend.app.career_twin.progress import get_progress
from backend.app.career_twin.service import build_riasec_state
from backend.app.careers.models import Career
from backend.app.certification_recommendations.service import get_certification_recommendations
from backend.app.jobs.matching import get_job_match
from backend.app.jobs.service import get_analysis, list_analyses
from backend.app.roadmap.models import RoadmapItem
from backend.app.students.service import get_profile_by_user_id, get_user_primary_career_goal

MAX_SOURCES = 12
MAX_CONTEXT_CHARS = 7000


def quoted(value) -> str:
    """Delimit small user labels; never send notes, body text or contact details."""
    text = str(value or "")
    return json.dumps(text[:160] + (" [label shortened]" if len(text) > 160 else ""), ensure_ascii=True)


def resolve_topic(request: AssistantRequest) -> str:
    if request.topic != "auto":
        return request.topic
    text = request.message.casefold()
    if request.application_id or any(word in text for word in ("application", "interviewing", "interviews")):
        return "applications"
    if request.jd_analysis_id or any(word in text for word in ("this job", "job analysis", "job description", "this jd")):
        return "job_match"
    for topic, words in (("certifications", ("certification", "certificate")), ("progress", ("changed", "progress", "history")),
                         ("assessments", ("assessment", "exam", "score")), ("skills", ("evidence", "skill", "weak", "gap")),
                         ("profile", ("profile", "interest", "career goal", "target role"))):
        if any(word in text for word in words):
            return topic
    return "next_steps"


def validate_references(db: Session, user_id: UUID, request: AssistantRequest):
    # Validate ALL supplied references, even with no provider or a different topic.
    if request.jd_analysis_id:
        get_analysis(db, user_id, request.jd_analysis_id)
    if request.application_id:
        get_application(db, user_id, request.application_id)


def build_context(db: Session, user_id: UUID, request: AssistantRequest) -> tuple[str, list[GroundingSource], list[str]]:
    validate_references(db, user_id, request)
    topic = resolve_topic(request)
    sources: list[GroundingSource] = []
    limitations = ["Structured context is a bounded selection, not a complete account of your capabilities."]

    def add(kind, text, provenance, href):
        if len(sources) >= MAX_SOURCES or sum(len(source.text) for source in sources) + len(text) > MAX_CONTEXT_CHARS:
            if "Some context was omitted to keep this request bounded." not in limitations:
                limitations.append("Some context was omitted to keep this request bounded.")
            return
        sources.append(GroundingSource(id=f"s{len(sources) + 1}", kind=kind, text=text, provenance=provenance, href=href))

    try:
        if topic == "profile":
            profile = get_profile_by_user_id(db, user_id)
            add("FACT", "A student profile is recorded." if profile else "A student profile is not available.", "Current owned profile lookup; contact details omitted", "/profile")
            goal = get_user_primary_career_goal(db, user_id)
            if goal:
                add("FACT", f"Your recorded target role is {quoted(goal.target_role)}.", "Current primary career goal", "/profile")
                career = db.scalar(select(Career).where(Career.onet_soc_code == goal.onet_soc_code)) if goal.onet_soc_code else None
                if career:
                    add("FACT", f"Its O*NET occupational anchor is {quoted(career.title)} ({career.onet_soc_code}); the occupational anchor is distinct from your target role.", "Stored O*NET occupational mapping", "/dashboard")
            else:
                limitations.append("No primary career goal is recorded.")
            riasec = build_riasec_state(db, user_id)
            if riasec:
                add("MODEL_OUTPUT", f"Your latest RIASEC dominant code is {quoted(riasec['dominant_code'])}. It describes recorded interests, not readiness or employment probability.", "Latest owned RIASEC result", "/assessment")
        elif topic == "skills":
            result = get_current_skill_states(db, user_id)
            states = sorted(result["skills"], key=lambda state: (str(state.get("name", "")).casefold() not in request.message.casefold(), str(state.get("name", ""))))[:6]
            for state in states:
                types = sorted({detail["source_type"] for detail in state.get("evidence_details", [])})
                measurement = state.get("estimated_proficiency")
                text = (f"For {quoted(state['name'])}, the latest recorded Career Twin has {state['evidence_count']} evidence entries "
                        f"with source types {', '.join(types) or 'none recorded'}. ACIF evidence confidence is {state['evidence_confidence']}; this is not proficiency. "
                        + (f"Assessment-derived measurement {measurement} is assessment-specific, not universal proficiency." if measurement is not None else "No assessment-derived measurement is recorded for this skill."))
                add("MODEL_OUTPUT", text, f"Career Twin snapshot {result['snapshot_version']}; {result['model_version']}", "/evidence")
        elif topic == "job_match":
            analysis_id = request.jd_analysis_id
            if analysis_id is None:
                recent = list_analyses(db, user_id, limit=1)["items"]
                analysis_id = recent[0].id if recent else None
            if analysis_id is not None:
                match = get_job_match(db, user_id, analysis_id)
                alignment = match["alignment"]
                add("MODEL_OUTPUT", (f"CareerPilot Evidence Alignment has {alignment['numerator']} strongly evidenced technologies out of {alignment['denominator']} eligible mapped required technologies." if alignment["value"] is not None else "CareerPilot Evidence Alignment is unavailable because eligible information is insufficient.") + " This is not hiring probability or complete job suitability.", f"Owned JD {analysis_id}; snapshot {match['snapshot_version']}; {match['matching_version']}", "/job-match")
                rows = sorted(match["requirements"], key=lambda row: (str(row["canonical_technology"] or "").casefold() not in request.message.casefold(), row["requirement"].position))[:5]
                for row in rows:
                    add("MODEL_OUTPUT", f"JD interpretation {quoted(row['canonical_technology'] or row['requirement'].group)}: {row['state']}. {row['explanation']} Strength interpretation: {row['strength']}. Missing evidence is not missing skill.", f"Persisted requirement {row['requirement'].id}; quote remains available on the JD page", "/job-match")
            else:
                limitations.append("No owned job description analysis is available.")
        elif topic == "applications":
            if request.application_id:
                items = [get_application(db, user_id, request.application_id)]
            else:
                status = "INTERVIEW" if "interview" in request.message.casefold() else None
                listing = list_applications(db, user_id, status, 5, 0)
                items = listing["items"]
                add("FACT", f"You have {listing['total']} recorded applications" + (" with status INTERVIEW." if status else ".") + " At most five recent records are included here; no employer outcome is inferred.", "Current owner-scoped application list", "/applications")
            for item in items:
                add("FACT", f"Application for {quoted(item.job_title)} at {quoted(item.company)}: recorded status {item.status}; applied date {item.applied_date or 'not recorded'}.", f"Owned application {item.id}; notes excluded", "/applications")
        elif topic == "progress":
            result = get_progress(db, user_id, limit=2)
            add("MODEL_OUTPUT", result["history_message"], "Actual Career Twin snapshot comparison", "/progress")
            for metric in result["comparison"]:
                if metric["change"] is not None:
                    add("MODEL_OUTPUT", f"{metric['label']}: previous recorded value {metric['previous_recorded_value']}, current recorded value {metric['current_recorded_value']}, change {metric['change']}. This is not continuous tracking or proficiency.", "Latest two compatible owned snapshots", "/progress")
            add("FACT", f"Current completed assessment-attempt count is {result['completed_assessment_attempts']}; this current total is not historical measurement coverage.", "Current owner-scoped completed attempts", "/assessment")
        elif topic == "certifications":
            result = get_certification_recommendations(db, user_id)
            for item in result["recommendations"][:4]:
                add("PERSONALIZED_RECOMMENDATION", f"Optional certification recommendation: {quoted(item['name'])} from {quoted(item['provider'])}. {item['reason']} It is not an earned certification or proof of proficiency; verify current eligibility with the provider.", f"Existing curated catalogue {item['key']}; snapshot {result['snapshot_version']}", "/certifications")
        elif topic == "assessments":
            for attempt in get_user_attempts(db, user_id, limit=3):
                score = f" Score: {attempt.percentage}% on this assessment only." if attempt.status == "COMPLETED" and attempt.percentage is not None else " No completed assessment score is reported here."
                add("FACT", f"Recorded assessment {quoted(attempt.assessment.title)} (v{attempt.assessment.version}): {attempt.status}.{score} This is not universal proficiency.", f"Owned assessment attempt {attempt.id}", "/assessment")
            result = get_my_assessment_recommendations(db, user_id)
            for item in result["recommendations"][:3]:
                add("PERSONALIZED_RECOMMENDATION", f"Existing assessment recommendation: {quoted(item['title'])}. {item['reason']}", f"Active assessment {item['assessment_id']}; current goal mapping", "/assessment")
        else:
            # Persisted roadmap rows only: get_roadmap generates/commits items.
            rows = db.scalars(select(RoadmapItem).where(RoadmapItem.user_id == user_id, RoadmapItem.status.in_(["NOT_STARTED", "IN_PROGRESS"])).order_by(RoadmapItem.display_order, RoadmapItem.id).limit(3)).all()
            for row in rows:
                add("PERSONALIZED_RECOMMENDATION", f"Recorded roadmap action: {quoted(row.recommended_action)}; status {row.status}. No completion is inferred.", f"Persisted roadmap {row.id}; snapshot {row.snapshot_version}", "/roadmap")
            goal = get_user_primary_career_goal(db, user_id)
            career = db.scalar(select(Career).where(Career.onet_soc_code == goal.onet_soc_code)) if goal and goal.onet_soc_code else None
            if career:
                result = get_minimum_action_path(db, user_id, career.id)
                for action in result["minimum_action_path"]["path"][:3]:
                    add("PERSONALIZED_RECOMMENDATION", f"ACIF Minimum Action Path suggests: {quoted(action['recommended_action'])}. This is a heuristic suggestion, not an optimized or guaranteed outcome.", f"ACIF Minimum Action Path; snapshot {result['snapshot_version']}", "/roadmap")
    except HTTPException as error:
        if error.status_code != 404:
            raise
        limitations.append("Some relevant structured context is not available yet; no missing information was inferred.")
    if not sources:
        limitations.append("No relevant source statements are available. Add evidence or select another context topic.")
    return topic, sources, limitations
