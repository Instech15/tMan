import sqlite3
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivymd.uix.list import TwoLineListItem
from kivymd.uix.button import MDRaisedButton
from datetime import datetime
from kivy.clock import Clock
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from calendar import monthrange
from dotenv import load_dotenv
load_dotenv()

# Email Configuration
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Screen Classes
class LoginScreen(Screen): pass
class SignupScreen(Screen): pass
class TaskManagerScreen(Screen): pass
class AddTaskScreen(Screen): pass
class ProfileScreen(Screen): pass

class CalendarScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_date = None

    def create_calendar(self, year, month):
        self.clear_widgets()  # Clear any existing widgets
        layout = GridLayout(cols=7, padding=10, spacing=5)

        # Adjust the month and year for navigation
        if month < 1:  # If navigating to a previous year
            month = 12
            year -= 1
        elif month > 12:  # If navigating to the next year
            month = 1
            year += 1

        # Add navigation buttons and display the current month and year
        nav_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=60, spacing=10)
        prev_button = Button(
            text="<",
            size_hint=(None, None),
            size=(50, 50),
            on_release=lambda x: self.create_calendar(year, month - 1)
        )
        next_button = Button(
            text=">",
            size_hint=(None, None),
            size=(50, 50),
            on_release=lambda x: self.create_calendar(year, month + 1)
        )
        month_label = Label(
            text=f"{datetime(year, month, 1).strftime('%B %Y')}",  # Display month name and year
            size_hint=(1, None),  # Take up remaining horizontal space
            height=50,
            halign="center",
            valign="middle",
            color=(0, 0, 0, 1)  # Black text color
        )
        month_label.bind(size=month_label.setter("text_size"))  # Ensure text is centered
        back_button = Button(
            text="Back",
            size_hint=(None, None),
            size=(100, 50),
            on_release=lambda x: self.go_back()
        )
        nav_layout.add_widget(prev_button)
        nav_layout.add_widget(month_label)
        nav_layout.add_widget(next_button)
        nav_layout.add_widget(back_button)
        self.add_widget(nav_layout)

        # Add day headers
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for day in days:
            layout.add_widget(Button(text=day, size_hint=(None, None), size=(50, 50), background_color=(0.8, 0.8, 0.8, 1)))

        # Get the first day of the month and the number of days in the month
        first_day, num_days = monthrange(year, month)

        # Fetch tasks for the current month
        app = MDApp.get_running_app()
        app.cursor.execute("SELECT due_date FROM tasks WHERE user_id=?", (app.user_id,))
        task_dates = [datetime.strptime(row[0], "%Y-%m-%d").date() for row in app.cursor.fetchall() if row[0]]

        # Add empty buttons for days before the first day of the month
        for _ in range(first_day):
            layout.add_widget(Button(disabled=True, background_color=(0, 0, 0, 0)))

        # Add buttons for each day of the month
        for day in range(1, num_days + 1):
            current_date = datetime(year, month, day).date()
            if current_date in task_dates:
                btn_color = (0, 0, 1, 1)  # Days with tasks (blue)
            elif current_date < datetime.now().date():
                btn_color = (1, 0, 0, 1)  # Overdue tasks (red)
            else:
                btn_color = (0, 1, 0, 1)  # Current and future dates without tasks (green)

            btn = Button(
                text=str(day),
                size_hint=(None, None),
                size=(50, 50),
                background_color=btn_color,
                on_release=lambda instance, day=day: self.select_date(year, month, day)  # Call select_date
            )
            layout.add_widget(btn)

        # Add the layout to the screen
        self.add_widget(layout)

    def select_date(self, year, month, day):
        self.selected_date = f"{year}-{month:02d}-{day:02d}"  # Format the selected date as YYYY-MM-DD
        print(f"Selected date: {self.selected_date}")  # Debugging: Print the selected date

        # Navigate to the Task Manager screen and display tasks for the selected date
        app = MDApp.get_running_app()
        app.filter_tasks_by_date(self.selected_date)  # Filter tasks by the selected date
        app.root.current = "task_manager"  # Navigate to Task Manager screen

    def go_back(self):
        app = MDApp.get_running_app()
        app.root.current = "task_manager"  # Navigate back to the Task Manager screen

    def view_tasks_by_date(self, year, month, day):
        selected_date = f"{year}-{month:02d}-{day:02d}"
        app = MDApp.get_running_app()
        app.filter_tasks_by_date(selected_date)
        app.root.current = "task_manager"  # Navigate to Task Manager screen

