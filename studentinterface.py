import tkinter as tk
from tkinter import font as tkfont
import sqlite3
import random

# --- Configuration ---
DATABASE_FILE = "rharrellQuiz.db"
# A list of your table names to validate against and prevent errors.
QUIZ_CATEGORIES = ["ds 3850", "ds 3860", "mkt 4100", "hist 4093"]


class QuizBowlApp(tk.Tk):
    """Main application class that controls frame navigation."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("Quiz Bowl Application")
        self.geometry("850x650")

        # Main container to hold all frames (screens)
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        # Initialize and store all frames
        for F in (LoginFrame, CategorySelectionFrame, QuizFrame):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Show the initial login screen
        self.show_frame("LoginFrame")

    def show_frame(self, page_name, category=None):
        """Brings the requested frame to the front."""
        frame = self.frames[page_name]
        # If navigating to the QuizFrame, load the selected category's data
        if page_name == "QuizFrame" and category:
            frame.load_quiz(category)
        frame.tkraise()


class LoginFrame(tk.Frame):
    """The initial login screen with two path options."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        title_font = tkfont.Font(family='Helvetica', size=28, weight="bold")
        label = tk.Label(self, text="Quiz Bowl Login", font=title_font, pady=40)
        label.pack()

        button_font = tkfont.Font(family='Helvetica', size=14)
        
        # Path 1: The main path for quiz takers
        quiz_taker_button = tk.Button(self, text="Take a Quiz",
                                     font=button_font,
                                     width=20, height=2,
                                     command=lambda: controller.show_frame("CategorySelectionFrame"))
        quiz_taker_button.pack(pady=15)

        # Path 2: Placeholder for a second path
        admin_button = tk.Button(self, text="Admin Path (Not Implemented)",
                                 font=button_font,
                                 width=25, height=2, state="disabled")
        admin_button.pack(pady=15)


class CategorySelectionFrame(tk.Frame):
    """The welcome screen for selecting a quiz category."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        title_font = tkfont.Font(family='Helvetica', size=24, weight="bold")
        label = tk.Label(self, text="Select a Quiz Category", font=title_font, pady=30)
        label.pack()

        button_font = tkfont.Font(family='Helvetica', size=12)
        for category in QUIZ_CATEGORIES:
            button = tk.Button(self, text=category.upper(),
                               font=button_font,
                               width=20, height=2,
                               command=lambda cat=category: controller.show_frame("QuizFrame", category=cat))
            button.pack(pady=10)


class QuizFrame(tk.Frame):
    """The main interface for taking the quiz."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # --- State variables ---
        self.questions = []
        self.current_question_index = 0
        self.score = 0
        self.correct_answer = ""
        self.selected_option = tk.StringVar()

        # --- GUI Widgets ---
        self.title_label = tk.Label(self, text="Quiz", font=tkfont.Font(size=20, weight="bold"))
        self.title_label.pack(pady=20)

        self.question_label = tk.Label(self, text="Question appears here", font=tkfont.Font(size=16), wraplength=750)
        self.question_label.pack(pady=(10, 30))

        options_frame = tk.Frame(self)
        options_frame.pack(pady=10)
        self.option_buttons = []
        # Create radio buttons for options a, b, c, d
        for option_char in ["A", "B", "C", "D"]:
            rb = tk.Radiobutton(options_frame, text="", variable=self.selected_option,
                               value=option_char, font=tkfont.Font(size=12), anchor="w", justify="left")
            rb.pack(fill="x", pady=5, padx=20)
            self.option_buttons.append(rb)
        
        self.feedback_label = tk.Label(self, text="", font=tkfont.Font(size=14, weight="bold"))
        self.feedback_label.pack(pady=15)
        
        self.submit_button = tk.Button(self, text="Submit Answer", command=self.check_answer, font=tkfont.Font(size=12))
        self.submit_button.pack(pady=10)
        
        self.next_button = tk.Button(self, text="Next Question", command=self.next_question, font=tkfont.Font(size=12))
        self.results_label = tk.Label(self, text="", font=tkfont.Font(size=18, weight="bold"))
        self.return_button = tk.Button(self, text="Return to Menu", command=self.reset_and_return, font=tkfont.Font(size=12))

    def load_quiz(self, category):
        """Fetches questions from the database for the selected category."""
        if category not in QUIZ_CATEGORIES:
            self.question_label.config(text=f"Error: Invalid category '{category}'.")
            return
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            # Note: Quoting column and table names with spaces is crucial
            query = f'SELECT "Question", "Option A", "Option B", "Option C", "Option D", "Correct" FROM "{category}"'
            cursor.execute(query)
            self.questions = cursor.fetchall()
            conn.close()
            
            random.shuffle(self.questions) # Shuffle questions for a new experience
            self.current_question_index = 0
            self.score = 0
            self.display_question()
        except sqlite3.Error as e:
            self.question_label.config(text=f"Database Error: {e}\nCould not load quiz.")

    def display_question(self):
        """Updates the GUI with the current question and options."""
        # Reset UI for the new question
        self.feedback_label.config(text="")
        self.selected_option.set(None)
        for rb in self.option_buttons:
            rb.config(state="normal")
            rb.pack(fill="x", pady=5, padx=20) # Ensure they are visible
        self.submit_button.pack(pady=10)
        self.next_button.pack_forget()
        self.results_label.pack_forget()
        self.return_button.pack_forget()

        # Load question data
        q_data = self.questions[self.current_question_index]
        question_text, opt_a, opt_b, opt_c, opt_d, self.correct_answer = q_data
        
        self.title_label.config(text=f"Question {self.current_question_index + 1}/{len(self.questions)}")
        self.question_label.config(text=question_text)
        self.option_buttons[0].config(text=opt_a)
        self.option_buttons[1].config(text=opt_b)
        self.option_buttons[2].config(text=opt_c)
        self.option_buttons[3].config(text=opt_d)

    def check_answer(self):
        """Checks the selected answer and provides immediate feedback."""
        user_answer = self.selected_option.get()
        if user_answer == 'None': # Check if an option was selected
            self.feedback_label.config(text="Please select an answer.", fg="orange")
            return
        
        # Provide feedback and update score
        if user_answer.strip().lower() == self.correct_answer.strip().lower():
            self.score += 1
            self.feedback_label.config(text="Correct! 🎉", fg="green")
        else:
            self.feedback_label.config(text=f"Incorrect. The correct answer was: {self.correct_answer}", fg="red")
        
        # Disable options and swap the Submit button for the Next button
        for rb in self.option_buttons:
            rb.config(state="disabled")
        self.submit_button.pack_forget()
        self.next_button.pack(pady=10)
        
    def next_question(self):
        """Loads the next question or shows the final results."""
        self.current_question_index += 1
        if self.current_question_index < len(self.questions):
            self.display_question()
        else:
            self.show_results()

    def show_results(self):
        """Displays the final score at the end of the quiz."""
        # Clear quiz elements
        self.question_label.config(text="")
        for rb in self.option_buttons:
            rb.pack_forget()
        self.next_button.pack_forget()
        self.feedback_label.config(text="")
        
        # Display final score
        self.results_label.config(text=f"Quiz Complete!\nYour Final Score: {self.score} / {len(self.questions)}", fg="blue")
        self.results_label.pack(pady=50)
        self.return_button.pack(pady=20)

    def reset_and_return(self):
        """Resets the quiz state and returns to the category selection screen."""
        self.questions = []
        self.controller.show_frame("CategorySelectionFrame")

if __name__ == "__main__":
    app = QuizBowlApp()
    app.mainloop()