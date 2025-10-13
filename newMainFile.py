import tkinter as tk
from tkinter import messagebox, simpledialog, ttk # Added simpledialog and ttk
import sqlite3
import random

# --- DATABASE CONFIGURATION ---
DB_NAME = "rharrellQuiz.db"
NUM_QUESTIONS = 10
ADMIN_PASSWORD = "admin" # The admin password

# --- DATABASE HELPER FUNCTIONS (UPDATED & NEW) ---

def execute_db_query(query, params=(), fetch=None):
    """A central function to execute database queries."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if fetch == "all":
                return cursor.fetchall()
            if fetch == "one":
                return cursor.fetchone()
            conn.commit()
            return True
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"An error occurred: {e}")
        return False

def get_quiz_tables():
    """Fetches the names of all tables (quizzes) from the database."""
    tables_data = execute_db_query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
        fetch="all"
    )
    return [table[0] for table in tables_data] if tables_data else []

def get_questions(table_name):
    """Fetches a specified number of random questions from a given table."""
    return execute_db_query(
        f'SELECT * FROM "{table_name}" ORDER BY RANDOM() LIMIT {NUM_QUESTIONS}',
        fetch="all"
    )

# --- NEW ADMIN DATABASE FUNCTIONS ---

def create_new_course(table_name):
    """Creates a new table in the database for a new course."""
    query = f'''CREATE TABLE IF NOT EXISTS "{table_name}" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_answer TEXT NOT NULL
            );'''
    return execute_db_query(query)

def add_question(table_name, q_data):
    """Adds a new question to the specified table."""
    query = f'''INSERT INTO "{table_name}" 
               (question, option_a, option_b, option_c, option_d, correct_answer) 
               VALUES (?, ?, ?, ?, ?, ?)'''
    params = (q_data['question'], q_data['opt_a'], q_data['opt_b'], q_data['opt_c'], q_data['opt_d'], q_data['correct'])
    return execute_db_query(query, params)

def update_question(table_name, q_id, q_data):
    """Updates an existing question in the database."""
    query = f'''UPDATE "{table_name}" SET 
               question = ?, option_a = ?, option_b = ?, option_c = ?, option_d = ?, correct_answer = ?
               WHERE id = ?'''
    params = (q_data['question'], q_data['opt_a'], q_data['opt_b'], q_data['opt_c'], q_data['opt_d'], q_data['correct'], q_id)
    return execute_db_query(query, params)

def delete_question(table_name, q_id):
    """Deletes a question from the database."""
    return execute_db_query(f'DELETE FROM "{table_name}" WHERE id = ?', (q_id,))

def get_all_questions_for_course(table_name):
    """Gets all questions from a table for editing."""
    return execute_db_query(f'SELECT * FROM "{table_name}" ORDER BY id', fetch="all")


# --- MAIN APPLICATION CLASS (UPDATED) ---

class QuizApp(tk.Tk):
    """Main application window that manages frames."""
    def __init__(self):
        super().__init__()
        self.title("Quiz Bowl Application")
        self.geometry("800x600")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.quiz_data = {"table_name": None, "questions": [], "score": 0}

        # Add the new Admin frames to the loop
        for F in (LoginFrame, QuizSelectionFrame, QuizFrame, ResultsFrame, AdminDashboardFrame, ManageCourseFrame):
            frame = F(container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginFrame")

    def show_frame(self, page_name, **kwargs):
        """Shows the specified frame and passes optional data."""
        if page_name == "ManageCourseFrame":
            self.frames[page_name].set_course(kwargs.get("course_name"))
        
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, 'on_show'): # Call on_show method if it exists
            frame.on_show()

    def start_quiz(self, table_name):
        """Loads quiz data and shows the quiz frame."""
        self.quiz_data["table_name"] = table_name
        self.quiz_data["questions"] = get_questions(table_name)
        self.quiz_data["score"] = 0
        
        if not self.quiz_data["questions"]:
             messagebox.showerror("Error", "No questions could be loaded for this quiz.")
             return

        self.frames["QuizFrame"].load_new_quiz()
        self.show_frame("QuizFrame")


# --- GUI FRAMES (SCREENS) ---

class LoginFrame(tk.Frame):
    """The initial login screen."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        label = tk.Label(self, text="Welcome to Quiz Bowl", font=("Arial", 24, "bold"))
        label.pack(pady=40, padx=10)

        student_button = tk.Button(self, text="Student Login", font=("Arial", 16),
                                   command=lambda: controller.show_frame("QuizSelectionFrame"))
        student_button.pack(pady=20)
        
        # Admin button is now enabled and calls the admin_login method
        admin_button = tk.Button(self, text="Admin Login", font=("Arial", 16), command=self.admin_login)
        admin_button.pack(pady=20)
    
    def admin_login(self):
        """Prompts for admin password."""
        password = simpledialog.askstring("Password", "Enter Admin Password:", show='*')
        if password == ADMIN_PASSWORD:
            self.controller.show_frame("AdminDashboardFrame")
        elif password is not None: # User didn't click cancel
            messagebox.showerror("Access Denied", "Incorrect Password")


