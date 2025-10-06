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
- **Automatic refresh**: The instructor dashboard updates automatically every few seconds.  
- **Secure instructor login** using a secret code.  
- **Lightweight deployment** on [Railway](https://railway.app).

---

## ⚙️ Tech Stack

| Component | Technology |
|------------|-------------|
| Framework | Flask |
| Database | SQLite (local) / Railway-hosted |
| Frontend | HTML + Bootstrap (Jinja templates) |
| Hosting | Railway.app |
| File uploads | Local `/uploads` directory |

---

## 🖥️ Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/KasperBuilds/AHScdpc.git
cd AHScdpc
