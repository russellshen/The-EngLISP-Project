import os
import sys
import sqlite3
import datetime

LEDGER_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "dataset_tally.sqlite"))

def get_db():
    conn = sqlite3.connect(LEDGER_DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_ledger(total_lines=145437):
    conn = get_db()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sentence_tally (
                line_id INTEGER PRIMARY KEY,
                english TEXT NOT NULL,
                french_target TEXT NOT NULL,
                status TEXT DEFAULT 'UNTOUCHED', -- 'UNTOUCHED', 'ANALYZED', 'FLAGGED'
                tier_label TEXT,
                analyzed_at TEXT,
                base_prediction TEXT,
                base_loss REAL,
                tuned_prediction TEXT,
                tuned_loss REAL,
                loss_reduction REAL,
                diagnosis TEXT,
                pipeline_verified INTEGER DEFAULT 0
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON sentence_tally(status);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tier ON sentence_tally(tier_label);")

    # Check if lines are already populated
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sentence_tally;")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print(f"[*] Initializing ledger with {total_lines} lines from fra.txt...")
        fra_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "fra.txt"))
        rows_to_insert = []
        with open(fra_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                parts = line.split("\t")
                eng = parts[0]
                fr = parts[1] if len(parts) > 1 else ""
                rows_to_insert.append((idx, eng, fr, "UNTOUCHED"))
                if len(rows_to_insert) >= 10000:
                    cursor.executemany(
                        "INSERT INTO sentence_tally (line_id, english, french_target, status) VALUES (?, ?, ?, ?)",
                        rows_to_insert
                    )
                    conn.commit()
                    rows_to_insert = []
                    
        if rows_to_insert:
            cursor.executemany(
                "INSERT INTO sentence_tally (line_id, english, french_target, status) VALUES (?, ?, ?, ?)",
                rows_to_insert
            )
            conn.commit()
        print(f"[SUCCESS] Ledger initialized with {total_lines} entries.")
    conn.close()

def record_evaluation(line_id, base_pred, base_loss, tuned_pred, tuned_loss, diagnosis, tier_label="Tier 1", verified=1):
    conn = get_db()
    reduction = round(base_loss - tuned_loss, 4)
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with conn:
        conn.execute("""
            UPDATE sentence_tally
            SET status = 'ANALYZED',
                tier_label = ?,
                analyzed_at = ?,
                base_prediction = ?,
                base_loss = ?,
                tuned_prediction = ?,
                tuned_loss = ?,
                loss_reduction = ?,
                diagnosis = ?,
                pipeline_verified = ?
            WHERE line_id = ?
        """, (tier_label, now_str, base_pred, base_loss, tuned_pred, tuned_loss, reduction, diagnosis, verified, line_id))
    conn.close()

def get_ledger_summary():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sentence_tally WHERE status = 'ANALYZED'")
    analyzed = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM sentence_tally WHERE status = 'UNTOUCHED'")
    untouched = cursor.fetchone()[0]
    cursor.execute("SELECT AVG(base_loss), AVG(tuned_loss) FROM sentence_tally WHERE status = 'ANALYZED'")
    avg_base, avg_tuned = cursor.fetchone()
    
    cursor.execute("""
        SELECT tier_label, COUNT(*), AVG(base_loss), AVG(tuned_loss), AVG(loss_reduction)
        FROM sentence_tally
        WHERE status = 'ANALYZED'
        GROUP BY tier_label
    """)
    tier_stats = cursor.fetchall()
    conn.close()
    
    return {
        "analyzed_count": analyzed,
        "untouched_count": untouched,
        "total": analyzed + untouched,
        "avg_base_loss": avg_base if avg_base is not None else 0.0,
        "avg_tuned_loss": avg_tuned if avg_tuned is not None else 0.0,
        "tier_stats": tier_stats
    }

if __name__ == "__main__":
    init_ledger()
    summary = get_ledger_summary()
    print("Ledger Status:", summary)
