"""
Local SQLite-backed database adapter for NexaRoll AI.
Provides seamless fallback when Supabase credentials are not yet configured,
implementing the exact same .table().select().eq().execute() API.
"""

import sqlite3
import json
import os
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "attendance_local.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_local_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                name TEXT NOT NULL,
                face_embedding TEXT,
                voice_embedding TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER,
                subject_code TEXT NOT NULL,
                name TEXT NOT NULL,
                section TEXT NOT NULL,
                teacher_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subject_students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                is_present INTEGER DEFAULT 1,
                type TEXT DEFAULT 'photo',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

class QueryResponse:
    def __init__(self, data):
        self.data = data

class LocalTableQuery:
    def __init__(self, table_name):
        self.table_name = table_name
        self.select_columns = "*"
        self.filters = []
        self.insert_data = None
        self.delete_mode = False
        self.limit_count = None
        self.order_by = None

    def select(self, columns="*"):
        self.select_columns = columns
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def ilike(self, column, value):
        val_str = str(value).lower() if value is not None else ""
        self.filters.append((f"LOWER({column})", val_str))
        return self


    def limit(self, count):
        self.limit_count = count
        return self

    def order(self, column, desc=False):
        self.order_by = (column, desc)
        return self

    def insert(self, data):
        self.insert_data = data
        return self

    def update(self, data):
        self.update_data = data
        return self

    def delete(self):
        self.delete_mode = True
        return self


    def execute(self):
        init_local_db()
        with get_connection() as conn:
            cursor = conn.cursor()

            # Handle UPDATE
            if hasattr(self, 'update_data') and self.update_data is not None:
                where_clauses = [f"{col} = ?" for col, _ in self.filters]
                where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
                set_clauses = [f"{col} = ?" for col in self.update_data.keys()]
                sql = f"UPDATE {self.table_name} SET {', '.join(set_clauses)}{where_sql}"
                params = list(self.update_data.values()) + [val for _, val in self.filters]
                cursor.execute(sql, params)
                conn.commit()
                cursor.execute(f"SELECT * FROM {self.table_name}{where_sql}", [val for _, val in self.filters])
                return QueryResponse([dict(r) for r in cursor.fetchall()])

            # Handle INSERT
            if self.insert_data is not None:
                records = self.insert_data if isinstance(self.insert_data, list) else [self.insert_data]

                inserted_rows = []
                for rec in records:
                    rec_copy = dict(rec)
                    # Convert list/dict embeddings to JSON strings
                    for k in ["face_embedding", "voice_embedding"]:
                        if k in rec_copy and rec_copy[k] is not None and not isinstance(rec_copy[k], str):
                            rec_copy[k] = json.dumps(rec_copy[k])

                    cols = list(rec_copy.keys())
                    placeholders = ", ".join(["?"] * len(cols))
                    sql = f"INSERT INTO {self.table_name} ({', '.join(cols)}) VALUES ({placeholders})"
                    cursor.execute(sql, list(rec_copy.values()))
                    row_id = cursor.lastrowid
                    
                    # Ensure primary key aliases like student_id / teacher_id / subject_id are set
                    if self.table_name == "teachers":
                        cursor.execute("UPDATE teachers SET teacher_id = ? WHERE id = ?", (row_id, row_id))
                        rec_copy["teacher_id"] = row_id
                    elif self.table_name == "students":
                        cursor.execute("UPDATE students SET student_id = ? WHERE id = ?", (row_id, row_id))
                        rec_copy["student_id"] = row_id
                    elif self.table_name == "subjects":
                        cursor.execute("UPDATE subjects SET subject_id = ? WHERE id = ?", (row_id, row_id))
                        rec_copy["subject_id"] = row_id
                    
                    rec_copy["id"] = row_id
                    inserted_rows.append(rec_copy)

                conn.commit()
                return QueryResponse(inserted_rows)

            # Handle DELETE
            if self.delete_mode:
                where_clauses = [f"{col} = ?" for col, _ in self.filters]
                where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
                params = [val for _, val in self.filters]
                if self.table_name == "subjects":
                    cursor.execute(f"SELECT id, subject_id FROM subjects{where_sql}", params)
                    deleted_subs = cursor.fetchall()
                    for sub_row in deleted_subs:
                        sid = sub_row["subject_id"] if "subject_id" in sub_row.keys() else sub_row["id"]
                        cursor.execute("DELETE FROM subject_students WHERE subject_id = ?", (sid,))
                        cursor.execute("DELETE FROM attendance_logs WHERE subject_id = ?", (sid,))
                cursor.execute(f"DELETE FROM {self.table_name}{where_sql}", params)
                conn.commit()
                return QueryResponse([])

            # Handle SELECT
            where_clauses = [f"{col} = ?" for col, _ in self.filters]
            where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            params = [val for _, val in self.filters]

            # Special join handling for subjects & attendance
            if self.table_name == "subjects" and "subject_students" in self.select_columns:
                cursor.execute(f"SELECT * FROM subjects{where_sql}", params)
                rows = [dict(r) for r in cursor.fetchall()]
                for s in rows:
                    sid = s.get("subject_id") or s.get("id")
                    cursor.execute("SELECT COUNT(*) as count FROM subject_students WHERE subject_id = ?", (sid,))
                    st_count = cursor.fetchone()["count"]
                    s["subject_students"] = [{"count": st_count}]
                    cursor.execute("SELECT timestamp FROM attendance_logs WHERE subject_id = ?", (sid,))
                    att_rows = [dict(r) for r in cursor.fetchall()]
                    s["attendance_logs"] = att_rows
                return QueryResponse(rows)

            if self.table_name == "subject_students" and "subjects(*)" in self.select_columns:
                cursor.execute(f"SELECT * FROM subject_students{where_sql}", params)
                ss_rows = [dict(r) for r in cursor.fetchall()]
                valid_rows = []
                for ss in ss_rows:
                    cursor.execute("SELECT * FROM subjects WHERE id = ? OR subject_id = ?", (ss["subject_id"], ss["subject_id"]))
                    subj = cursor.fetchone()
                    if subj:
                        ss["subjects"] = dict(subj)
                        valid_rows.append(ss)
                if self.limit_count is not None:
                    valid_rows = valid_rows[:self.limit_count]
                return QueryResponse(valid_rows)

            if self.table_name == "subject_students" and "students(*)" in self.select_columns:
                cursor.execute(f"SELECT * FROM subject_students{where_sql}", params)
                ss_rows = [dict(r) for r in cursor.fetchall()]
                valid_rows = []
                for ss in ss_rows:
                    cursor.execute("SELECT * FROM students WHERE student_id = ?", (ss["student_id"],))
                    st_row = cursor.fetchone()
                    if st_row:
                        st_dict = dict(st_row)
                        for k in ["face_embedding", "voice_embedding"]:
                            if k in st_dict and st_dict[k] and isinstance(st_dict[k], str):
                                try:
                                    st_dict[k] = json.loads(st_dict[k])
                                except Exception:
                                    pass
                        ss["students"] = st_dict
                        valid_rows.append(ss)
                if self.limit_count is not None:
                    valid_rows = valid_rows[:self.limit_count]
                return QueryResponse(valid_rows)



            if self.table_name == "attendance_logs" and "subjects(*)" in self.select_columns:
                cursor.execute(f"SELECT * FROM attendance_logs{where_sql}", params)
                att_rows = [dict(r) for r in cursor.fetchall()]
                for att in att_rows:
                    cursor.execute("SELECT * FROM subjects WHERE id = ? OR subject_id = ?", (att["subject_id"], att["subject_id"]))
                    subj = cursor.fetchone()
                    att["subjects"] = dict(subj) if subj else {}
                return QueryResponse(att_rows)

            cursor.execute(f"SELECT * FROM {self.table_name}{where_sql}", params)
            rows = [dict(r) for r in cursor.fetchall()]
            
            # Decode JSON embeddings
            for r in rows:
                for k in ["face_embedding", "voice_embedding"]:
                    if k in r and r[k] and isinstance(r[k], str):
                        try:
                            r[k] = json.loads(r[k])
                        except Exception:
                            pass
                if "is_present" in r:
                    r["is_present"] = bool(r["is_present"])

            if self.limit_count is not None:
                rows = rows[:self.limit_count]

            return QueryResponse(rows)


class LocalSupabaseClient:
    def table(self, table_name):
        return LocalTableQuery(table_name)

_local_client = None

def get_local_client():
    global _local_client
    if _local_client is None:
        init_local_db()
        _local_client = LocalSupabaseClient()
    return _local_client
