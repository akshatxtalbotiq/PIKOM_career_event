#!/usr/bin/env python3
"""Create repeatable demo data for the PIKOM event platform.

Run from the repository root with: python synthetic_data/seed.py
Records are tagged by stable names/emails and get_or_create so reruns do not
duplicate the showcase. This script never deletes existing records.
"""

import os
import sys
from datetime import datetime, time, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "picom.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402
from django.utils import timezone  # noqa: E402

from register.models import (  # noqa: E402
    Answer,
    Booth,
    Campaign,
    CampaignTeam,
    Employer,
    EventSession,
    FloorMap,
    InterviewBooking,
    InterviewSlot,
    Job,
    JobBookmark,
    Question,
    SessionRegistration,
    Survey,
    SurveyUser,
    TrainingProvider,
    University,
    UniversityProgram,
    VoucherClaim,
    VoucherPromotion,
)


EVENT_TITLE = "PIKOM Synthetic Showcase 2026"
ORGANIZER_USERNAME = "synthetic.organizer"
ORGANIZER_PASSWORD = "SyntheticDemo2026!"
ATTENDEE_EMAILS = [f"attendee{i:02d}@synthetic.pikom.test" for i in range(1, 13)]


def seed():
    if not settings.DEBUG:
        raise SystemExit(
            "Refusing to seed while DJANGO_DEBUG is false. Use a development database."
        )

    User = get_user_model()
    organizer, created = User.objects.get_or_create(
        username=ORGANIZER_USERNAME,
        defaults={"email": "organizer@synthetic.pikom.test", "is_staff": True},
    )
    if created:
        organizer.set_password(ORGANIZER_PASSWORD)
        organizer.save(update_fields=["password"])

    today = timezone.localdate()
    start = timezone.make_aware(datetime.combine(today + timedelta(days=30), time(8, 0)))
    end = timezone.make_aware(datetime.combine(today + timedelta(days=30), time(18, 0)))
    campaign, _ = Campaign.objects.update_or_create(
        title=EVENT_TITLE,
        defaults={
            "description": "A complete synthetic event for exploring registration, exhibitors, learning, interviews, and check-in.",
            "organizer_name": "PIKOM Demo Team",
            "organizer_email": "organizer@synthetic.pikom.test",
            "organizer_phone": "+60 3-0000 0000",
            "start_date": start,
            "end_date": end,
            "is_active": True,
            "event_time": "8:00 AM – 6:00 PM",
            "venue": "Kuala Lumpur Convention Centre, Kuala Lumpur",
            "dress_code": "Business casual",
            "theme_color": "#146c94",
            "need_qr": True,
            "extra_info": [
                {"icon": "🅿️", "label": "Parking", "value": "Synthetic demo parking information", "link": ""},
                {"icon": "📝", "label": "Agenda", "value": "View the event programme", "link": "https://example.com/agenda"},
            ],
        },
    )
    CampaignTeam.objects.get_or_create(campaign=campaign, user=organizer)

    survey, _ = Survey.objects.update_or_create(
        fkcampaign=campaign,
        title="Synthetic Showcase Registration",
        defaults={
            "description": "Register to explore the sample attendee experience.",
            "purpose": Survey.PURPOSE_REGISTRATION,
            "is_active": True,
            "show_event_details": True,
        },
    )
    identity_questions = [
        (Question.TYPE_IDENTITY_NAME, "Full name", True),
        (Question.TYPE_IDENTITY_PARTICIPANT_TYPE, "Participant type", True),
        (Question.TYPE_IDENTITY_EMAIL, "Email address", True),
        (Question.TYPE_IDENTITY_PHONE, "Phone", False),
        (Question.TYPE_IDENTITY_ORGANIZATION, "Organization", False),
    ]
    custom_questions = [
        (Question.TYPE_TEXT, "What are you hoping to learn?", None),
        (Question.TYPE_RADIO, "Which track interests you most?", ["AI & Data", "Cybersecurity", "Digital Careers"]),
        (Question.TYPE_CHECKBOX, "Which activities will you attend?", ["Keynotes", "Workshops", "Career fair"]),
    ]
    # Move existing custom questions out of the way, then establish the
    # identity rows first. This also repairs records created by earlier
    # versions of this repeatable seed script.
    existing_custom = survey.questions.exclude(question_type__in=Question.IDENTITY_TYPES.keys())
    for question in existing_custom:
        question.number += 10000
        question.save(update_fields=["number"])
    for number, (kind, text, required) in enumerate(identity_questions, start=1):
        question, _ = Question.objects.get_or_create(
            survey=survey,
            question_type=kind,
            defaults={"number": number, "text": text, "is_required": required},
        )
        question.number = number
        question.text = text
        question.is_required = required
        question.save(update_fields=["number", "text", "is_required"])
    question_rows = []
    for number, (kind, text, choices) in enumerate(custom_questions, start=len(identity_questions) + 1):
        question, _ = Question.objects.update_or_create(
            survey=survey,
            text=text,
            defaults={"question_type": kind, "text": text, "choices": choices,
                      "is_required": kind != Question.TYPE_CHECKBOX,
                      "number": number, "show_in_list": text.startswith("Which track")},
        )
        question_rows.append(question)

    attendee_rows = []
    status_cycle = [SurveyUser.STATUS_APPROVED] * 8 + [SurveyUser.STATUS_PENDING] * 3 + [SurveyUser.STATUS_REJECTED]
    organizations = ["Northstar Systems", "Meridian Bank", "Cloudline Labs", "PixelWorks"]
    for index, email in enumerate(ATTENDEE_EMAILS):
        status = status_cycle[index]
        attendee, created = SurveyUser.objects.get_or_create(
            survey=survey,
            email=email,
            defaults={
                "name": ["Aisha Rahman", "Daniel Lim", "Sofia Tan", "Arun Nair"][index % 4],
                "participant_type": SurveyUser.PARTICIPANT_TYPE_DELEGATE,
                "phone": f"+60 12-555-{index + 1000:04d}",
                "organization": organizations[index % len(organizations)],
                "approval_status": status,
                "qr_sent": status == SurveyUser.STATUS_APPROVED,
                "is_checked_in": status == SurveyUser.STATUS_APPROVED and index in (0, 1, 2),
                "approved_by": organizer if status == SurveyUser.STATUS_APPROVED else None,
                "approved_at": timezone.now() if status == SurveyUser.STATUS_APPROVED else None,
            },
        )
        if created:
            attendee.reg_no = f"SYN{attendee.pk:06d}"
            attendee.save(update_fields=["reg_no"])
        attendee_rows.append(attendee)
        for question, answer in zip(question_rows, [
            "Practical AI skills and new professional connections.",
            ["AI & Data", "Digital Careers"][index % 2],
            ["Keynotes", "Workshops", "Career fair"][:1 + index % 3],
        ]):
            Answer.objects.get_or_create(
                survey=survey, question=question, user=attendee,
                defaults={
                    "answer_text": answer if isinstance(answer, str) and question.question_type == Question.TYPE_TEXT else None,
                    "selected_options": answer if question.question_type != Question.TYPE_TEXT else None,
                },
            )

    floor_map, _ = FloorMap.objects.get_or_create(
        campaign=campaign,
        name="Synthetic Showcase Hall",
        defaults={"description": "Demo exhibition floor map with interactive booths.", "version": "Demo 1", "status": FloorMap.STATUS_PUBLISHED},
    )
    media_path = Path("synthetic_data") / "showcase-floor-plan.svg"
    source_map = ROOT / "synthetic_data" / "assets" / "showcase-floor-plan.svg"
    (ROOT / "media" / "synthetic_data").mkdir(parents=True, exist_ok=True)
    (ROOT / "media" / media_path).write_bytes(source_map.read_bytes())
    if floor_map.image.name != str(media_path):
        floor_map.image.name = str(media_path)
        floor_map.save(update_fields=["image"])

    booth_specs = [
        ("A01", "Northstar Systems", "Technology", 12, 22),
        ("A02", "Meridian Bank", "Finance", 32, 22),
        ("B01", "Cloudline Labs", "Cloud", 52, 52),
        ("B02", "PixelWorks University", "Education", 72, 52),
        ("C01", "FutureSkills Academy", "Training", 12, 72),
    ]
    booths = {}
    for number, name, category, x, y in booth_specs:
        booths[number], _ = Booth.objects.get_or_create(
            floor_map=floor_map, number=number,
            defaults={"name": name, "category": category, "organization_name": name,
                      "x_percent": x, "y_percent": y, "width_percent": 14, "height_percent": 12},
        )

    employer_specs = [
        ("Northstar Systems", "Technology that helps communities thrive.", "A01"),
        ("Meridian Bank", "Building inclusive digital finance.", "A02"),
        ("Cloudline Labs", "Cloud engineering and applied AI teams.", "B01"),
    ]
    employers = {}
    for name, description, booth_number in employer_specs:
        employers[name], _ = Employer.objects.update_or_create(
            campaign=campaign, name=name,
            defaults={"description": description, "website": "https://example.com", "contact_name": "Demo Contact",
                      "contact_email": "careers@example.com", "booth": booths[booth_number], "is_active": True},
        )

    job_specs = [
        ("Northstar Systems", "Junior Data Analyst", "internship", "Entry level", "Kuala Lumpur"),
        ("Northstar Systems", "Software Engineer", "full_time", "Early career", "Hybrid"),
        ("Meridian Bank", "Cybersecurity Associate", "full_time", "Entry level", "Kuala Lumpur"),
        ("Cloudline Labs", "Cloud Support Intern", "internship", "Student", "Hybrid"),
    ]
    jobs = []
    for employer_name, title, employment, level, location in job_specs:
        job, _ = Job.objects.update_or_create(
            employer=employers[employer_name], title=title,
            defaults={"description": f"Synthetic sample listing: {title}.", "requirements": "Curiosity, communication, and a willingness to learn.",
                      "employment_type": employment, "experience_level": level, "location": location,
                      "application_url": "https://example.com/careers", "is_active": True},
        )
        jobs.append(job)

    sessions = []
    session_specs = [
        ("Opening keynote: Skills for an AI-ready economy", time(9, 0), time(10, 0), 180, "Main Stage", "Dr. Maya Hassan", "speaking"),
        ("Building trustworthy AI products", time(10, 30), time(11, 30), 60, "Workshop Room 1", "Jason Wong", "panel"),
        ("Careers in cloud engineering", time(13, 0), time(14, 0), 80, "Main Stage", "Priya Nair", "employer"),
    ]
    for title, starts, ends, capacity, location, speaker, kind in session_specs:
        session, _ = EventSession.objects.update_or_create(
            campaign=campaign, title=title,
            defaults={"description": "A synthetic programme session for exploring the attendee schedule.",
                      "session_type": kind, "event_date": today + timedelta(days=30), "start_time": starts,
                      "end_time": ends, "capacity": capacity, "location": location,
                      "speaker_name": speaker, "status": EventSession.STATUS_SCHEDULED},
        )
        sessions.append(session)

    slots = []
    for employer_name in employers:
        slot, _ = InterviewSlot.objects.update_or_create(
            employer=employers[employer_name], date=today + timedelta(days=30), start_time=time(14, 0),
            defaults={"end_time": time(16, 0), "booking_mode": InterviewSlot.MODE_OPEN,
                      "slot_duration_minutes": 20, "capacity": 2,
                      "interviewer_info": "Meet the recruiting team at the employer booth.", "status": InterviewSlot.STATUS_OPEN},
        )
        slots.append(slot)

    university, _ = University.objects.update_or_create(
        campaign=campaign, name="PixelWorks University",
        defaults={"description": "Synthetic university profile for programmes and campus opportunities.",
                  "website": "https://example.com/university", "contact_name": "Admissions Team",
                  "contact_email": "admissions@example.com", "booth": booths["B02"], "is_active": True},
    )
    programs = [
        ("Applied Data Science", "12-month professional certificate", "Degree or equivalent experience"),
        ("Secure Software Engineering", "Part-time postgraduate programme", "Computing background preferred"),
    ]
    for name, description, eligibility in programs:
        UniversityProgram.objects.update_or_create(
            university=university, name=name,
            defaults={"description": description, "eligibility": eligibility,
                      "upcoming_batch_info": "Next intake: January 2027", "internship_fresher_info": "Internship placements available.", "is_active": True},
        )

    provider, _ = TrainingProvider.objects.update_or_create(
        campaign=campaign, name="FutureSkills Academy",
        defaults={"description": "Practical short courses in digital and professional skills.",
                  "website": "https://example.com/training", "contact_name": "Learning Team",
                  "contact_email": "learn@example.com", "booth": booths["C01"], "is_active": True},
    )
    promotion, _ = VoucherPromotion.objects.update_or_create(
        provider=provider, title="Synthetic learner pass",
        defaults={"description": "A sample promotion to demonstrate attendee claims.", "value_label": "20% off",
                  "expires_at": end + timedelta(days=14), "max_claims": 100,
                  "instructions": "Use code PIKOM-DEMO at checkout.", "is_active": True},
    )

    approved = [attendee for attendee in attendee_rows if attendee.approval_status == SurveyUser.STATUS_APPROVED]
    interview_start = datetime.combine(today, time(14, 0))
    for index, attendee in enumerate(approved):
        SessionRegistration.objects.get_or_create(session=sessions[index % len(sessions)], attendee=attendee)
        if index < len(jobs):
            JobBookmark.objects.get_or_create(job=jobs[index], attendee=attendee)
        VoucherClaim.objects.get_or_create(promotion=promotion, attendee=attendee)
        if index < len(slots):
            InterviewBooking.objects.get_or_create(
                slot=slots[index], attendee=attendee,
                start_time=(interview_start + timedelta(minutes=20 * index)).time(),
                defaults={"status": InterviewBooking.STATUS_BOOKED},
            )

    print(f"Synthetic showcase ready: {campaign.title} (campaign id {campaign.pk})")
    print(f"Organizer login: {ORGANIZER_USERNAME} / {ORGANIZER_PASSWORD}")
    print("Organizer URL: http://127.0.0.1:8000/login/")
    print(f"Public registration URL: http://127.0.0.1:8000/event/{survey.slug or survey.survey_code}/")
    print("Attendee API tokens (use as Bearer credentials):")
    for attendee in approved[:3]:
        print(f"  {attendee.email}: {attendee.registration_code}")
    print("Rerunning this script updates/reuses this synthetic showcase; it does not delete records.")


if __name__ == "__main__":
    seed()
