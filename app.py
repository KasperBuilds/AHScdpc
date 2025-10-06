import os
import sqlite3
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, abort, flash, jsonify, send_from_directory
)

APP_SECRET = os.environ.get("APP_SECRET", "dev-secret")
INSTRUCTOR_CODE = os.environ.get("INSTRUCTOR_CODE", "letmein")

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "queue.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTS = {"pdf", "doc", "docx"}
MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB

app = Flask(__name__)
app.secret_key = APP_SECRET
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db():
    con = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = get_db()
    cur = con.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS queues(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course TEXT NOT NULL,
            is_open INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS questions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            queue_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            -- replaced topic and location with question_body
            question_body TEXT NOT NULL,
            resume_filename TEXT,  -- stored server-side file name
            resume_orig_name TEXT, -- original file name for display
            status TEXT NOT NULL DEFAULT 'waiting', -- waiting, helping, done, cancelled
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            finished_at TIMESTAMP,
            FOREIGN KEY(queue_id) REFERENCES queues(id)
        );
        """
    )
    con.commit()
    # migrate older DBs that still have topic/location columns
    # add columns if missing
    def col_exists(tbl, col):
        r = cur.execute("PRAGMA table_info(%s)" % tbl).fetchall()
        return any(c[1] == col for c in r)

    if not col_exists("questions", "question_body"):
        # create a new column and copy a best-effort value from existing fields
        cur.execute("ALTER TABLE questions ADD COLUMN question_body TEXT")
        cur.execute("UPDATE questions SET question_body = COALESCE(body, topic || ' @ ' || COALESCE(location,''))")
        con.commit()
    if not col_exists("questions", "resume_filename"):
        cur.execute("ALTER TABLE questions ADD COLUMN resume_filename TEXT")
        con.commit()
    if not col_exists("questions", "resume_orig_name"):
        cur.execute("ALTER TABLE questions ADD COLUMN resume_orig_name TEXT")
        con.commit()

    # seed a default queue if none
    cur.execute("SELECT COUNT(*) as c FROM queues")
    if cur.fetchone()["c"] == 0:
        cur.execute("INSERT INTO queues(course, is_open) VALUES(?, ?)", ("AHS Resume Review Workshop", 1))
        con.commit()
    con.close()


with app.app_context():
    init_db()


def current_queue():
    con = get_db()
    q = con.execute("SELECT * FROM queues ORDER BY id DESC LIMIT 1").fetchone()
    con.close()
    return q


def average_wait_minutes(queue_id, window_hours=6):
    con = get_db()
    rows = con.execute(
        """
        SELECT julianday(COALESCE(started_at, CURRENT_TIMESTAMP)) - julianday(created_at) AS d
        FROM questions
        WHERE queue_id = ? AND status IN ('helping','done')
          AND created_at >= datetime('now', ?)
        """,
        (queue_id, f"-{window_hours} hours"),
    ).fetchall()
    con.close()
    if not rows:
        return 0
    total_mins = sum(r["d"] * 24 * 60 for r in rows)
    return round(total_mins / len(rows))


def require_instructor():
    if session.get("role") != "instructor":
        abort(403)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTS


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name", "").strip() or "Guest"
        code = request.form.get("code", "")
        if code == INSTRUCTOR_CODE:
            session["role"] = "instructor"
            session["name"] = name
            return redirect(url_for("instructor"))
        flash("Incorrect code")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/")
def index():
    q = current_queue()
    con = get_db()
    my_name = session.get("name")
    my_qs = []
    if my_name:
        my_qs = con.execute(
            "SELECT id, question_body, status, created_at FROM questions WHERE queue_id=? AND name=? ORDER BY created_at DESC LIMIT 5",
            (q["id"], my_name),
        ).fetchall()
    con.close()
    avg_wait = average_wait_minutes(q["id"])
    waiting_count = queue_counts(q["id"])["waiting"]
    return render_template("index.html", q=q, avg_wait=avg_wait, waiting_count=waiting_count, my_qs=my_qs)


@app.route("/ask", methods=["POST"])
def ask():
    q = current_queue()
    if not q["is_open"]:
        flash("The queue is closed")
        return redirect(url_for("index"))

    name = request.form.get("name", "").strip() or "Anon"
    question_body = request.form.get("question_body", "").strip()
    if not question_body:
        flash("Please enter your question")
        return redirect(url_for("index"))

    session["name"] = name

    resume_file = request.files.get("resume")
    stored_name = None
    orig_name = None
    if resume_file and resume_file.filename:
        if not allowed_file(resume_file.filename):
            flash("File type not allowed. Upload pdf, doc, or docx.")
            return redirect(url_for("index"))
        orig_name = resume_file.filename
        # store using a unique server-side name
        ext = orig_name.rsplit(".", 1)[1].lower()
        stored_name = f"{name.replace(' ', '_')}_{str(q['id'])}_{str(os.getpid())}_{str(os.urandom(3).hex())}.{ext}"
        resume_file.save(os.path.join(UPLOAD_FOLDER, stored_name))

    con = get_db()
    con.execute(
        """
        INSERT INTO questions(queue_id, name, question_body, resume_filename, resume_orig_name)
        VALUES(?,?,?,?,?)
        """,
        (q["id"], name, question_body, stored_name, orig_name),
    )
    con.commit()
    con.close()
    return redirect(url_for("index"))


def queue_counts(queue_id):
    con = get_db()
    c = {}
    for s in ("waiting", "helping", "done", "cancelled"):
        c[s] = (
            con.execute("SELECT COUNT(*) AS c FROM questions WHERE queue_id=? AND status=?", (queue_id, s))
            .fetchone()["c"]
        )
    con.close()
    return c


@app.route("/instructor")
def instructor():
    require_instructor()
    q = current_queue()
    con = get_db()
    qs = con.execute(
        """
        SELECT id, name, question_body, resume_filename, resume_orig_name, status, created_at
        FROM questions
        WHERE queue_id=? AND status IN ('waiting','helping')
        ORDER BY created_at
        """,
        (q["id"],),
    ).fetchall()
    counts = queue_counts(q["id"])
    avg_wait = average_wait_minutes(q["id"])
    con.close()
    return render_template("instructor.html", q=q, qs=qs, counts=counts, avg_wait=avg_wait)


@app.route("/toggle_queue", methods=["POST"])
def toggle_queue():
    require_instructor()
    q = current_queue()
    new_state = 0 if q["is_open"] else 1
    con = get_db()
    con.execute("UPDATE queues SET is_open=? WHERE id=?", (new_state, q["id"]))
    con.commit()
    con.close()
    return redirect(url_for("instructor"))


@app.route("/question/<int:qid>/start", methods=["POST"])
def start_help(qid):
    require_instructor()
    con = get_db()
    con.execute(
        "UPDATE questions SET status='helping', started_at=CURRENT_TIMESTAMP WHERE id=? AND status='waiting'", (qid,)
    )
    con.commit()
    con.close()
    return redirect(url_for("instructor"))


@app.route("/question/<int:qid>/done", methods=["POST"])
def done(qid):
    require_instructor()
    con = get_db()
    con.execute(
        "UPDATE questions SET status='done', finished_at=CURRENT_TIMESTAMP WHERE id=? AND status IN ('waiting','helping')",
        (qid,),
    )
    con.commit()
    con.close()
    return redirect(url_for("instructor"))


@app.route("/question/<int:qid>/cancel", methods=["POST"])
def cancel(qid):
    require_instructor()
    con = get_db()
    con.execute(
        "UPDATE questions SET status='cancelled', finished_at=CURRENT_TIMESTAMP WHERE id=? AND status IN ('waiting','helping')",
        (qid,),
    )
    con.commit()
    con.close()
    return redirect(url_for("instructor"))


# ---------- APIs for live updates ----------

@app.route("/api/stats")
def api_stats():
    q = current_queue()
    counts = queue_counts(q["id"])
    return jsonify(
        {
            "queue": {"course": q["course"], "is_open": bool(q["is_open"])},
            "counts": counts,
            "avg_wait_minutes": average_wait_minutes(q["id"]),
        }
    )


@app.route("/api/queue")
def api_queue():
    q = current_queue()
    con = get_db()
    rows = con.execute(
        """
        SELECT id, name, question_body, resume_filename, resume_orig_name, status, created_at
        FROM questions
        WHERE queue_id=? AND status IN ('waiting','helping')
        ORDER BY created_at
        """,
        (q["id"],),
    ).fetchall()
    con.close()
    return jsonify([dict(r) for r in rows])


# ---------- safe résumé download ----------
@app.route("/download/<int:qid>")
def download_resume(qid):
    require_instructor()
    con = get_db()
    r = con.execute(
        "SELECT resume_filename, resume_orig_name FROM questions WHERE id=?", (qid,)
    ).fetchone()
    con.close()
    if not r or not r["resume_filename"]:
        abort(404)
    return send_from_directory(
        UPLOAD_FOLDER, r["resume_filename"], as_attachment=True, download_name=r["resume_orig_name"] or "resume"
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
