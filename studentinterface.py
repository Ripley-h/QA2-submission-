import tkinter as tk
from tkinter import font as tkfont
import sqlite3
import random

# A list of your table names to prevent SQL injection
# The application will only allow quizzes from these tables.
ALLOWED_TABLES = ["ds3850", "ds3860", "mkt4100", "hist4093"]

class QuizApp(tk.Tk):
    """
    Main application class that manages switching between frames (screens).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("Quiz Bowl Application")
        self.geometry("800x600")

        # Set up a container to hold all the frames
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        # Create and store each frame in the container
        for F in (CategorySelectionFrame, QuizFrame):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Show the initial frame
        self.show_frame("CategorySelectionFrame")

    def show_frame(self, page_name):
        """Raises the given frame to the top to make it visible."""
        frame = self.frames[page_name]
        frame.tkraise()
        # If we are showing the quiz frame, we need to load the quiz data
        if page_name == "QuizFrame":
            # This is a placeholder; the category will be set by the selection screen
            pass

class CategorySelectionFrame(tk.Frame):
    """
    The welcome screen where users select their quiz category.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Title Label
        title_font = tkfont.Font(family='Helvetica', size=24, weight="bold")
        title_label = tk.Label(self, text="Welcome to Quiz Bowl!", font=title_font)
        title_label.pack(pady=40)

        subtitle_font = tkfont.Font(family='Helvetica', size=14)
        subtitle_label = tk.Label(self, text="Please select a quiz category to begin:", font=subtitle_font)
        subtitle_label.pack(pady=10, padx=20)

        # Create a button for each allowed table/category
        button_font = tkfont.Font(family='Helvetica', size=12)
        for category in ALLOWED_TABLES:
            button = tk.Button(
                self,
                text=category.upper(),
                font=button_font,
                width=20,
                height=2,
                command=lambda cat=category: self.start_quiz(cat)
            )
            button.pack(pady=8)

    def start_quiz(self, category_name):
        """
        Loads the quiz data for the selected category and switches to the quiz frame.
        """
        quiz_frame = self.controller.frames["QuizFrame"]
        quiz_frame.load_quiz(category_name)
        self.controller.show_frame("QuizFrame")