# Main App
class TaskApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tag_menu = None
        self.priority_menu = None

    def open_tag_menu(self, caller):
        if not self.tag_menu:
            menu_items = [
                {"text": "General", "viewclass": "OneLineListItem", "on_release": lambda x="General": self.set_tag(caller, x)},
                {"text": "Work", "viewclass": "OneLineListItem", "on_release": lambda x="Work": self.set_tag(caller, x)},
                {"text": "Personal", "viewclass": "OneLineListItem", "on_release": lambda x="Personal": self.set_tag(caller, x)},
                {"text": "Urgent", "viewclass": "OneLineListItem", "on_release": lambda x="Urgent": self.set_tag(caller, x)},
            ]
            self.tag_menu = MDDropdownMenu(caller=caller, items=menu_items, width_mult=4)
        self.tag_menu.open()

    def set_tag(self, caller, tag):
        caller.text = tag
        self.tag_menu.dismiss()

    def open_priority_menu(self, caller):
        if not self.priority_menu:
            menu_items = [
                {"text": "Low", "viewclass": "OneLineListItem", "on_release": lambda x="Low": self.set_priority(caller, x)},
                {"text": "Medium", "viewclass": "OneLineListItem", "on_release": lambda x="Medium": self.set_priority(caller, x)},
                {"text": "High", "viewclass": "OneLineListItem", "on_release": lambda x="High": self.set_priority(caller, x)},
                {"text": "Critical", "viewclass": "OneLineListItem", "on_release": lambda x="Critical": self.set_priority(caller, x)},
            ]
            self.priority_menu = MDDropdownMenu(caller=caller, items=menu_items, width_mult=4)
        self.priority_menu.open()

    def set_priority(self, caller, priority):
        caller.text = priority
        self.priority_menu.dismiss()

    def open_am_pm_menu(self, caller):
        menu_items = [
            {"text": "AM", "viewclass": "OneLineListItem", "on_release": lambda x="AM": self.set_am_pm(caller, x)},
            {"text": "PM", "viewclass": "OneLineListItem", "on_release": lambda x="PM": self.set_am_pm(caller, x)},
        ]
        self.am_pm_menu = MDDropdownMenu(caller=caller, items=menu_items, width_mult=3)
        self.am_pm_menu.open()

    def set_am_pm(self, caller, value):
        caller.text = value
        self.am_pm_menu.dismiss()

    def build(self):
        self.title = "Task Manager"
        self.conn = sqlite3.connect("users_tasks.db")
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.user_id = None  # Initialize user_id
        self.theme_cls.theme_style = "Light"  # Default theme
        # Schedule notifications to run every 60 seconds
        Clock.schedule_interval(self.check_notifications, 60)
        self.test_email()
        return Builder.load_file("main.kv")

    def create_tables(self):
        # Create the `users` table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT,
            name TEXT
        )''')

        # Create the `tasks` table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT,
            note_tag TEXT,
            date TEXT,
            time TEXT,  -- Time column added
            priority TEXT,
            due_date TEXT,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')

        # Add the `time` column if it doesn't exist
        try:
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN time TEXT")
            print("Added 'time' column to 'tasks' table.")
        except sqlite3.OperationalError:
            print("'time' column already exists.")

        self.conn.commit()

    def signup(self, name, username, password, email):
        try:
            if not name.strip() or not username.strip() or not password.strip() or not email.strip():
                self.show_notification("Error", "All fields are required.")
                return

            # Validate email format
            if "@" not in email or "." not in email:
                self.show_notification("Error", "Invalid email address.")
                return

            self.cursor.execute("INSERT INTO users (name, username, password, email) VALUES (?, ?, ?, ?)", (name, username, password, email))
            self.conn.commit()
            self.show_notification("Success", "Signup successful. Please log in.")
            self.root.current = "login"
        except sqlite3.IntegrityError:
            self.show_notification("Error", "Username already exists.")
        except Exception as e:
            self.show_notification("Error", f"An error occurred during signup: {e}")

    def login(self, username, password):
        try:
            self.cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
            result = self.cursor.fetchone()

            if result:
                self.user_id = result[0]
                print(f"Login successful. User ID: {self.user_id}")
                self.root.current = "task_manager"
                self.load_tasks()  # Correct method name
            else:
                self.show_notification("Login Failed", "Invalid username or password. Please try again.")
        except Exception as e:
            self.show_notification("Error", f"An error occurred during login: {e}")

    def send_email(self, subject, body):
        try:
            # Fetch the user's email
            self.cursor.execute("SELECT email FROM users WHERE id=?", (self.user_id,))
            result = self.cursor.fetchone()
            if not result or not result[0]:
                print("No email address found for the user.")
                return

            recipient_email = result[0]

            # Create the email
            msg = MIMEMultipart()
            msg["From"] = EMAIL_ADDRESS
            msg["To"] = recipient_email
            msg["Subject"] = subject

            # Add the email body
            msg.attach(MIMEText(body, "plain"))

            # Connect to the SMTP server and send the email
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.send_message(msg)

            print(f"Email sent to {recipient_email}")
        except smtplib.SMTPException as e:
            print(f"SMTP error occurred: {e}")
        except Exception as e:
            print(f"Error sending email: {e}")

    def test_email(self):
        try:
            self.send_email(
                subject="Test Email",
                body="This is a test email from the Task Manager app."
            )
            print("Test email sent successfully.")
        except Exception as e:
            print(f"Error sending test email: {e}")

    def notify_due_tasks(self):
        try:
            now = datetime.now()
            self.cursor.execute("SELECT content, due_date FROM tasks WHERE user_id=? AND completed=0", (self.user_id,))
            tasks = self.cursor.fetchall()

            for task in tasks:
                task_content, due_date = task
                if due_date:
                    due_date_obj = datetime.strptime(due_date, "%Y-%m-%d")
                    time_remaining = (due_date_obj - now).days
                    if 0 <= time_remaining <= 1:  # Task is due within the next 24 hours
                        self.show_notification("Task Due Soon", f"Task '{task_content}' is due soon (Due Date: {due_date}).")
                        self.send_email(
                            subject="Task Due Soon Reminder",
                            body=f"Task '{task_content}' is due soon. Please complete it by {due_date}."
                        )
        except Exception as e:
            print(f"Error notifying due tasks: {e}")

    def notify_overdue_tasks(self):
        try:
            now = datetime.now()
            self.cursor.execute("SELECT content, due_date FROM tasks WHERE user_id=? AND completed=0", (self.user_id,))
            tasks = self.cursor.fetchall()

            for task in tasks:
                task_content, due_date = task
                if due_date:
                    due_date_obj = datetime.strptime(due_date, "%Y-%m-%d")
                    if due_date_obj < now:  # Task is overdue
                        self.show_notification("Overdue Task", f"Task '{task_content}' was due on {due_date}.")
                        self.send_email(
                            subject="Overdue Task Reminder",
                            body=f"Task '{task_content}' was due on {due_date}. Please complete it as soon as possible."
                        )
        except Exception as e:
            print(f"Error notifying overdue tasks: {e}")

    def check_notifications(self, *args):
        self.notify_due_tasks()
        self.notify_overdue_tasks()

    def show_notification(self, title, message):
        try:
            dialog = MDDialog(
                title=title,
                text=message,
                buttons=[
                    MDRaisedButton(
                        text="OK",
                        on_release=lambda x: dialog.dismiss()
                    )
                ],
            )
            dialog.open()
        except Exception as e:
            print(f"Error showing notification: {e}")

    def load_tasks(self):
        try:
            task_list = self.root.get_screen("task_manager").ids.task_list
            task_list.clear_widgets()

            self.cursor.execute("SELECT id, content, note_tag, date, time, priority, due_date, completed FROM tasks WHERE user_id=?", (self.user_id,))
            tasks = self.cursor.fetchall()

            for task in tasks:
                task_id, content, note_tag, date, time, priority, due_date, completed = task
                task_item = self.create_task_item(task_id, content, note_tag, priority, due_date, time, completed)
                task_list.add_widget(task_item)
        except sqlite3.Error as e:
            self.show_notification("Database Error", f"An error occurred: {e}")
        except Exception as e:
            self.show_notification("Error", f"Error loading tasks: {e}")

    def add_task(self, task_text, due_date=None, time=None, tag="General", priority="Medium"):
        try:
            if not self.user_id:
                self.show_notification("Error", "User is not logged in. Task not added.")
                return

            if not task_text.strip():
                self.show_notification("Error", "Task text is empty. Task not added.")
                return

            # Validate due_date format
            if due_date:
                try:
                    datetime.strptime(due_date, "%Y-%m-%d")
                except ValueError:
                    self.show_notification("Error", "Invalid due date format. Use YYYY-MM-DD.")
                    return

            # Validate time format
            if time:
                try:
                    datetime.strptime(time, "%I:%M %p")  # 12-hour format with AM/PM
                except ValueError:
                    self.show_notification("Error", "Invalid time format. Use HH:MM AM/PM.")
                    return

            date_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if hasattr(self, "editing_task_id") and self.editing_task_id:
                # Update the existing task
                self.cursor.execute(
                    "UPDATE tasks SET content=?, note_tag=?, priority=?, due_date=?, time=? WHERE id=?",
                    (task_text, tag, priority, due_date, time, self.editing_task_id)
                )
                self.editing_task_id = None  # Clear the editing task ID
                self.show_notification("Success", "Task updated successfully.")
            else:
                # Add a new task
                self.cursor.execute(
                    "INSERT INTO tasks (user_id, content, note_tag, date, time, priority, due_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (self.user_id, task_text, tag, date_created, time, priority, due_date)
                )
                self.show_notification("Success", "Task added successfully.")

            self.conn.commit()
            self.load_tasks()
            self.root.current = "task_manager"
        except sqlite3.Error as e:
            self.show_notification("Database Error", f"An error occurred: {e}")
        except Exception as e:
            self.show_notification("Error", f"Error adding/updating task: {e}")

    def filter_tasks_by_category(self, category):
        try:
            task_list = self.root.get_screen("task_manager").ids.task_list
            task_list.clear_widgets()

            now = datetime.now()

            if category == "completed":
                self.cursor.execute(
                    "SELECT id, content, note_tag, date, time, priority, due_date, completed FROM tasks WHERE user_id=? AND completed=1",
                    (self.user_id,)
                )
                tasks = self.cursor.fetchall()
            elif category == "uncompleted":
                self.cursor.execute(
                    "SELECT id, content, note_tag, date, time, priority, due_date, completed FROM tasks WHERE user_id=? AND completed=0",
                    (self.user_id,)
                )
                tasks = self.cursor.fetchall()
            elif category == "due_soon":
                self.cursor.execute(
                    "SELECT id, content, note_tag, date, time, priority, due_date, completed FROM tasks WHERE user_id=? AND completed=0",
                    (self.user_id,)
                )
                tasks = self.cursor.fetchall()
                tasks = [
                    task for task in tasks
                    if task[6] and 0 <= (datetime.strptime(task[6], "%Y-%m-%d") - now).days <= 1
                ]
            elif category == "overdue":
                self.cursor.execute(
                    "SELECT id, content, note_tag, date, time, priority, due_date, completed FROM tasks WHERE user_id=? AND completed=0",
                    (self.user_id,)
                )
                tasks = self.cursor.fetchall()
                tasks = [
                    task for task in tasks
                    if task[6] and datetime.strptime(task[6], "%Y-%m-%d") < now
                ]
            else:
                self.load_tasks()
                return

            # Display filtered tasks with buttons
            for task in tasks:
                task_id, content, note_tag, date, time, priority, due_date, completed = task
                task_item = self.create_task_item(task_id, content, note_tag, priority, due_date, time, completed)
                task_list.add_widget(task_item)
        except sqlite3.Error as e:
            self.show_notification("Database Error", f"An error occurred: {e}")
        except Exception as e:
            self.show_notification("Error", f"Error filtering tasks: {e}")

    def search_tasks(self, query):
        try:
            task_list = self.root.get_screen("task_manager").ids.task_list
            task_list.clear_widgets()

            # Fetch tasks that match the search query
            self.cursor.execute(
                "SELECT id, content, note_tag, date, time, priority, due_date, completed FROM tasks WHERE user_id=? AND content LIKE ?",
                (self.user_id, f"%{query}%")
            )
            tasks = self.cursor.fetchall()

            for task in tasks:
                task_id, content, note_tag, date, time, priority, due_date, completed = task
                task_item = self.create_task_item(task_id, content, note_tag, priority, due_date, time, completed)
                task_list.add_widget(task_item)
        except sqlite3.Error as e:
            self.show_notification("Database Error", f"An error occurred: {e}")
        except Exception as e:
            self.show_notification("Error", f"Error searching tasks: {e}")

    def edit_task(self, task_id):
        try:
            # Fetch the task details from the database
            self.cursor.execute("SELECT content, due_date, note_tag, priority, time FROM tasks WHERE id=?", (task_id,))
            task = self.cursor.fetchone()
            if task:
                content, due_date, note_tag, priority, time = task
                # Navigate to the AddTaskScreen and pre-fill the fields for editing
                self.root.current = "add_task"
                add_task_screen = self.root.get_screen("add_task")
                add_task_screen.ids.task_input.text = content
                add_task_screen.ids.due_date_input.text = due_date or ""
                add_task_screen.ids.time_input.text = time or ""
                add_task_screen.ids.tag_dropdown.text = note_tag
                add_task_screen.ids.priority_dropdown.text = priority
                # Store the task_id for updating
                self.editing_task_id = task_id
        except sqlite3.Error as e:
            self.show_notification("Database Error", f"An error occurred: {e}")
        except Exception as e:
            self.show_notification("Error", f"Error editing task: {e}")

    def delete_task(self, task_id):
        try:
            self.cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            self.conn.commit()
            self.show_notification("Success", "Task deleted successfully.")
            self.load_tasks()
        except sqlite3.Error as e:
            self.show_notification("Database Error", f"An error occurred: {e}")
        except Exception as e:
            self.show_notification("Error", f"Error deleting task: {e}")

    def complete_task(self, task_id):
        try:
            self.cursor.execute("UPDATE tasks SET completed=1 WHERE id=?", (task_id,))
            self.conn.commit()
            self.show_notification("Success", "Task marked as completed.")
            self.load_tasks()
        except sqlite3.Error as e:
            self.show_notification("Database Error", f"An error occurred: {e}")
        except Exception as e:
            self.show_notification("Error", f"Error completing task: {e}")

    def open_calendar_screen(self):
        # Get the current year and month
        now = datetime.now()
        year, month = now.year, now.month

        # Navigate to the calendar screen and create the calendar
        calendar_screen = self.root.get_screen("calendar")
        calendar_screen.create_calendar(year, month)
        self.root.current = "calendar"

    def clear_add_task_fields(self):
        try:
            add_task_screen = self.root.get_screen("add_task")
            add_task_screen.ids.task_input.text = ""  # Clear task input
            add_task_screen.ids.due_date_input.text = ""  # Clear due date input
            add_task_screen.ids.time_input.text = ""  # Clear time input
            add_task_screen.ids.tag_dropdown.text = "General"  # Reset tag dropdown
            add_task_screen.ids.priority_dropdown.text = "Medium"  # Reset priority dropdown
            self.editing_task_id = None  # Clear the editing task ID
        except Exception as e:
            self.show_notification("Error", f"Error clearing task fields: {e}")

    def sign_out(self):
        try:
            self.user_id = None  # Clear the logged-in user ID
            self.show_notification("Signed Out", "You have been signed out successfully.")
            self.root.current = "login"  # Navigate back to the Login screen
        except Exception as e:
            self.show_notification("Error", f"Error signing out: {e}")

    def filter_tasks_by_date(self, date):
        try:
            task_list = self.root.get_screen("task_manager").ids.task_list
            task_list.clear_widgets()

            self.cursor.execute(
                "SELECT id, content, note_tag, date, time, priority, due_date, completed FROM tasks WHERE user_id=? AND due_date=?",
                (self.user_id, date)
            )
            tasks = self.cursor.fetchall()

            for task in tasks:
                task_id, content, note_tag, date, time, priority, due_date, completed = task
                task_item = self.create_task_item(task_id, content, note_tag, priority, due_date, time, completed)
                task_list.add_widget(task_item)
        except sqlite3.Error as e:
            self.show_notification("Database Error", f"An error occurred: {e}")
        except Exception as e:
            self.show_notification("Error", f"Error filtering tasks: {e}")

    def prefill_due_date(self):
        try:
            add_task_screen = self.root.get_screen("add_task")
            calendar_screen = self.root.get_screen("calendar")
            if (calendar_screen.selected_date):
                add_task_screen.ids.due_date_input.text = calendar_screen.selected_date  # Pre-fill the selected date
        except Exception as e:
            self.show_notification("Error", f"Error pre-filling due date: {e}")

    def load_profile(self):
        try:
            # Fetch the user's details from the database
            self.cursor.execute("SELECT name, username, email FROM users WHERE id=?", (self.user_id,))
            user = self.cursor.fetchone()
            if user:
                name, username, email = user
                profile_screen = self.root.get_screen("profile")
                profile_screen.ids.name_input.text = name
                profile_screen.ids.username_input.text = username
                profile_screen.ids.email_input.text = email
        except sqlite3.Error as e:
            self.show_notification("Database Error", f"An error occurred: {e}")
        except Exception as e:
            self.show_notification("Error", f"Error loading profile: {e}")

    def update_profile(self, name, email):
        try:
            if not name.strip() or not email.strip():
                self.show_notification("Error", "Name and email cannot be empty.")
                return

            # Validate email format
            if "@" not in email or "." not in email:
                self.show_notification("Error", "Invalid email address.")
                return

            # Update the user's details in the database
            self.cursor.execute("UPDATE users SET name=?, email=? WHERE id=?", (name, email, self.user_id))
            self.conn.commit()
            self.show_notification("Success", "Profile updated successfully.")
            self.root.current = "task_manager"  # Navigate back to Task Manager
        except sqlite3.Error as e:
            self.show_notification("Database Error", f"An error occurred: {e}")
        except Exception as e:
            self.show_notification("Error", f"Error updating profile: {e}")

    def create_task_item(self, task_id, content, note_tag, priority, due_date, time, completed):
        task_item = BoxLayout(orientation="horizontal", size_hint_y=None, height=50, spacing=10)
        task_details = TwoLineListItem(
            text=f"{content} (Priority: {priority})",
            secondary_text=f"Tag: {note_tag}, Due: {due_date} at {time}, Completed: {'Yes' if completed else 'No'}"
        )
        task_item.add_widget(task_details)
        # Add buttons (Edit, Delete, Complete)
        edit_button = MDRaisedButton(
            text="Edit",
            size_hint=(None, None),
            size=(80, 40),
            on_release=lambda x, task_id=task_id: self.edit_task(task_id)
        )
        task_item.add_widget(edit_button)

        delete_button = MDRaisedButton(
            text="Delete",
            size_hint=(None, None),
            size=(80, 40),
            on_release=lambda x, task_id=task_id: self.delete_task(task_id)
        )
        task_item.add_widget(delete_button)

        complete_button = MDRaisedButton(
            text="Complete",
            size_hint=(None, None),
            size=(100, 40),
            on_release=lambda x, task_id=task_id: self.complete_task(task_id)
        )
        task_item.add_widget(complete_button)

        return task_item

    def on_stop(self):
        self.conn.close()

if __name__ == "__main__":
    TaskApp().run()