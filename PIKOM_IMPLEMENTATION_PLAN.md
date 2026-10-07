# PIKOM Event Platform --- Implementation Plan

## Purpose

This document is the source of truth for implementing the existing
event-management platform into the new **PIKOM Career Festival / Event
Management Platform**.

The implementation must be completed **phase by phase**.

### Mandatory Agent Rule

> **DO NOT implement multiple phases in one run.**
>
> Complete only the current phase.
>
> After the current phase is implemented: 1. Run the relevant
> tests/checks. 2. Review the changes for regressions. 3. Provide a
> concise summary of what changed. 4. Clearly list any remaining issues
> or decisions. 5. **STOP.**
>
> Do not start the next phase until the user explicitly says to proceed.

### Mandatory Phase Workflow

Every phase must include automated tests for the functionality introduced
or modified in that phase. This is a required completion gate, not an
optional follow-up. Complete these steps in order:

1. Implement the current phase.
2. Add or update relevant Django automated tests for the changes.
3. Run `python manage.py check`.
4. Run `python manage.py test`.
5. Fix failures and rerun the relevant checks and test suite until they
   pass. Do not mark the phase complete while a required check fails or
   has not been run.
6. Review the changes for regressions, report the test count and results,
   and request approval for the next phase.

Only after all six steps may the phase be marked complete. If the
environment prevents a required command from running, report the blocker
and leave the phase incomplete; do not request approval to proceed.

The existing working functionality should be preserved unless this
document explicitly says otherwise.

------------------------------------------------------------------------

# Current Product Direction

The existing application is an event-management platform with an
established foundation around:

-   Campaign/event creation
-   Event details and branding
-   Registration forms
-   Custom form builder
-   Participant registration
-   Approval/rejection
-   QR generation and email
-   Check-in
-   Badge printing
-   Reminders
-   Feedback
-   Reports/exports
-   Organizer/team permissions

The new PIKOM platform should evolve this foundation into a
**career-festival/event platform**.

The broader product will eventually support:

-   Employers
-   Jobs
-   Interview booking
-   Universities and programs
-   Training providers
-   Vouchers/promotions
-   Stage sessions
-   Event agenda
-   Floor maps
-   Booths
-   Booth navigation
-   Attendee schedules
-   Mobile-first attendee experience

The event-management/infrastructure work is the primary focus of this
plan.

------------------------------------------------------------------------

# Architecture Direction

## Keep the Existing Django Backend

Do not rewrite the existing backend.

Continue using the existing Django application, database,
authentication, permissions, event-management logic, registration
system, QR/check-in functionality, etc.

Do not rename core existing models such as `Campaign` simply for
terminology purposes unless there is a strong technical reason.

In particular:

-   Keep `Campaign` as the existing event entity for now.
-   Keep `Survey` and existing registration functionality where
    reusable.
-   Keep `SurveyUser` and existing participant functionality where
    reusable.
-   Preserve existing migrations and production data compatibility.

## Admin / Organizer Experience

Initially continue using the existing Django server-rendered
admin/organizer UI.

Improve and extend it rather than replacing it immediately.

The organizer needs to be able to configure the complete event from the
admin side.

## Attendee Experience

The eventual attendee-facing experience should be **mobile-first** and
can be implemented using Next.js.

Next.js should not be introduced prematurely.

Before building the Next.js application:

-   establish the required backend models
-   establish business logic
-   establish permissions
-   establish stable API boundaries
-   verify the workflows through the existing Django UI

This keeps the backend and product model stable before introducing a
second frontend.

------------------------------------------------------------------------

# Phase 1 --- Event Management Foundation

## Goal

Make the existing event-management system a strong foundation for PIKOM
events.

The organizer should be able to create and configure an event cleanly
without dealing with golf-specific functionality or confusing legacy UI.

## Scope

### 1. Event Creation

Improve the existing campaign/event creation flow.

Support:

-   Event name
-   Start date
-   End date
-   Event time
-   Venue
-   Organizer/contact information
-   Event status
-   Registration status
-   Branding/theme information
-   Event banner
-   Basic event description

