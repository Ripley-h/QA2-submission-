import tkinter as tk
from tkinter import messagebox
import sqlite3
import random

# --- DATABASE CONFIGURATION ---
DB_NAME = "rharrellQuiz.db"
NUM_QUESTIONS = 10

# --- DATABASE HELPER FUNCTIONS ---

def get_quiz_tables():
    """Fetches the names of all tables (quizzes) from the database."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]
            # Filter out internal sqlite tables if any exist
            return [t for t in tables if not t.startswith('sqlite_')]
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Could not connect to database: {e}")
        return []

def get_questions(table_name):
    """Fetches a specified number of random questions from a given table."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            # Fetch NUM_QUESTIONS random questions
            cursor.execute(f'SELECT * FROM "{table_name}" ORDER BY RANDOM() LIMIT {NUM_QUESTIONS}')
            questions = cursor.fetchall()
            if len(questions) < NUM_QUESTIONS:
                messagebox.showwarning("Warning", f"The '{table_name}' quiz has fewer than {NUM_QUESTIONS} questions. The quiz will proceed with {len(questions)} questions.")
            return questions
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Could not fetch questions from table {table_name}: {e}")
        return []

# --- MAIN APPLICATION CLASS ---

class QuizApp(tk.Tk):
    """Main application window that manages frames."""
    def __init__(self):
        super().__init__()
        self.title("Quiz Bowl Application")
        self.geometry("800x600")

        # Container for all frames
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.quiz_data = {"table_name": None, "questions": [], "score": 0}

        # Create and store frames
        for F in (LoginFrame, QuizSelectionFrame, QuizFrame, ResultsFrame):
            frame = F(container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginFrame")

    def show_frame(self, page_name):
        """Shows the specified frame."""
        frame = self.frames[page_name]
        frame.tkraise()
        # Special handling for frames that need refreshing
        if page_name == "ResultsFrame":
             frame.show_score() # Update score display when shown
        if page_name == "QuizSelectionFrame":
             frame.update_quiz_list() # Update quiz list in case DB changes

    def start_quiz(self, table_name):
        """Loads quiz data and shows the quiz frame."""
        self.quiz_data["table_name"] = table_name
        self.quiz_data["questions"] = get_questions(table_name)
        self.quiz_data["score"] = 0
        
        if not self.quiz_data["questions"]:
             messagebox.showerror("Error", "No questions could be loaded for this quiz. Please select another.")
             return

        # Tell QuizFrame to set up the new quiz
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

        admin_button = tk.Button(self, text="Admin Login", font=("Arial", 16), state="disabled")
        admin_button.pack(pady=20)


class QuizSelectionFrame(tk.Frame):
    """Screen for students to select a quiz."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.label = tk.Label(self, text="Please Select a Quiz", font=("Arial", 24, "bold"))
        self.label.pack(pady=40, padx=10)
        
        self.quiz_buttons_frame = tk.Frame(self)
        self.quiz_buttons_frame.pack(pady=10)

        self.update_quiz_list()

    def update_quiz_list(self):
        # Clear old buttons
        for widget in self.quiz_buttons_frame.winfo_children():
            widget.destroy()

        # Create buttons for each quiz table
        tables = get_quiz_tables()
        if not tables:
             no_quiz_label = tk.Label(self.quiz_buttons_frame, text="No quizzes found in the database.", font=("Arial", 14))
             no_quiz_label.pack()
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

    def load_new_quiz(self):
        """Resets and loads the UI for the start of a new quiz."""
        self.current_question_index = 0
        self.display_current_question()

    def display_current_question(self):
        """Updates the labels and buttons for the current question."""
        questions = self.controller.quiz_data["questions"]
        if self.current_question_index < len(questions):
            question_data = questions[self.current_question_index]
            
            # Unpack data, assuming the last column is the correct letter (A, B, C, or D)
            q_id, q_text, opt_a, opt_b, opt_c, opt_d, correct_letter = question_data
            
            # Create a map of letters to the actual answer text
            answer_map = {'A': opt_a, 'B': opt_b, 'C': opt_c, 'D': opt_d}
            
            # Find the full text of the correct answer using the letter
            clean_letter = correct_letter.strip().upper()
            self.correct_answer_text = answer_map.get(clean_letter)
            
            if self.correct_answer_text is None:
                messagebox.showerror("Data Error", f"Invalid correct answer letter ('{correct_letter}') found in database for question: '{q_text}'")
                self.controller.show_frame("QuizSelectionFrame")
                return

            self.question_number_label.config(text=f"Question {self.current_question_index + 1}/{len(questions)}")
            self.question_label.config(text=q_text)
            
            # Display options in a fixed order (A, B, C, D)
            options = [opt_a, opt_b, opt_c, opt_d]
            
            self.selected_option.set(None)

            for i, option_text in enumerate(options):
                self.option_buttons[i].config(text=option_text, value=option_text)
        else:
            # End of quiz
            self.controller.show_frame("ResultsFrame")

    def next_question(self):
        """Checks the answer and moves to the next question or results."""
        selected_answer = self.selected_option.get()
        if not selected_answer:
            messagebox.showwarning("No Selection", "Please select an answer before proceeding.")
            return

        # Compare the selected full text with the correct full text
        if selected_answer.strip().lower() == self.correct_answer_text.strip().lower():
            self.controller.quiz_data["score"] += 1
        
        self.current_question_index += 1
        self.display_current_question()

class ResultsFrame(tk.Frame):
    """The final screen showing the quiz score."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.label = tk.Label(self, text="Quiz Complete!", font=("Arial", 24, "bold"))
        self.label.pack(pady=40)

        self.score_label = tk.Label(self, text="", font=("Arial", 20))
        self.score_label.pack(pady=20)

        home_button = tk.Button(self, text="Take Another Quiz", font=("Arial", 16),
                                command=lambda: controller.show_frame("QuizSelectionFrame"))
        home_button.pack(pady=20)
    
    def show_score(self):
        """Updates the score label with the final score."""
        score = self.controller.quiz_data["score"]
        total = len(self.controller.quiz_data["questions"])
        
        # Calculate score out of 10
        if total > 0:
            score_out_of_10 = round((score / total) * 10, 1)
        else:
            score_out_of_10 = 0
            
        self.score_label.config(text=f"You scored {score} out of {total}.\n\nYour final score is: {score_out_of_10} / 10")


# --- RUN THE APPLICATION ---

if __name__ == "__main__":
    app = QuizApp()
    app.mainloop()