class QuizFrame(tk.Frame):
    """
    The main quiz interface where questions are displayed and answered.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- State Variables ---
        self.questions = []
        self.current_question_index = 0
        self.score = 0
        self.correct_answer = ""
        self.selected_option = tk.StringVar()

        # --- Title and Score ---
        self.title_label = tk.Label(self, text="Quiz in Progress", font=tkfont.Font(size=20, weight="bold"))
        self.title_label.pack(pady=20)

        self.score_label = tk.Label(self, text="Score: 0/0", font=tkfont.Font(size=14))
        self.score_label.pack(pady=5)

        # --- Question Display ---
        self.question_label = tk.Label(
            self,
            text="Question text will appear here.",
            font=tkfont.Font(size=16),
            wraplength=700, # Ensures text wraps if too long
            justify="center"
        )
        self.question_label.pack(pady=30)

        # --- Options (Radio Buttons) ---
        options_frame = tk.Frame(self)
        options_frame.pack(pady=20)
        self.option_buttons = []
        option_font = tkfont.Font(family='Helvetica', size=12)
        
        for i, option in enumerate(["A", "B", "C", "D"]):
            rb = tk.Radiobutton(
                options_frame,
                text=f"Option {option}",
                variable=self.selected_option,
                value=option,
                font=option_font,
                anchor="w",
                justify="left"
            )
            rb.pack(fill="x", pady=5, padx=50)
            self.option_buttons.append(rb)

        # --- Feedback Label ---
        self.feedback_label = tk.Label(self, text="", font=tkfont.Font(size=14, weight="bold"))
        self.feedback_label.pack(pady=10)

        # --- Control Buttons ---
        self.submit_button = tk.Button(self, text="Submit Answer", command=self.check_answer, font=tkfont.Font(size=12))
        self.submit_button.pack(pady=10)

        self.next_button = tk.Button(self, text="Next Question", command=self.next_question, font=tkfont.Font(size=12))
        # self.next_button is packed later when needed

        self.return_button = tk.Button(self, text="Return to Menu", command=lambda: controller.show_frame("CategorySelectionFrame"), font=tkfont.Font(size=12))
        # self.return_button is packed at the end of the quiz

    def load_quiz(self, table_name):
        """Fetches questions from the database for the selected category."""
        if table_name not in ALLOWED_TABLES:
            self.question_label.config(text=f"Error: Invalid quiz category '{table_name}'.")
            return
            
        try:
            conn = sqlite3.connect('rharrellQuiz.db')
            cursor = conn.cursor()
            # Safely query the table using the verified table_name
            cursor.execute(f"SELECT question, \"option a\", \"option b\", \"option c\", \"option d\", correct FROM {table_name}")
            self.questions = cursor.fetchall()
            conn.close()
            
            if not self.questions:
                self.question_label.config(text="No questions found in this category.")
                return

            random.shuffle(self.questions) # Shuffle questions for a new experience
            
            # Reset state for a new quiz
            self.current_question_index = 0
            self.score = 0
            self.display_question()

        except sqlite3.Error as e:
            self.question_label.config(text=f"Database Error: {e}")
            self.questions = []

    def display_question(self):
        """Updates the GUI to show the current question and options."""
        # Hide end-of-quiz buttons if they exist
        self.return_button.pack_forget()
        
        # Reset UI elements for the new question
        self.feedback_label.config(text="")
        self.selected_option.set(None) # Deselect radio buttons
        self.submit_button.pack(pady=10)
        self.next_button.pack_forget()

        # Enable option buttons
        for rb in self.option_buttons:
            rb.config(state="normal")
            
        # Get current question data
        question_data = self.questions[self.current_question_index]
        question_text, opt_a, opt_b, opt_c, opt_d, self.correct_answer = question_data
        
        # Update labels and buttons with new data
        self.title_label.config(text=f"Question {self.current_question_index + 1}/{len(self.questions)}")
        self.question_label.config(text=question_text)
        self.option_buttons[0].config(text=opt_a, value="A")
        self.option_buttons[1].config(text=opt_b, value="B")
        self.option_buttons[2].config(text=opt_c, value="C")
        self.option_buttons[3].config(text=opt_d, value="D")
        self.update_score_label()

    def check_answer(self):
        """Checks the user's selected answer and provides immediate feedback."""
        user_answer = self.selected_option.get()

        if not user_answer: # Check if an option was selected
            self.feedback_label.config(text="Please select an answer!", fg="orange")
            return
            
        # Disable option buttons after submission
        for rb in self.option_buttons:
            rb.config(state="disabled")

        if user_answer == self.correct_answer:
            self.score += 1
            self.feedback_label.config(text="Correct!", fg="green")
        else:
            self.feedback_label.config(text=f"Incorrect. The correct answer was: {self.correct_answer}", fg="red")
        
        self.update_score_label()
        
        # Swap Submit button for Next button
        self.submit_button.pack_forget()
        self.next_button.pack(pady=10)

    def next_question(self):
        """Moves to the next question or ends the quiz."""
        self.current_question_index += 1
        if self.current_question_index < len(self.questions):
            self.display_question()
        else:
            self.show_results()
            
    def show_results(self):
        """Displays the final score at the end of the quiz."""
        # Clear the quiz elements
        self.question_label.config(text="Quiz Finished!")
        for rb in self.option_buttons:
            rb.pack_forget()
        self.feedback_label.config(text=f"Your Final Score: {self.score} out of {len(self.questions)}", fg="blue")
        self.next_button.pack_forget()
        
        # Show the return to menu button
        self.return_button.pack(pady=20)

    def update_score_label(self):
        """Updates the score display."""
        self.score_label.config(text=f"Score: {self.score}/{len(self.questions)}")


if __name__ == "__main__":
    app = QuizApp()
    app.mainloop()