Use the existing `Campaign` model where practical.

Do not unnecessarily rename or replace it.

### 2. Event Settings

Improve the event settings experience.

Organize configuration logically, for example:

-   Basic information
-   Date/time
-   Venue
-   Branding
-   Registration
-   Check-in
-   Emails
-   Event status

The exact UI structure can follow the existing design system while
making it cleaner and easier to use.

### 3. Organizer Dashboard

Improve the existing campaign/event dashboard.

It should make the event's status easy to understand.

Potential information:

-   Total registrations
-   Approved attendees
-   Pending approvals
-   Checked-in attendees
-   Registration status
-   Event date/time
-   Quick actions

Do not build advanced analytics yet.

### 4. Registration Foundation

Preserve and improve the existing:

-   Registration form
-   Form builder
-   Custom questions
-   Registration submission
-   Approval/rejection
-   QR generation
-   Email flow
-   Check-in

Do not rewrite working functionality without a clear reason.

### 5. Golf Functionality

Do not delete golf code in this phase.

Instead:

-   Hide golf-specific functionality from the primary PIKOM organizer
    experience.
-   Remove golf navigation/menu items where appropriate.
-   Ensure golf functionality does not interfere with the new event
    flow.

Actual cleanup/deletion can happen later after the new platform is
stable.

### 6. UI Cleanup

Improve the existing organizer UI where it directly affects event
creation and management.

Focus on:

-   Navigation
-   Information hierarchy
-   Forms
-   Empty states
-   Buttons/actions
-   Consistent terminology
-   Responsive behavior
-   Visual polish

Do not redesign the entire product yet.

## Phase 1 Deliverables

At the end of Phase 1:

-   Organizer can create an event.
-   Organizer can configure event details.
-   Organizer can configure registration.
-   Existing registration/approval/QR/check-in functionality still
    works.
-   Dashboard provides useful event status.
-   Golf functionality is no longer prominent in the main PIKOM flow.
-   Existing tests continue to pass.
-   New functionality has appropriate tests.

## Phase 1 Gate

STOP after Phase 1.

Report:

-   Files changed
-   Models/migrations changed
-   Routes/views added or modified
-   UI changes
-   Tests executed
-   Known issues
-   Any migration/data risks

**Wait for explicit approval before starting Phase 2.**

### Phase 1 Test Status

The initial Phase 1 implementation did not include automated tests. This
was identified during review and corrected in the follow-up recorded
below, which adds coverage for event creation/date handling, event access
permissions, banner and description rendering, and dashboard registration
status/counts, then runs both required Django commands.

**Follow-up completed 2026-10-07:** Added ten Phase 1 automated tests
covering event creation/profile persistence and date boundaries, invalid
event input, banner size validation and fallback rendering, event
description rendering, event edit/dashboard access, and dashboard
registration states and attendee counts. The first test run exposed an
end-date parsing defect; it was fixed and the complete suite was rerun
successfully.

- `python manage.py check`: passed, no issues.
- `python manage.py test`: passed, 10 tests discovered and 10 run.
- Additional `makemigrations --check --dry-run` reports existing
  `Golf*` models without migrations. This pre-existing golf schema drift
  was not changed as part of this Phase 1 test follow-up.

Phase 1 remains at its approval gate; do not begin Phase 2 until the user
explicitly approves it.

------------------------------------------------------------------------

# Phase 2 --- Festival Infrastructure

## Goal

Add the event-specific infrastructure required for a career festival.

This phase focuses on things owned by the event organizer:

-   Stage
-   Sessions
-   Agenda
-   Floor map
-   Booths
-   Booth configuration

Employer/job functionality should not be deeply implemented here unless
required for booth relationships.

## Scope

### 1. Stage / Session Management

Create the data model and organizer UI for event sessions.

A session should support concepts such as:

-   Event
-   Title
-   Description
-   Session type
-   Date
-   Start time
-   End time
-   Duration
-   Location
-   Capacity
-   Speaker/presenter information
-   Status

