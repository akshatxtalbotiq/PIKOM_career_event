# PIKOM Event Platform — Application Guide

This guide explains the current attendee and organizer journeys, where each
feature lives, and how to try the application with synthetic data. The platform
has two interfaces: a Next.js attendee app and a Django organizer application.
The Django admin site at `/admin/` is available for database administration;
event organizers normally use the Django pages described below.

## The main concepts

| Application term | Django model | What it represents |
| --- | --- | --- |
| Event | `Campaign` | Event details, dates, venue, theme, and the organizer team. |
| Registration form | `Survey` | Public form attached to an event. It can contain identity and custom questions. |
| Attendee | `SurveyUser` | A submitted registration, its approval state, QR status, and check-in state. |
| Session | `EventSession` | A scheduled talk, panel, or workshop with optional capacity. |
| Employer and job | `Employer`, `Job` | Organizations and opportunities shown to attendees. |
| Interview | `InterviewSlot`, `InterviewBooking` | Employer availability and attendee bookings. |
| Floor map | `FloorMap`, `Booth` | Published venue map and clickable exhibitor locations. |
| Education and training | `University`, `UniversityProgram`, `TrainingProvider`, `VoucherPromotion` | Programs and promotions attendees can explore or claim. |

The older golf registration feature uses separate Golf models and pages. It is
retained for existing data and is hidden from the organizer navigation by
default; see [Legacy Golf](#legacy-golf).

## Attendee journey

### 1. Find an event and register

1. Open the Next.js app at `http://localhost:3000/`. The home page lists active
   Django events that have an active registration form.
2. Choose **Register** for an event. The registration page loads the active
   form questions from Django. Name and email are required; phone and
   organization can also be collected. Custom text, select, radio, and checkbox
   questions appear with the identity fields.
3. Submit the form. Django creates a pending attendee registration and sends a
   receipt email when email delivery is configured. The browser receives a
   private attendee access token and opens the attendee dashboard.

The standalone Django-hosted registration page is also available at
`/event/<form-slug-or-code>/`. The Next.js app uses `/register?event=<event-id>`.

### 2. Wait for organizer review

New registrations start as **Pending**. Pending attendees can open their
dashboard, but bookings and other gated actions require approval. An attendee
can enter the private access code at `http://localhost:3000/login/`, or use the
browser session created by registration. The access code is a credential: keep
it private and do not share it.

After approval, the attendee's check-in QR appears in the Next.js app. Approval
does not automatically send the QR email; the organizer can send that separately
from the attendee list. The `qr_sent` status tracks email delivery, not whether
the approved attendee can display their QR in the app. Approved attendees can
also use the event directory and booking actions.

### 3. Explore and take part

The attendee navigation provides:

- **Dashboard** — event details, approval state, and a summary of the personal
  schedule.
- **Employers** — organization profiles and booth locations.
- **Jobs** — openings, application links, and save/unsave controls.
- **Interviews** — open time choices offered by employers; attendees can book
  an available time or cancel a booking from their schedule.
- **Universities** — institutions, programs, eligibility, and intake details.
- **Training** — providers and current promotions; attendees can claim and
  later cancel a promotion claim.
- **Sessions** — event talks and workshops; attendees can add a session to
  their schedule or cancel it. Capacity is enforced by Django.
- **Map** — published venue maps, booths, and a text filter for locating an
  organization or booth.
- **My schedule** — session and interview bookings, saved jobs, and promotion
  claims.
- **Check-in** — registration reference, approval/check-in state, and the
  attendee's QR image when one has been issued.

The attendee API uses the registration code as a bearer token. It is separate
from Django organizer login and does not grant organizer access.

## Organizer journey (Django)

### 1. Sign in and find an event

Open `http://127.0.0.1:8000/login/`. After signing in, the event list is at
`http://127.0.0.1:8000/campaign_list/` (the root page also opens the event
list). Superusers can see all events; other users see events assigned to their
organizer team. A user must be on an event's team to manage that event.

Create an event from the event list. Add the event name, dates, venue,
organizer contact details, and theme. The event is the shared parent for its
registration forms, sessions, floor maps, employers, jobs, and attendee
records.

### 2. Set up the event experience

For an event with ID `EVENT_ID`:

- **Event overview and registration stats:** `/campaign_dashboard/EVENT_ID/`
- **Sessions and venue maps:** `/events/EVENT_ID/infrastructure/`
- **Employers, jobs, interviews, education, and training:**
  `/events/EVENT_ID/career/`
- **Registration forms:** `/registration_forms/` (or use the event's form
  shortcuts from the event list)
- **Attendee rows for a registration form:**
  `/survey_submission_list/FORM_ID/`
- **Form editor:** `/form_builder/FORM_ID/`

The form editor manages identity/custom questions and form appearance. Keep
the form active when registration should be open. The public Next.js event
list shows an event when it is active and has an active registration form.

In the infrastructure page, organizers can add sessions with dates, times,
locations, speakers, and capacity; publish a floor map; and position booths.
In the career page, organizers can add employer profiles and jobs, open
interview availability, university programs, training providers, and
promotions.

### 3. Review registrations and issue access

1. Open the form's attendee list from the event list or the URL above.
2. Review individual answers and use the list's status controls to mark
   selected attendees **Approved**, **Rejected**, or **Pending**.
3. Select approved attendees and use **Send QR** to send their check-in QR
   email. The bulk action skips already-sent messages by default; use its
   resend option when an attendee needs another copy.
4. Share or resend the attendee access link/code when needed. Attendees use it
   to enter the Next.js app; organizer login remains separate.

The dashboard summarizes registration totals, approval states, QR emails,
check-ins, sign-up timeline, and selected attendee breakdowns.

### 4. Event-day and post-event tasks

- Use the form's QR scanner link from the event list for camera-based check-in.
  Organizers can also change check-in state from the attendee list.
- Use the infrastructure and career pages to review session registration,
  interview bookings, and promotion claims.
- The attendee list supports participant editing, remarks, labels/printouts,
  reminders, and exports/reports where those actions are available.
- Create a feedback-purpose survey for post-event feedback and send its
  reminder to attendees from the form's bulk actions.

The mobile attendee check-in screen displays its QR and current check-in
state. It is read-only; organizers perform event check-in through the scanner
or attendee management tools.

## A complete local walkthrough with synthetic data

In the repository root, migrate the development database and run the repeatable
seed script:

```bash
python manage.py migrate
python synthetic_data/seed.py
python manage.py runserver
```

The seed script creates a showcase event with an organizer team, a registration
form, attendee records in pending/approved/rejected states, jobs, sessions,
interviews, a map with booths, university programs, training promotions, and
bookings. It is repeatable, never deletes data, and refuses to run when
`DJANGO_DEBUG=false`. See [synthetic data instructions](synthetic_data/README.md)
for the demo organizer credentials and attendee test tokens.

Start the attendee app in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Browse `http://localhost:3000/`, register a new address, then approve that
attendee in Django. To explore an already-approved attendee journey, enter one
of the seeded approved attendee tokens at `/login/`. Use an unused email when
submitting the same form again; duplicate event registrations are rejected.

## Legacy Golf

Golf tournaments, participant/sponsor forms, entries, player slots, and
sponsorship items are a separate legacy workflow in Django. The navigation is
hidden by default. Set `SHOW_LEGACY_GOLF_TOOLS=true` in the Django environment
and restart Django to show the Golf links for an authorized organizer. Golf
routes and existing Golf data are retained; the Next.js attendee app does not
replace these Golf pages.

## Where to look in the code

- `frontend/app/` — attendee routes and pages.
- `frontend/components/Explorer.js` — attendee event directory and dashboard
  sections.
- `register/api_views.py` and `register/api_urls.py` — attendee API and
  registration endpoints.
- `register/views.py`, `register/event_views.py`, and
  `register/career_views.py` — Django event, registration, infrastructure, and
  organizer workflows.
- `register/models.py` — event, form, attendee, session, map, career, and
  legacy Golf records.
- `register/templates/register/` — Django organizer and legacy page templates.
- `synthetic_data/` — repeatable sample data and the sample floor plan.

For deployment variables, static/media hosting, and Django/Next.js setup, see
the root [README](README.md).
