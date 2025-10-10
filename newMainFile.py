import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sqlite3
import random

# --- Main Application Class ---
# This class manages the main window and all the different screens (frames).
class QuizApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("R. Harrell Quiz Bowl")
        self.geometry("600x500")

        # Container for all frames
        container = ttk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        # Create and store each frame
        for F in (LoginScreen, QuizSelectionScreen, QuizScreen, ResultsScreen):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(LoginScreen)

    def show_frame(self, cont, data=None):
        """Raises the selected frame to the top and can pass data to it."""
        frame = self.frames[cont]
        if data:
            frame.receive_data(data)
        frame.tkraise()

# --- Login Screen Frame ---
# The first screen the user sees.
class LoginScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        
        label = ttk.Label(self, text="Welcome to the Quiz Bowl!", font=("Helvetica", 18))
        label.pack(pady=20, padx=10)

        student_button = ttk.Button(self, text="Student Login",
                                   command=lambda: controller.show_frame(QuizSelectionScreen))
        student_button.pack(pady=10)

        admin_button = ttk.Button(self, text="Admin Login", state="disabled")
        admin_button.pack(pady=10)
        
        admin_info = ttk.Label(self, text="(Admin functionality is not yet implemented)")
        admin_info.pack(pady=5)


# --- Quiz Selection Screen Frame ---
# This screen fetches and displays the available quizzes (tables) from the database.
class QuizSelectionScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        label = ttk.Label(self, text="Select a Quiz", font=("Helvetica", 16))
        label.pack(pady=20, padx=10)

        self.selected_quiz_var = tk.StringVar()
        
        # This OptionMenu will be populated with quiz names from the database
        self.quiz_menu = ttk.OptionMenu(self, self.selected_quiz_var, "Select a quiz...")
        self.quiz_menu.pack(pady=10)

        start_button = ttk.Button(self, text="Start Quiz", command=self.start_quiz)
        start_button.pack(pady=20)
        
        # Populate the menu when the frame is raised
        self.bind("<<ShowFrame>>", self.on_show_frame)

    def on_show_frame(self, event):
        """Called when the frame is shown to refresh the quiz list."""
        self.populate_quizzes()
        
    def populate_quizzes(self):
        """Connects to the DB and fetches the table names to display."""
        try:
            conn = sqlite3.connect('rharrellQuiz.db')
            cursor = conn.cursor()
            # This query gets all table names from the database
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            # Fetch all table names, which are returned as tuples
            tables = [table[0] for table in cursor.fetchall()]
            conn.close()

            # Update the OptionMenu with the fetched table names
            menu = self.quiz_menu["menu"]
            menu.delete(0, "end")
            if tables:
                for table in tables:
                    menu.add_command(label=table, command=lambda value=table: self.selected_quiz_var.set(value))
                self.selected_quiz_var.set(tables[0]) # Default to the first quiz
            else:
                self.selected_quiz_var.set("No quizzes found")
                
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not connect to database or find tables.\nError: {e}")
            self.selected_quiz_var.set("Error loading quizzes")

    def start_quiz(self):
        """Starts the selected quiz."""
        selected_quiz = self.selected_quiz_var.get()
        if selected_quiz and "Select" not in selected_quiz and "Error" not in selected_quiz and "No quizzes" not in selected_quiz:
             # Pass the selected table name to the QuizScreen
            self.controller.show_frame(QuizScreen, data={"quiz_name": selected_quiz})
        else:
            messagebox.showwarning("Selection Error", "Please select a valid quiz to start.")


# --- Quiz Screen Frame ---
# This frame displays the questions, options, and handles quiz logic.
class QuizScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.question_label = ttk.Label(self, text="Question text will go here", font=("Helvetica", 14), wraplength=550, justify="center")
        self.question_label.pack(pady=20, padx=20)

        self.user_answer = tk.StringVar()
        self.radio_buttons = []
        for i in range(4):
            rb = ttk.Radiobutton(self, text="", variable=self.user_answer, value="")
            rb.pack(anchor="w", padx=40, pady=5)
            self.radio_buttons.append(rb)

        self.submit_button = ttk.Button(self, text="Submit Answer", command=self.next_question)
        self.submit_button.pack(pady=20)

    def receive_data(self, data):
        """Receives the quiz name and loads the questions."""
        quiz_name = data.get("quiz_name")
        if quiz_name:
            self.load_quiz(quiz_name)

    def load_quiz(self, table_name):
        """Fetches questions from the selected table in the database."""
        try:
            conn = sqlite3.connect('rharrellQuiz.db')
            cursor = conn.cursor()
            # SQL queries with table names containing spaces need double quotes
            cursor.execute(f'SELECT * FROM "{table_name}"')
            self.questions = cursor.fetchall()
            conn.close()
            
            # Shuffle the questions for variety
            random.shuffle(self.questions)

            # Reset quiz state
            self.current_question_index = 0
            self.score = 0
            
            if not self.questions:
                messagebox.showerror("Quiz Error", f"No questions found in the '{table_name}' quiz.")
                self.controller.show_frame(QuizSelectionScreen)
                return
            
            self.display_question()

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load questions from '{table_name}'.\nError: {e}")
            self.controller.show_frame(QuizSelectionScreen)

    def display_question(self):
        """Updates the GUI with the current question and options."""
        if self.current_question_index < len(self.questions):
            q_data = self.questions[self.current_question_index]
            # q_data tuple: (id, question, option_a, option_b, option_c, option_d, correct_answer)
            question_text = q_data[1]
            
            # THE FIX IS HERE: Convert the tuple slice to a list
            options = list(q_data[2:6])

            self.question_label.config(text=f"Q{self.current_question_index + 1}: {question_text}")
            
            # Shuffle the options for this question
            random.shuffle(options)
            
            self.user_answer.set(None) # Deselect radio buttons

            for i, option in enumerate(options):
                self.radio_buttons[i].config(text=option, value=option)
                
            self.submit_button.config(text="Submit Answer")
            if self.current_question_index == len(self.questions) - 1:
                self.submit_button.config(text="Finish Quiz")

    def next_question(self):
        """Checks the user's answer and moves to the next question or the results screen."""
        selected_answer = self.user_answer.get()
        if not selected_answer or selected_answer == 'None':
            messagebox.showwarning("No Answer", "Please select an answer before proceeding.")
            return

        correct_answer = self.questions[self.current_question_index][6]

        if selected_answer == correct_answer:
            self.score += 1
        
        self.current_question_index += 1

        if self.current_question_index < len(self.questions):
            self.display_question()
        else:
            # Quiz is over, show the results screen
            result_data = {"score": self.score, "total": len(self.questions)}
            self.controller.show_frame(ResultsScreen, data=result_data)


# --- Results Screen Frame ---
# The final screen showing the user's score.
class ResultsScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.result_label = ttk.Label(self, text="", font=("Helvetica", 18))
        self.result_label.pack(pady=40, padx=20)
        
        return_button = ttk.Button(self, text="Take Another Quiz",
                                  command=lambda: controller.show_frame(QuizSelectionScreen))
        return_button.pack(pady=20)

    def receive_data(self, data):
        """Receives the final score and total questions to display."""
        score = data.get("score")
        total = data.get("total")
        self.result_label.config(text=f"Quiz Complete!\n\nYour Score: {score} out of {total}")


# --- Main execution block ---
if __name__ == "__main__":
    app = QuizApp()
    # This is a trick to raise the QuizSelectionScreen frame and trigger its on_show_frame method on startup
    app.frames[QuizSelectionScreen].event_generate("<<ShowFrame>>")
    app.mainloop()