Session types may include:

-   Panel
-   Live session
-   Speaking session
-   Employer presentation
-   University presentation
-   Other configurable event sessions

### 2. Session Registration

Support:

-   Session capacity
-   Attendee registration
-   Registration status
-   Cancellation where appropriate
-   Preventing registration after capacity is reached

The exact attendee UI can remain basic in Django during this phase.

### 3. Agenda

Provide an organizer view for the event agenda.

Support:

-   Sessions ordered by date/time
-   Session status
-   Capacity
-   Location
-   Basic filtering

### 4. Floor Map

Create an event-level floor map concept.

Support:

-   Map/image upload
-   Event association
-   Map metadata
-   Version/status if needed

Do not over-engineer indoor positioning.

### 5. Booths

Create a booth model associated with an event/floor map.

A booth should support concepts such as:

-   Booth number
-   Booth name
-   Description
-   Location on floor map
-   Coordinates/position
-   Size
-   Category/type
-   Organization reference
-   Active/inactive status

The organization could later be an employer, university, training
provider, or another event participant.

### 6. Booth Navigation Data

Prepare the backend/data model so the future attendee application can:

-   Load the floor map
-   Load booth locations
-   Identify booths
-   Open booth details
-   Navigate/filter booths

Do not build sophisticated indoor navigation unless explicitly required.

## Phase 2 Deliverables

At the end of Phase 2:

-   Organizer can create/manage sessions.
-   Organizer can define session capacity.
-   Organizer can manage the event agenda.
-   Organizer can upload/configure a floor map.
-   Organizer can create and position booths.
-   Data is structured cleanly for future attendee APIs/frontend.
-   Relevant tests exist.

## Phase 2 Gate

STOP after Phase 2.

Report:

-   New models
-   Migrations
-   Admin/organizer screens
-   Session/agenda behavior
-   Floor-map behavior
-   Booth behavior
-   Tests
-   Known limitations

**Wait for explicit approval before starting Phase 3.**

### Phase 2 Implementation Status

**Completed 2026-10-07; Phase 3 has not been started.** Phase 2 added
event sessions and attendee bookings, an ordered/filterable organizer
agenda, event floor maps, and booths with normalized image coordinates.
Organizer management is available from the event dashboard; attendees
can browse the agenda and book or cancel sessions through a registration
token link. Capacity is enforced when booking, and cancelled bookings can
be restored while space remains.

- Models: `EventSession`, `SessionRegistration`, `FloorMap`, and `Booth`.
- Migration: `register/migrations/0069_phase2_event_infrastructure.py`.
- Organizer screen: event infrastructure page for session, map, and booth
  creation, editing, filtering, positioning, and deletion.
- Attendee screens: event agenda and session booking/cancellation pages.
- Automated tests: 9 Phase 2 tests added; the full suite discovered and
  ran 19 tests successfully, including attendee email agenda links.
- `python manage.py check`: passed with no issues.
- Known schema drift: migration autodetection still reports existing
  `Golf*` models without migrations. Those unrelated golf tables were not
  added to this Phase 2 migration.

Phase 2 is at its approval gate. Wait for explicit approval before
starting Phase 3.

------------------------------------------------------------------------

# Phase 3 --- Career Festival Backend Modules

## Phase 3 Status — Completed 2026-10-07

Phase 3 implementation and its approval gate are complete. The workflow
below was followed: implementation, phase-specific Django tests,
`manage.py check`, full `manage.py test`, failure fixes, and final review.
Phase 4 has not been started.

Implemented:

- Event-scoped employer profiles and job listings, including attendee job
  bookmarks and direct application links/email addresses.
- Fixed-block and generated open interview times, attendee bookings,
  cancellation/rebooking, approved-attendee eligibility, and per-time
  capacity protection.
- University/program profiles, training providers, and promotions with
  expiry, optional documents, claim limits, cancellation/reclaim, and
  claim instructions emailed to attendees.
