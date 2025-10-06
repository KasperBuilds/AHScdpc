# AHS × CDPC Résumé Review Queue

A collaboration between the **Alexander Hamilton Society (AHS)** and the **Carnegie Mellon Career and Professional Development Center (CDPC)**.  
This web app provides a simple queue system for students to submit their résumés for review during the **CDPC Résumé Review Workshop**.

Built using **Flask**, it allows students to upload their résumé files and instructors to view and manage submissions in real time.

---

## 🎯 Purpose

This project was created to streamline in-person résumé review sessions, ensuring:

- Students can check in easily and upload their résumés.
- CDPC reviewers and AHS organisers can track submissions live.
- Reviews happen efficiently without manual paper lists or confusion.

---

## 🧩 Features

- **Student submission form**: Name, question or comment, résumé upload (PDF/DOCX).  
- **Instructor dashboard**: Live-updating queue of students and downloadable résumés.  
- **Queue management**: Mark as *helping* or *done* in real time.  
- **Automatic refresh**: Instructor dashboard updates automatically every few seconds.  
- **Secure instructor login** using a secret access code.  
- **Lightweight and deployment-ready** on [Railway](https://railway.app).

---

## ⚙️ Tech Stack

| Component | Technology |
|------------|-------------|
| Framework | Flask |
| Database | SQLite (local) or Railway-hosted |
| Frontend | HTML + Bootstrap (Jinja templates) |
| Hosting | Railway.app |
| File uploads | Local `/uploads` directory |

---

## 🖥️ Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/KasperBuilds/AHScdpc.git
cd AHScdpc
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set environment variables
```bash
export APP_SECRET="dev-secret"
export INSTRUCTOR_CODE="letmein"
```

### 5. Run the app
```bash
python3 app.py
```

Then visit **http://localhost:5000** in your browser.

---

## 🚀 Deployment on Railway

1. Push your repository to GitHub.  
2. Go to [Railway](https://railway.app) → **New Project → Deploy from GitHub**.  
3. Add these variables under **Settings → Variables**:
   - `APP_SECRET` → long random string (session key)
   - `INSTRUCTOR_CODE` → code for instructor login access
4. Railway automatically builds and serves your Flask app.  
5. Once deployed, your live URL will look like:
   ```
   https://ahs-cdpc-review.up.railway.app
   ```

---

## 🔐 Security Notes

- Do **not** commit your `queue.db` or uploaded résumés to GitHub.  
- Sensitive and runtime data are excluded via `.gitignore`:
  ```
  queue.db
  uploads/
  venv/
  __pycache__/
  ```
- Keep `APP_SECRET` private — it encrypts and signs user sessions.

---

## 🧠 Example Routes

| Page | Route |
|------|-------|
| Student queue | `/` |
| Instructor login | `/login` |
| Instructor dashboard | `/dashboard` (or `/instructor`, depending on config) |

---

## 🤝 Credits

Developed for the  
**AHS × CDPC Résumé Review Workshop**  
Carnegie Mellon University, 2025

**Contributors**
- Alexander Hamilton Society (CMU Chapter)  
- Career and Professional Development Center (CDPC)  
- Project maintained by **Kasper Hong**

---

## 📧 Contact

For collaboration or technical inquiries, reach out to the AHS CMU organising committee
