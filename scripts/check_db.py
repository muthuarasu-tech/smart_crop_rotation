import sqlite3

conn = sqlite3.connect("database/crop_rotation.db")
rows = conn.execute(
    "SELECT name FROM sqlite_master WHERE type = ?", ("table",)
).fetchall()
print("tables:", [r[0] for r in rows])

mr = conn.execute(
    "SELECT model_name, round(accuracy * 100, 1), is_best FROM model_results ORDER BY is_best DESC"
).fetchall()
print("model_results:", mr)
conn.close()