- Organizer career-directory management protected by event team access;
  attendee career hub links use the existing registration token and all
  listed records are scoped to that registration's event.
- Career hub links in registration and QR emails, and Django admin entries
  for the new domain models.

Verification:

- Migration: `register/migrations/0070_phase3_career_modules.py`.
- Automated coverage: 6 Phase 3 tests were added. The full suite discovered
  and ran 25 tests; all passed.
- `python manage.py check`: passed with no issues.
- `python manage.py test`: passed (25 tests).
- `python manage.py makemigrations --check --dry-run` still reports only
  the pre-existing Golf model migration drift (`GolfEvent`, `GolfForm`, and
  related Golf models). Those models were intentionally excluded from the
  Phase 3 migration. This check is informational and was not one of the
  mandatory phase gates.
- No duplicate employer/job/university/training/voucher/interview workflows
  were found before implementation.

**Phase 3 is complete. Stop here and wait for explicit approval before
starting Phase 4.**

## Goal

Implement the career-festival domain that sits on top of the event
infrastructure.

This phase can overlap conceptually with work owned by other developers,
so inspect the current codebase before creating duplicate models or
workflows.

## Scope

### 1. Employers

Support:

-   Employer profile
-   Name
-   Logo
-   Description
-   Website/contact information
-   Event association
-   Booth association
-   Active/inactive state

### 2. Jobs

Support:

-   Employer
-   Job title
-   Description
-   Requirements
-   Employment type
-   Experience/level
-   Location
-   Application information
-   Active/inactive state

Prepare the model for attendee actions such as:

-   View
-   Save/bookmark
-   Apply

Do not invent an external job-application system if one does not exist.

### 3. Interview Slots

Support configurable interview rules.

The event may have employers with:

#### Fixed blocks

Example:

-   IBM: 3:00--4:00 PM

#### Open booking slots

Example:

-   20-minute slots
-   Multiple available slots during a configured period

The organizer should be able to configure:

-   Employer
-   Date
-   Start time
-   End time
-   Slot duration
-   Capacity
-   Interviewer information where required
-   Booking status

### 4. Interview Bookings

Support:

-   Attendee
-   Interview slot
-   Booking status
-   Created time
-   Cancellation where appropriate
-   Capacity protection

Do not allow overbooking.

### 5. Universities

Support:

-   University profile
-   Description
-   Website/contact
-   Event association
-   Booth association
-   Programs

### 6. Programs

Support:

-   University
-   Program name
-   Description
-   Eligibility
-   UPIKOMing batch information
-   Internship/fresher information where applicable

### 7. Training Providers

Support:

-   Provider profile
-   Description
-   Website/contact
-   Event association
-   Booth association

### 8. Vouchers / Promotions

Support:

-   Promotion/voucher title
-   Description
-   Discount/value
-   Expiration if required
-   Provider
-   PDF/document upload where required
-   Claim/subscription state

The eventual flow may be:

1.  Attendee views training provider.
2.  Attendee subscribes/claims promotion.
3.  System records the claim.
4.  Attendee receives relevant email/instructions.

Do not over-engineer redemption unless required.

## Phase 3 Deliverables

At the end of Phase 3:

-   Employer data exists.
-   Job data exists.
-   Interview scheduling exists.
-   Interview booking exists.
-   University/program data exists.
-   Training provider data exists.
-   Voucher/promotion workflow exists.
-   Relationships to event/booths are established.
-   Permissions are enforced.
-   Tests cover critical business rules.

## Phase 3 Gate

STOP after Phase 3.

Report:

-   Models/migrations
-   Business rules
-   Booking logic
-   Capacity logic
-   Admin/organizer screens
-   Permissions
-   Tests
-   Any overlap/conflict with other developer work

**Wait for explicit approval before starting Phase 4.**

------------------------------------------------------------------------

# Phase 4 --- API + Next.js Attendee Experience

## Phase 4 Status — Completed 2026-10-07

Phase 4 implementation and its approval gate are complete. The mandatory
workflow was followed: implementation, phase-specific tests, Django system
check, full Django test suite, fixes, and final frontend build. Phase 5 has
not been started.

