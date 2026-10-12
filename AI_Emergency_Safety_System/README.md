# AI Emergency Safety System

## 1. Project introduction

**AI Emergency Safety System** is a B.Tech CSE (Artificial Intelligence & Machine Learning) web application. It helps a registered user send an emergency SOS alert to predefined contacts.

When the user presses **SOS**, the browser requests GPS location, the Flask backend saves the event, classifies an **assistance-only risk label** (LOW / MEDIUM / HIGH / CRITICAL), and tries to send SMS (Twilio) and email (SMTP). If Twilio or email credentials are missing, the app **does not crash** and **does not fake a successful send**. It clearly reports **Demo Mode**.

This is an academic demonstration. The machine-learning module is **not** a real-world danger predictor and must never be presented as a substitute for calling local emergency services (for example 112 / 108 / 100 in India).

## 2. Features

- User registration and login with hashed passwords
- Flask session protection for private pages
- Large mobile-friendly **SOS** button with confirmation
- Browser Geolocation (no hard-coded coordinates)
- Google Maps and OpenStreetMap location links
- Interactive Leaflet.js map
- Multiple emergency contacts (add / edit / delete)
- Emergency types and optional description
- SQLite alert history (SMS status, email status, risk label)
- Twilio SMS when configured; otherwise Demo Mode
- SMTP email when configured; otherwise Demo Mode
- Random Forest **Emergency Risk Classification** on a labeled demo dataset
- CSRF protection on forms and the SOS JSON request

## 3. Technology stack

| Layer | Technology |
| --- | --- |
| Language | Python 3 |
| Backend | Flask |
| Database | SQLite |
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5 |
| Maps | Leaflet.js + OpenStreetMap |
| Location | Browser Geolocation API, Geopy (optional reverse geocode) |
| SMS | Twilio REST API |
| Email | Python `smtplib` |
| AI/ML | scikit-learn Random Forest |
| Secrets | `.env` via python-dotenv |

No extra frameworks are required.

## 4. Folder structure

```
AI_Emergency_Safety_System/
├── app.py                 # Flask entry point
├── config.py              # Settings from environment variables
├── database.py            # SQLite connection and schema
├── models.py              # Parameterized data-access queries
├── auth.py                # Register, login, logout
├── emergency.py           # Dashboard, SOS, contacts, history
├── ai_model.py            # Demo dataset, training, risk classification
├── notifications.py       # Twilio SMS and SMTP email (Demo Mode aware)
├── train_model.py         # Rebuild the demo model from the CSV
├── requirements.txt
├── .env.example
├── README.md
├── data/
│   └── emergency_dataset.csv
├── model/
│   └── risk_model.pkl
├── instance/              # Created at runtime (database, local secret)
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── contacts.html
│   ├── history.html
│   ├── emergency.html
│   └── error.html
└── static/
    ├── css/style.css
    └── js/location.js
        dashboard.js
```

## 5. Installation instructions

1. Install **Python 3.10+** (3.11 or 3.12 recommended).
2. Copy this folder onto your computer (or open it in VS Code).
3. Create a virtual environment, install dependencies, then run `app.py` as shown below.

## 6. Python virtual environment setup

From the `AI_Emergency_Safety_System` folder:

```bash
python -m venv venv
```

**Windows:**

```bash
venv\Scripts\activate
```

**macOS / Linux:**

```bash
source venv/bin/activate
```

## 7. Dependency installation

```bash
pip install -r requirements.txt
```

## 8. Database setup

SQLite is created automatically on first run at:

`instance/emergency_safety.db`

Tables:

- `users`
- `emergency_contacts`
- `emergency_alerts`
- `emergency_events` (features used for classification)
- `model_logs` (model output and explanation JSON)

You do **not** need to install a separate database server.

Optional: copy environment defaults:

```bash
cp .env.example .env
```

On Windows (Command Prompt):

```bat
copy .env.example .env
```

## 9. How to run the application

With the virtual environment activated:

```bash
python app.py
```

Then open:

**http://127.0.0.1:5000**

The first start trains the demo Random Forest if `model/risk_model.pkl` is missing and writes `data/emergency_dataset.csv` if needed.

To rebuild the model later:

```bash
python train_model.py
```

## 10. Demo Mode instructions

Leave Twilio and SMTP fields **empty** in `.env`.

Expected behaviour:

- The app starts normally.
- Dashboard shows **SMS Demo Mode** and **Email Demo Mode** badges.
- After SOS, the stored statuses include:
  - `Demo Mode: SMS service is not configured.`
  - `Demo Mode: Email service is not configured.`
- The UI never claims that an SMS or email was actually delivered.

