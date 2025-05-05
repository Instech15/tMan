import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="users_tasks.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Create the `users` table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )''')

        # Create the `tasks` table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT,
            note_tag TEXT,
            date TEXT,
            priority TEXT,
            due_date TEXT,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')

        # Add the 'completed' column if it doesn't exist
        try:
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN completed INTEGER DEFAULT 0")
            print("Added 'completed' column to 'tasks' table.")
        except sqlite3.OperationalError:
            print("'completed' column already exists.")

        self.conn.commit()

    def add_user(self, username, password):
        try:
            self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            self.conn.commit()
            print("User added successfully.")
        except sqlite3.IntegrityError:
            print("Username already exists.")
        except Exception as e:
            print(f"Error adding user: {e}")

    def add_task(self, user_id, content, note_tag="general", priority="medium", due_date=None):
        try:
            date_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute(
                "INSERT INTO tasks (user_id, content, note_tag, date, priority, due_date) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, content, note_tag, date_created, priority, due_date)
            )
            self.conn.commit()
            print("Task added successfully.")
        except Exception as e:
            print(f"Error adding task: {e}")

    def get_tasks(self, user_id):
        try:
            self.cursor.execute("SELECT id, content, note_tag, date, priority, due_date, completed FROM tasks WHERE user_id=?", (user_id,))
            tasks = self.cursor.fetchall()
            return tasks
        except Exception as e:
            print(f"Error fetching tasks: {e}")
            return []

    def update_task(self, task_id, content=None, note_tag=None, priority=None, due_date=None):
        try:
            if content:
                self.cursor.execute("UPDATE tasks SET content=? WHERE id=?", (content, task_id))
            if note_tag:
                self.cursor.execute("UPDATE tasks SET note_tag=? WHERE id=?", (note_tag, task_id))
            if priority:
                self.cursor.execute("UPDATE tasks SET priority=? WHERE id=?", (priority, task_id))
            if due_date:
                self.cursor.execute("UPDATE tasks SET due_date=? WHERE id=?", (due_date, task_id))
            self.conn.commit()
            print(f"Task {task_id} updated successfully.")
        except Exception as e:
            print(f"Error updating task: {e}")

    def delete_task(self, task_id):
        try:
            self.cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            self.conn.commit()
            print(f"Task {task_id} deleted successfully.")
        except Exception as e:
            print(f"Error deleting task: {e}")

    def mark_task_completed(self, task_id):
        try:
            self.cursor.execute("UPDATE tasks SET completed=1 WHERE id=?", (task_id,))
            self.conn.commit()
            print(f"Task {task_id} marked as completed.")
        except Exception as e:
            print(f"Error marking task as completed: {e}")

    def close_connection(self):
        self.conn.close()