Implemented API boundary (`/api/`):

- Public event list/detail, registration form schema, and attendee
  registration endpoints.
- Registration preserves configured identity and custom question answers;
  newly registered attendees remain pending organizer approval.
- Attendee profile read/update, event directory, combined schedule,
  read-only check-in state and approved QR image.
- Event-scoped employers/jobs, universities/programs, training providers and
  promotions, interview slots, sessions/capacity, published floor maps and
  booth coordinates.
- Attendee job bookmark, session registration/cancellation, interview
  booking/cancellation, and voucher claim/cancellation actions.
- Mutating endpoints require the attendee's existing high-entropy
  `registration_code` as a Bearer token. Event browsing/registration are
  public. Attendee actions are restricted to the attendee's own event and
  approved registrations. Check-in is read-only for attendees.

Implemented a separate `frontend/` Next.js application with mobile-first
event discovery, configured registration forms, confirmation, attendee
token login, dashboard, employers, jobs, interviews, universities, training
promotions, sessions, schedule/bookings, searchable floor maps/booths, and
check-in QR display. Next.js rewrites `/api/` and `/media/` to Django using
`DJANGO_API_URL`. Setting `ATTENDEE_APP_URL` in the Django environment adds
private app login links to registration emails.

Verification:

- No Phase 4 database migration was required.
- 8 Phase 4 Django API tests were added. Full suite discovered and ran 33
  tests; all passed.
- `python manage.py check`: passed with no issues.
- `python manage.py test`: passed (33 tests).
- `npm run build` in `frontend/`: passed with all app routes compiled.
- `npm install` audited the frontend dependency tree with no reported
  vulnerabilities.
- No browser-driven end-to-end test suite exists yet; frontend verification
  is the production build plus the API integration tests.

The attendee token is a bearer credential and currently has no separate
expiry/rotation flow. Keep it private. Configure `ATTENDEE_APP_URL` and
`DJANGO_API_URL` for the deployed origins.

**Phase 4 is complete. Stop here and wait for explicit approval before
starting Phase 5.**

## Goal

Build the modern, mobile-first attendee experience without destabilizing
the Django organizer/admin application.

## Part A --- API Boundary

Before building the full frontend, expose clean APIs for the attendee
experience.

The API should support the required read/write operations for:

-   Event
-   Event details
-   Registration
-   Attendee profile
-   Employers
-   Jobs
-   Universities
-   Programs
-   Training providers
-   Vouchers
-   Interview slots
-   Interview bookings
-   Sessions
-   Session registration
-   Floor map
-   Booths
-   Check-in
-   Attendee schedule/bookings

Use the existing authentication/permission model where possible.

Do not expose unnecessary internal/admin data.

## Part B --- Next.js Application

Create a separate Next.js attendee frontend.

The attendee experience should be mobile-first.

Suggested routes:

``` text
/
 /register
 /register/success
 /login

 /dashboard
 /dashboard/bookings
 /dashboard/sessions
 /dashboard/saved-jobs

 /employers
 /employers/[id]

 /jobs
 /jobs/[id]

 /universities
 /universities/[id]

 /training-providers
 /training-providers/[id]

 /sessions
 /sessions/[id]

 /floor-map

 /check-in
```

The exact route structure can change if the implementation has a better
architecture.

## Main Attendee Experience

### Event Home

Show:

-   Event information
-   Date/time
-   Venue
-   Key sections
-   UPIKOMing sessions
-   Quick access to map
-   User's bookings

### Agenda

Users should be able to:

-   Browse sessions
-   See time/location
-   See remaining capacity where appropriate
-   Register for sessions

### Floor Map

Users should be able to:

-   View map
-   See booths
-   Search/filter booths
-   Open booth details
-   Identify booth location

### Employers / Jobs

Users should be able to:

-   Browse employers
-   View employer details
-   Browse jobs
-   View job details
-   Save/bookmark jobs where supported

### Interviews

Users should be able to:

