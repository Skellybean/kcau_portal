# KCA Virtual Campus and Students Portal (STU 701)

Mobile app (React Native, Expo) with a Django REST backend. All data is sample data.

## How access works

- **KCA emails only.** Sign-up and sign-in accept `@students.kcau.ac.ke` (students) and `@kcau.ac.ke` (lecturers). The check is an exact match on the domain, so `name@kcau.ac.ke.evil.com` and `name@gmail.com` are refused. The server enforces it; the app repeats it for instant feedback.
- **Email verification.** Registering sends a 6-digit code to the KCA inbox (hashed in the database, expires in 15 minutes, locks after 5 wrong tries). An account cannot sign in until it is verified.
- **Roles come from the email domain**, never from the request. Administrators are created with `createsuperuser` or in the admin site.
- **Units come from the KCA portal.** Students register for units, per trimester, on the portal. The Virtual Campus does not let students enrol themselves. It shows what the portal sends (see "Portal registrations").

## Run the backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo            # sample users, units, timetable, results, notices, facilities
python manage.py createsuperuser      # use a @kcau.ac.ke address
python manage.py runserver 0.0.0.0:8000
python manage.py test                 # 42 tests
```

Verification codes print in the terminal while no SMTP server is configured.
Admin site: http://localhost:8000/admin/

Demo accounts (already verified), password `Campus#Demo2026`:

| Role | Email |
|---|---|
| Student | demo.student1@students.kcau.ac.ke |
| Lecturer | demo.lecturer1@kcau.ac.ke |
| Administrator | demo.admin@kcau.ac.ke |

## Run the mobile app

```bash
cd mobile
cp .env.example .env        # set EXPO_PUBLIC_API_URL
npm install
npx expo start
```

Android emulator reaches your computer at `http://10.0.2.2:8000`. A physical phone needs your computer's LAN address (for example `http://192.168.1.20:8000`) and the phone on the same Wi-Fi. Open the app with Expo Go or a development build.

## Portal registrations

Set `CURRENT_TRIMESTER` to the portal's wording (default `2026 Trimester 3`). The timetable, My Units and dashboard show the current trimester's registrations only.

1. **Portal push (API).** Set `PORTAL_SYNC_KEY`, then the portal sends:

   ```
   POST /api/portal/registrations/
   X-Portal-Key: <PORTAL_SYNC_KEY>

   {"registrations": [
     {"email": "jane@students.kcau.ac.ke", "unit_code": "DIT 201",
      "trimester": "2026 Trimester 3", "action": "register"}
   ]}
   ```

   `action` is `register` (default) or `drop`. Up to 1000 rows per call; the reply lists a status per row. A student who has not created an account yet is held as a pending registration and applied when they verify their email.
2. **CSV import.** `python manage.py import_registrations file.csv` with columns `email,unit_code,trimester[,action]`.
3. **Admin site.** Add or remove Enrollment rows by hand.

Unit codes must already exist as Units (add them in the admin site).

## Deploy (Render + Supabase)

1. Create a Supabase project and copy its PostgreSQL connection string into `DATABASE_URL`.
2. Create a Render web service from this repository using `render.yaml`, then fill in `DJANGO_ALLOWED_HOSTS`. See `backend/.env.example` for every variable.
3. Configure SMTP (`EMAIL_HOST` and related) so verification codes reach real inboxes.
4. Point `EXPO_PUBLIC_API_URL` at the Render URL.

Do not run `seed_demo` against production.

## API summary

| Endpoint | Who |
|---|---|
| `POST /api/auth/register/`, `verify/`, `resend-code/`, `login/`, `password-reset/`, `password-reset/confirm/` | Public, KCA emails only |
| `GET/PATCH /api/auth/me/`, `POST /api/auth/logout/` | Signed in |
| `GET /api/dashboard/` | Signed in |
| `GET /api/units/?mine=1`, `/api/timetable/`, `/api/results/`, `/api/announcements/`, `/api/facilities/` | Signed in, scoped by role |
| `POST/PATCH/DELETE /api/units/`, `/api/timetable/`, `/api/facilities/` | Administrators |
| `POST/PATCH/DELETE /api/results/` | Lecturers (own units) and administrators |
| `POST /api/announcements/` | Lecturers and administrators (only administrators can pin) |
| `POST /api/portal/registrations/` | KCA portal, with `X-Portal-Key` |

## Online and hybrid classes

Each timetable slot is **In person**, **Online** or **Hybrid**. Online and hybrid slots can carry a class link (https only) and an optional passcode or instructions.

- Students registered for a unit see a **Join class** button on the Timetable, Home (next class) and Unit screens. Students who are not registered never receive the link.
- A lecturer opens a slot of a unit they teach and taps **Edit class link** to change the mode, link and passcode. Lecturers cannot change times, venues or other lecturers' slots.
- Administrators can create slots and set all fields in the admin site.
- An online class needs no venue and may be created before its link exists; students then see "The lecturer has not posted the class link yet." In-person and hybrid classes need a venue.

After pulling this update run `python manage.py migrate`. `python manage.py seed_demo` refreshes the demo slots (DIT 210 online, DIT 214 hybrid).

## Known limits

- Lecturers record results through the API or admin site; the app has no results-entry screen.
- The student email domain (`students.kcau.ac.ke`) is an assumption. If KCA uses a different one, change `KCA_STUDENT_EMAIL_DOMAINS` on the backend and `STUDENT_EMAIL_DOMAINS` in `mobile/src/config.js`.
- The mobile app was bundled and the backend tested here, but the app has not been run on a device or emulator.
