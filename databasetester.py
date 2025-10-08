import tkinter as tk
from tkinter import ttk
import sqlite3
import os

DATABASE_FILE = "rharrellQuiz.db"
TABLE_NAMES = ["ds 3850", "ds 3860", "hist 4093", "mkt 4100"]

class QuizDBViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz Database Viewer")
        self.root.geometry("1200x700") # Set a larger initial size for better viewing
        
        # --- UI Elements ---
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Top frame for controls
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # Label and dropdown for table selection
        ttk.Label(control_frame, text="Select a Course Table to View:", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=(0, 10))
        
        self.selected_table = tk.StringVar()
        self.table_menu = ttk.OptionMenu(
            control_frame, 
            self.selected_table, 
            "Select a table", 
            *TABLE_NAMES, 
            command=self.load_table_data
        )
        self.table_menu.pack(side=tk.LEFT)
        self.table_menu.config(width=15)

        # --- Treeview for displaying data ---
        
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Define columns
        columns = ("id", "question", "opt_a", "opt_b", "opt_c", "opt_d", "answer")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        # Define headings
        self.tree.heading("id", text="ID")
        self.tree.heading("question", text="Question")
        self.tree.heading("opt_a", text="Option A")
        self.tree.heading("opt_b", text="Option B")
        self.tree.heading("opt_c", text="Option C")
        self.tree.heading("opt_d", text="Option D")
        self.tree.heading("answer", text="Correct")

        # Configure column widths
        self.tree.column("id", width=40, stretch=tk.NO, anchor="center")
        self.tree.column("question", width=450)
        self.tree.column("opt_a", width=120)
        self.tree.column("opt_b", width=120)
        self.tree.column("opt_c", width=120)
        self.tree.column("opt_d", width=120)
        self.tree.column("answer", width=60, stretch=tk.NO, anchor="center")

        # Add a scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Status Bar ---
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=5)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # --- Initial check for database file ---
        self.check_db_file()

    def check_db_file(self):
        """Checks if the database file exists and updates the status."""
        if not os.path.exists(DATABASE_FILE):
            self.status_var.set(f"ERROR: Database file '{DATABASE_FILE}' not found in this directory.")
            self.table_menu.config(state=tk.DISABLED) # Disable dropdown if no DB
        else:
            self.status_var.set(f"Successfully connected to '{DATABASE_FILE}'. Please select a table.")

    def load_table_data(self, table_name):
        """Fetches data from the selected table and displays it in the Treeview."""
        # Clear previous data from the tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            # Connect to the database
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            # Fetch all data from the selected table
            # Using f-string with quotes to handle table names with spaces
            cursor.execute(f'SELECT * FROM "{table_name}"')
            rows = cursor.fetchall()
            
            # Insert new data into the tree
            for row in rows:
                self.tree.insert("", tk.END, values=row)
                
            self.status_var.set(f"Displaying {len(rows)} questions from the '{table_name}' table.")

        except sqlite3.Error as e:
            self.status_var.set(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

if __name__ == "__main__":
    app_root = tk.Tk()
    app = QuizDBViewer(app_root)
    app_root.mainloop()