-   See available interview slots
-   Book a slot
-   View bookings
-   Cancel where allowed

### Universities

Users should be able to:

-   Browse universities
-   View programs
-   View university details

### Training Providers

Users should be able to:

-   Browse providers
-   View promotions/vouchers
-   Claim/subscribe where supported

### My Schedule

Provide one place for:

-   Interview bookings
-   Session registrations
-   Saved items
-   Relevant event activities

## Phase 4 Deliverables

At the end of Phase 4:

-   Stable backend APIs exist.
-   Next.js attendee application exists.
-   Mobile-first event experience works.
-   Registration works.
-   Sessions work.
-   Floor map works.
-   Booth browsing works.
-   Employer/job browsing works.
-   Interview booking works.
-   University/training flows work.
-   Authentication works.
-   Existing Django organizer flow continues to work.

## Phase 4 Gate

STOP after Phase 4.

Report:

-   API endpoints
-   Authentication approach
-   Next.js structure
-   Pages implemented
-   Main user flows tested
-   Backend/frontend integration status
-   Known issues

**Wait for explicit approval before starting Phase 5.**

------------------------------------------------------------------------

# Phase 5 --- Production Polish, Testing & Cleanup

## Phase 5 Status — Completed 2026-10-07

Phase 5 implementation and its completion gate are complete. Changes include
an end-to-end Django integration test, event directory pagination with a
frontend load-more control, dashboard aggregation, survey-management access
checks and input validation, production-oriented Django environment settings,
and deployment documentation. The legacy Golf navigation was hidden by
default at this point; the GolfEvent workflow and its empty tables were later
removed after confirming the removal scope.

Verification:

- 4 Phase 5 Django tests cover the registration-to-check-in flow, event and
  survey permissions, opt-in Golf navigation, and directory pagination.
- The full Django suite discovered and ran 37 tests; all passed.
- `python manage.py check`: passed with no issues.
- `python manage.py test`: passed (37 tests).
- `git diff --check`: passed.
- `npm run build` in `frontend/`: passed with all attendee routes compiled.
- `npm audit --audit-level=moderate`: passed with 0 vulnerabilities.
- No browser-driven end-to-end test suite exists. Frontend verification is
  the production build, with backend workflows covered by Django API tests.

No Phase 5 database migration was required. No Phase 6 work was started.

**Phase 5 is complete. Stop here for the final implementation report.**

## Goal

Make the complete PIKOM platform reliable and production-ready.

## Scope

### 1. End-to-End Testing

Test the complete flow:

``` text
Organizer creates event
        ↓
Configures registration
        ↓
Configures sessions
        ↓
Configures floor map
        ↓
Creates booths
        ↓
Adds organizations/content
        ↓
Creates interview slots
        ↓
Attendee registers
        ↓
Attendee receives confirmation/QR
        ↓
Attendee browses event
        ↓
Attendee registers for sessions
        ↓
Attendee books interviews
        ↓
Attendee uses floor map
        ↓
Attendee checks in
        ↓
Organizer sees results
```

### 2. Permissions

Verify:

-   Superuser access
-   Organizer access
-   Event-level access
-   Attendee access
-   Public endpoints
-   API authorization

Ensure attendees cannot access organizer functionality.

### 3. Data Validation

Check:

-   Duplicate bookings
-   Session capacity
-   Interview capacity
-   Invalid dates
-   Invalid event state
-   Missing required fields
-   Deleted/inactive entities
-   Unauthorized access

### 4. UI Polish

Polish:

-   Desktop organizer UI
-   Mobile attendee UI
-   Loading states
-   Empty states
-   Error states
-   Form validation
-   Navigation
-   Typography
-   Spacing
-   Consistent components

The goal is to make the product clearly better than the existing version
without introducing unnecessary visual complexity.

### 5. Performance

Review:

-   Database queries
-   N+1 queries
-   Large registration lists
-   API response size
-   Image/file handling
-   Floor-map loading
-   Session/job/organization lists

Add pagination/filtering where appropriate.

### 6. Golf Cleanup

