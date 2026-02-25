from clients.db import SQLiteClient


def get_last_run_time(task_name):
    db = SQLiteClient()
    result = db.select("task_runs", where="task_name = ?", params=(task_name,))
    if result:
        return result[0].get("last_run_time")

    return None


def update_last_run_time(task_name, run_time):
    db = SQLiteClient()
    existing = db.select("task_runs", where="task_name = ?", params=(task_name,))
    if existing:
        db.execute_query("UPDATE task_runs SET last_run_time = ? WHERE task_name = ?", (run_time, task_name))
    else:
        db.insert("task_runs", {"task_name": task_name, "last_run_time": run_time})
