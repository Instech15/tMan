# Task Manager App

The **Task Manager App** is a productivity application built using **Kivy** and **KivyMD**. It allows users to manage their tasks efficiently with features like task creation, categorization, prioritization, and calendar-based task viewing. The app also includes email notifications for due and overdue tasks.

---

## Features

- **User Authentication**: 
  - Signup and login functionality.
  - Profile management (update name and email).

- **Task Management**:
  - Add, edit, delete, and mark tasks as complete.
  - Categorize tasks with tags (e.g., General, Work, Personal, Urgent).
  - Set task priorities (Low, Medium, High, Critical).
  - Assign due dates and times to tasks.

- **Calendar Integration**:
  - View tasks on a calendar.
  - Highlight overdue tasks, tasks due today, and future tasks.

- **Email Notifications**:
  - Receive reminders for tasks due soon.
  - Get notified about overdue tasks.

- **Search and Filter**:
  - Search tasks by keywords.
  - Filter tasks by categories (completed, uncompleted, due soon, overdue).

---

## Technologies Used

- **Python**: Core programming language.
- **Kivy**: Framework for building the app's GUI.
- **KivyMD**: Material Design components for an enhanced UI.
- **SQLite**: Local database for storing user and task data.
- **smtplib**: For sending email notifications.
- **dotenv**: For managing environment variables securely.

---

## Installation

### Prerequisites
- Python 3.8 or higher installed on your system.
- Required Python libraries:
  - `kivy`
  - `kivymd`
  - `sqlite3`
  - `python-dotenv`

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/tManApp.git
   cd tManApp