class QuizSelectionFrame(tk.Frame):
    """Screen for students to select a quiz."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.label = tk.Label(self, text="Please Select a Quiz", font=("Arial", 24, "bold"))
        self.label.pack(pady=40, padx=10)
        
        self.quiz_buttons_frame = tk.Frame(self)
        self.quiz_buttons_frame.pack(pady=10)

        back_button = tk.Button(self, text="< Back to Login", command=lambda: controller.show_frame("LoginFrame"))
        back_button.pack(pady=(20, 0))
    
    def on_show(self):
        """Called every time the frame is shown to refresh the list."""
        self.update_quiz_list()
        
    def update_quiz_list(self):
        for widget in self.quiz_buttons_frame.winfo_children():
            widget.destroy()

        tables = get_quiz_tables()
        if not tables:
             tk.Label(self.quiz_buttons_frame, text="No quizzes found.", font=("Arial", 14)).pack()
        else:
            for table_name in tables:
                button = tk.Button(self.quiz_buttons_frame, text=table_name, font=("Arial", 16),
                                   command=lambda t=table_name: self.controller.start_quiz(t))
                button.pack(pady=10)


class QuizFrame(tk.Frame):
    """The main screen for taking the quiz."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.question_number_label = tk.Label(self, text="", font=("Arial", 16))
        self.question_number_label.pack(pady=20)

        self.question_label = tk.Label(self, text="", font=("Arial", 18, "bold"), wraplength=700)
        self.question_label.pack(pady=20, padx=20)

        self.selected_option = tk.StringVar()
        self.option_buttons = []
        options_frame = tk.Frame(self)
        options_frame.pack(pady=20)

        for i in range(4):
            btn = tk.Radiobutton(options_frame, text="", variable=self.selected_option, 
                                 value="", font=("Arial", 14), indicatoron=0, 
                                 width=40, padx=20, pady=10)
            btn.pack(pady=5)
            self.option_buttons.append(btn)

        self.submit_button = tk.Button(self, text="Submit Answer", font=("Arial", 16), command=self.next_question)
        self.submit_button.pack(pady=30)
        self.correct_answer_text = ""

    def load_new_quiz(self):
        self.current_question_index = 0
        self.display_current_question()

    def display_current_question(self):
        questions = self.controller.quiz_data["questions"]
        if self.current_question_index < len(questions):
            q_id, q_text, opt_a, opt_b, opt_c, opt_d, correct_letter = questions[self.current_question_index]
            answer_map = {'A': opt_a, 'B': opt_b, 'C': opt_c, 'D': opt_d}
            clean_letter = correct_letter.strip().upper()
            self.correct_answer_text = answer_map.get(clean_letter)
            
            if self.correct_answer_text is None:
                messagebox.showerror("Data Error", f"Invalid correct answer ('{correct_letter}')")
                self.controller.show_frame("QuizSelectionFrame")
                return

            self.question_number_label.config(text=f"Question {self.current_question_index + 1}/{len(questions)}")
            self.question_label.config(text=q_text)
            options = [opt_a, opt_b, opt_c, opt_d]
            self.selected_option.set(None)
            for i, option_text in enumerate(options):
                self.option_buttons[i].config(text=option_text, value=option_text)
        else:
            self.controller.show_frame("ResultsFrame")

    def next_question(self):
        selected_answer = self.selected_option.get()
        if not selected_answer:
            messagebox.showwarning("No Selection", "Please select an answer.")
            return

        if selected_answer.strip().lower() == self.correct_answer_text.strip().lower():
            self.controller.quiz_data["score"] += 1
        
        self.current_question_index += 1
        self.display_current_question()


class ResultsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text="Quiz Complete!", font=("Arial", 24, "bold")).pack(pady=40)
        self.score_label = tk.Label(self, text="", font=("Arial", 20))
        self.score_label.pack(pady=20)
        tk.Button(self, text="Take Another Quiz", font=("Arial", 16),
                  command=lambda: controller.show_frame("QuizSelectionFrame")).pack(pady=20)
    
    def on_show(self):
        score = self.controller.quiz_data["score"]
        total = len(self.controller.quiz_data["questions"])
        score_out_of_10 = round((score / total) * 10, 1) if total > 0 else 0
        self.score_label.config(text=f"You scored {score} out of {total}.\n\nYour final score is: {score_out_of_10} / 10")


# --- NEW ADMIN FRAMES ---

class AdminDashboardFrame(tk.Frame):
    """Admin main menu."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text="Admin Dashboard", font=("Arial", 24, "bold")).pack(pady=20)

        tk.Button(self, text="Add New Course", font=("Arial", 16), command=self.add_course).pack(pady=10)
        tk.Button(self, text="Add New Question", font=("Arial", 16), command=self.add_question).pack(pady=10)
        tk.Button(self, text="Manage Existing Course", font=("Arial", 16), command=self.manage_course).pack(pady=10)
        tk.Button(self, text="< Logout", font=("Arial", 14), command=lambda: controller.show_frame("LoginFrame")).pack(pady=(30,0))
    
    def add_course(self):
        course_name = simpledialog.askstring("New Course", "Enter the name for the new course (table):")
        if course_name:
            if create_new_course(course_name):
                messagebox.showinfo("Success", f"Course '{course_name}' created successfully.")
            else:
                messagebox.showerror("Error", f"Could not create course '{course_name}'. It may already exist.")
    
    def add_question(self):
        AddQuestionWindow(self) # Opens a new Toplevel window for adding a question
    
    def manage_course(self):
        courses = get_quiz_tables()
        if not courses:
            messagebox.showinfo("No Courses", "There are no courses to manage yet. Please add a course first.")
            return
        
        course = simpledialog.askstring("Select Course", f"Enter course name to manage:\n({', '.join(courses)})")
        if course and course in courses:
            self.controller.show_frame("ManageCourseFrame", course_name=course)
        elif course:
            messagebox.showerror("Error", f"Course '{course}' not found.")


class ManageCourseFrame(tk.Frame):
    """Frame to view, edit, and delete questions for a course."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.course_name = None

        # --- Left side: Treeview list ---
        left_frame = tk.Frame(self)
        left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        tk.Label(left_frame, text="Questions", font=("Arial", 16)).pack()
        cols = ('id', 'question')
        self.tree = ttk.Treeview(left_frame, columns=cols, show='headings')
        self.tree.heading('id', text='ID')
        self.tree.heading('question', text='Question')
        self.tree.column('id', width=50, anchor='center')
        self.tree.pack(fill="both", expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_item_select)

        # --- Right side: Editor ---
        right_frame = tk.Frame(self)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(right_frame, text="Edit Question", font=("Arial", 16)).pack()
        
        self.entries = {}
        fields = ["Question", "Option A", "Option B", "Option C", "Option D", "Correct Answer (A-D)"]
        keys = ["question", "opt_a", "opt_b", "opt_c", "opt_d", "correct"]
        for i, field in enumerate(fields):
            tk.Label(right_frame, text=field).pack(anchor='w', pady=(10,0))
            entry = tk.Entry(right_frame, width=50)
            entry.pack(fill='x')
            self.entries[keys[i]] = entry
            
        self.selected_question_id = None
        
        # --- Buttons ---
        btn_frame = tk.Frame(right_frame)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Save Changes", command=self.save_changes).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete Question", command=self.delete_selected_question).pack(side="left", padx=5)
        
        tk.Button(right_frame, text="< Back to Dashboard", command=lambda: controller.show_frame("AdminDashboardFrame")).pack()

    def set_course(self, course_name):
        self.course_name = course_name

    def on_show(self):
        """Refreshes the question list when the frame is shown."""
        self.controller.title(f"Managing: {self.course_name}")
        self.load_questions()

    def load_questions(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        questions = get_all_questions_for_course(self.course_name)
        if questions:
            for q in questions:
                self.tree.insert('', 'end', values=(q[0], q[1]), iid=q[0])
        self.clear_entries()

    def on_item_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        self.selected_question_id = selected_items[0]
        question_data = get_all_questions_for_course(self.course_name)
        
        for q in question_data:
            if str(q[0]) == self.selected_question_id:
                # q is (id, question, opt_a, opt_b, opt_c, opt_d, correct)
                self.entries["question"].delete(0, tk.END); self.entries["question"].insert(0, q[1])
                self.entries["opt_a"].delete(0, tk.END); self.entries["opt_a"].insert(0, q[2])
                self.entries["opt_b"].delete(0, tk.END); self.entries["opt_b"].insert(0, q[3])
                self.entries["opt_c"].delete(0, tk.END); self.entries["opt_c"].insert(0, q[4])
                self.entries["opt_d"].delete(0, tk.END); self.entries["opt_d"].insert(0, q[5])
                self.entries["correct"].delete(0, tk.END); self.entries["correct"].insert(0, q[6])
                break

    def save_changes(self):
        if not self.selected_question_id:
            messagebox.showwarning("Warning", "No question selected to save.")
            return

        q_data = {key: entry.get() for key, entry in self.entries.items()}
        if all(q_data.values()): # Check if any field is empty
            if update_question(self.course_name, self.selected_question_id, q_data):
                messagebox.showinfo("Success", "Question updated successfully.")
                self.load_questions() # Refresh list
            else:
                messagebox.showerror("Error", "Failed to update question.")
        else:
            messagebox.showwarning("Warning", "All fields must be filled.")

    def delete_selected_question(self):
        if not self.selected_question_id:
            messagebox.showwarning("Warning", "No question selected to delete.")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this question?"):
            if delete_question(self.course_name, self.selected_question_id):
                messagebox.showinfo("Success", "Question deleted.")
                self.load_questions() # Refresh list
            else:
                messagebox.showerror("Error", "Failed to delete question.")
    
    def clear_entries(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.selected_question_id = None


class AddQuestionWindow(tk.Toplevel):
    """A Toplevel window for adding a new question."""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add New Question")

        courses = get_quiz_tables()
        if not courses:
            messagebox.showerror("Error", "No courses exist. Please create a course first.", parent=self)
            self.destroy()
            return
            
        tk.Label(self, text="Select Course:").pack(padx=10, pady=(10,0))
        self.course_var = tk.StringVar(self)
        self.course_var.set(courses[0])
        tk.OptionMenu(self, self.course_var, *courses).pack(padx=10, pady=5)
        
        self.entries = {}
        fields = ["Question", "Option A", "Option B", "Option C", "Option D", "Correct Answer (A-D)"]
        keys = ["question", "opt_a", "opt_b", "opt_c", "opt_d", "correct"]
        for i, field in enumerate(fields):
            tk.Label(self, text=field).pack(padx=10, anchor='w')
            entry = tk.Entry(self, width=50)
            entry.pack(padx=10, pady=2, fill='x')
            self.entries[keys[i]] = entry
            
        tk.Button(self, text="Submit Question", command=self.submit).pack(pady=20)

    def submit(self):
        q_data = {key: entry.get() for key, entry in self.entries.items()}
        table_name = self.course_var.get()
        
        if all(q_data.values()):
            if add_question(table_name, q_data):
                messagebox.showinfo("Success", "Question added successfully.", parent=self)
                self.destroy()
            else:
                messagebox.showerror("Error", "Failed to add question.", parent=self)
        else:
            messagebox.showwarning("Incomplete", "All fields are required.", parent=self)


# --- RUN THE APPLICATION ---

if __name__ == "__main__":
    app = QuizApp()
    app.mainloop()