Only after confirming the new PIKOM workflows are stable:

-   Remove obsolete golf navigation.
-   Remove unused golf routes.
-   Remove unused golf templates.
-   Remove unused golf models/code where safe.
-   Remove dead dependencies/configuration if applicable.

Do not delete anything that could affect existing production data
without explicit verification.

### 7. Deployment Readiness

Review:

-   Environment variables
-   Static/media handling
-   Next.js deployment
-   Django deployment
-   API configuration
-   CORS
-   Email configuration
-   Database migrations
-   Logging
-   Error handling

## Phase 5 Deliverables

At the end of Phase 5:

-   Full end-to-end flow works.
-   Critical workflows are tested.
-   Permissions are verified.
-   UI is polished.
-   Performance issues are addressed.
-   Obsolete golf functionality is cleaned up safely.
-   Deployment configuration is documented.
-   No known critical blockers remain.

## Final Gate

After Phase 5, provide a final implementation report containing:

-   What was built
-   Architecture
-   Major models
-   API surface
-   Frontend routes
-   Admin functionality
-   Testing results
-   Known limitations
-   Deployment requirements
-   Recommended future improvements

------------------------------------------------------------------------

# Global Engineering Rules

These rules apply to every phase.

## 1. Preserve Existing Functionality

Do not break existing registration, approval, QR, check-in, email,
reporting, authentication, or permissions functionality.

Before changing existing behavior, understand how it is currently used.

## 2. Inspect Before Implementing

Before making changes in each phase:

1.  Inspect the relevant existing code.
2.  Understand existing models/routes/templates.
3.  Identify reusable functionality.
4.  Identify conflicts.
5.  Then implement.

Do not blindly create duplicate functionality.

## 3. Avoid Unnecessary Rewrites

Prefer:

-   extending existing models
-   adding focused models
-   reusing existing services
-   reusing existing permissions
-   extending existing templates where practical

Avoid rewriting working functionality just for architectural
cleanliness.

## 4. Database Safety

Do not perform destructive migrations casually.

Do not rename or delete existing models/data unless there is a clear
migration strategy.

## 5. Golf Code

Golf functionality should first be hidden/isolated.

Permanent deletion should happen only in Phase 5 after the new platform
has been validated.

## 6. Next.js

Do not introduce Next.js before the backend/domain model and API
boundary are sufficiently stable.

## 7. Tests

Every phase must include automated tests for the functionality introduced
or modified in that phase. Follow the Mandatory Phase Workflow: add/update
tests, run `python manage.py check`, run `python manage.py test`, fix
failures, and report the discovered and executed test count before marking
the phase complete.

At minimum:

-   Existing relevant tests
-   New model tests
-   Business-rule tests
-   Permission tests
-   Critical workflow tests

## 8. No Scope Creep

If the agent discovers something useful but outside the current phase:

-   Do not implement it.
-   Mention it in the phase report.
-   Add it to a "Future / Next Phase" list.

## 9. Stop After Every Phase

This is mandatory.

The agent must never assume approval to continue.

Use this status format at the end of each phase:

``` text
PHASE COMPLETE: Phase X

Implemented:
- ...

Tests:
- ...

Files/areas changed:
- ...

Known issues:
- ...

Deferred:
- ...

NEXT ACTION:
Waiting for explicit approval to begin Phase X+1.
```

------------------------------------------------------------------------

# Phase Sequence

``` text
PHASE 1
Event Management Foundation
        ↓
[USER APPROVAL]
        ↓
PHASE 2
Festival Infrastructure
        ↓
[USER APPROVAL]
        ↓
PHASE 3
Career Festival Backend Modules
        ↓
[USER APPROVAL]
        ↓
PHASE 4
API + Next.js Attendee Experience
        ↓
[USER APPROVAL]
        ↓
PHASE 5
Production Polish, Testing & Cleanup
        ↓
FINAL PRODUCT
```

## Most Important Instruction

**Never move from one phase to the next automatically.**

The user must explicitly approve the next phase.
