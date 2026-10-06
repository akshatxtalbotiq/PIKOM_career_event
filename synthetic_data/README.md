# Synthetic showcase data

From the repository root, run:

```bash
python manage.py migrate
python synthetic_data/seed.py
python manage.py runserver
```

The script creates or updates one clearly named showcase event and related
records for registration forms and answers, organizer access, attendees in
pending/approved/rejected states, QR/check-in status, employers and jobs,
bookmarks, sessions and bookings, an interactive floor map, interview slots,
university programs, and training promotions/claims. It creates the floor map
image under `MEDIA_ROOT/synthetic_data/` so the map renders in the attendee
app.

The script is repeatable: it reuses stable event, attendee, and content names,
does not duplicate the seeded records, and never deletes records. Run it only
against a development database; it refuses to run when `DJANGO_DEBUG=false`.
All records use synthetic names and `.test` email addresses.

After seeding, open the Django organizer UI at <http://127.0.0.1:8000/login/>.
The demo organizer credentials are printed by the script:

- Username: `synthetic.organizer`
- Password on first creation: `SyntheticDemo2026!`

The organizer is added to the showcase event's team. Existing organizer
passwords are never changed if that account already exists. The script also
prints attendee bearer tokens for trying the attendee API directly. The public
registration form is at the URL printed at the end of the run.

For the Next.js attendee app, start Django, set `DJANGO_API_URL` in
`frontend/.env.local` as described in the root README, then run `npm run dev`
from `frontend/`. Use one of the printed approved attendee tokens through the
attendee API; the app's public registration flow also returns a token and signs
in the registering browser.