Geolocation still requires browser permission. Use HTTPS or `localhost` (`127.0.0.1`).

## 11. Twilio configuration

1. Create a Twilio account and a phone number that can send SMS.
2. Put values in `.env` (never in source code):

```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890
```

3. Store emergency contact phones in **E.164** form when possible (example: `+919876543210`).
4. Restart `python app.py`.
5. Trial accounts can usually SMS only verified numbers.

If credentials are wrong, the alert is still saved and the SMS status shows the Twilio error. The process does not crash.

## 12. Email configuration

Example for Gmail (use an **App Password**, not your normal password):

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your.address@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your.address@gmail.com
SMTP_USE_TLS=true
```

Contacts without an email address are skipped with a clear status. Missing SMTP settings produce Demo Mode, not a fake “Sent”.

## 13. AI/ML model explanation

The **Emergency Risk Classification** module (`ai_model.py`) trains a **Random Forest** on a **synthetic, clearly labeled demo CSV**.

Features:

| Feature | Meaning |
| --- | --- |
| Emergency type | Medical, Accident, Personal Safety, Fire, Harassment, Other (encoded) |
| SOS attempts | Alerts from this user in the last 24 hours (including the current one) |
| Time of day | Hour 0–23 |
| Previous frequency | Total previous alerts for the user |
| Response status | 0 pending / 1 acknowledged / 2 resolved (0 at send time) |
| User-selected severity | 1 (low) to 5 (extreme) |

Labels in the demo CSV are produced by a **transparent scoring rule** so students can compare rules vs. the forest. Hold-out accuracy is only on this synthetic data.

**Disclaimer (also shown in the UI):** this is an assistance / risk-classification feature. It **cannot reliably predict real-world danger**.

If the pickle file cannot be loaded, a simple fallback rule is used and that fact is recorded.

## 14. How the SOS workflow works

1. User logs in and (optionally) chooses type, severity, and description.
2. User taps **SOS**.
3. Browser asks: *Are you sure you want to send an emergency alert?*
4. If confirmed, Geolocation API returns latitude and longitude (or an error).
5. JavaScript `POST`s JSON to `/sos` with CSRF token.
6. Flask validates coordinates, builds Google Maps / OSM URLs, optionally reverse-geocodes with Geopy.
7. Features are built and the Random Forest returns LOW / MEDIUM / HIGH / CRITICAL.
8. `notifications.py` SMS/emails every contact, or records Demo Mode.
9. Rows are inserted into `emergency_alerts`, `emergency_events`, and `model_logs`.
10. The dashboard shows status, map marker, and recent history.

GPS permission denied, GPS unavailable, and timeouts are handled in `static/js/location.js` without crashing the server.

## 15. Troubleshooting

| Problem | What to try |
| --- | --- |
| `ModuleNotFoundError` | Activate `venv` and run `pip install -r requirements.txt` |
| Port 5000 in use | Stop the other process or change the port in `app.py` |
| Location never appears | Allow location for the site; use `http://127.0.0.1:5000` (not a LAN IP over HTTP) |
| GPS permission denied | Reset site permissions in the browser |
| Duplicate email on register | Use a different email; `users.email` is unique |
| Invalid phone | 10–15 digits, optional `+` |
| CSRF / security check failed | Refresh the page and try again |
| Twilio error in status | Check SID, token, from-number, and destination format |
| Email failed | Check App Password, TLS, and that the contact has an email |
| Model missing | Run `python train_model.py` |
| Database error | Delete `instance/emergency_safety.db` only if you accept losing local data, then restart |

## 16. Future improvements

- Push notifications and live acknowledgement from contacts
- Multi-language UI
- Official emergency-number shortcuts by country
- Wearable / hardware SOS trigger
- Stronger authentication (2FA)
- Encrypted location at rest
- Training on a real, ethically sourced dataset (with clear consent)
- Automated tests and CI

---

## VS Code

1. File → Open Folder → `AI_Emergency_Safety_System`
2. Terminal → New Terminal
3. Run the venv, `pip`, and `python app.py` commands above
4. Open http://127.0.0.1:5000 in a browser

## Security notes

- Passwords are hashed with Werkzeug (`generate_password_hash`)
- All SQL uses placeholders (`?`), never string-formatted queries
- Login is required for dashboard, SOS, contacts, and history
- CSRF tokens protect forms and `/sos`
- Twilio and SMTP secrets belong only in `.env` (gitignored)
- Session cookie is HTTP-only with `SameSite=Lax`

## Academic honesty

State clearly in the report and viva that:

1. The dataset is synthetic and for demonstration.
2. Demo Mode does not send real SMS/email.
3. The classifier is not clinically or legally validated.
4. Real emergencies require calling local emergency services.
