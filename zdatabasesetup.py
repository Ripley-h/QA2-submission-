import sqlite3
import os

DATABASE_FILE = "rharrellQuiz.db"

# A dictionary to hold the questions for each course/table.
# Structure: { "table_name": [ (question, opt_a, opt_b, opt_c, opt_d, correct_answer), ... ] }
QUESTIONS = {
    "ds 3850": [
        ("What is the output of `print(2 ** 3)` in Python?", "6", "8", "5", "1.6", "B"),
        ("Which keyword is used to define a function in Python?", "def", "fun", "function", "define", "A"),
        ("How do you add a single-line comment in a Python script?", "# This is a comment", "// This is a comment", "/* This is a comment */", "", "A"),
        ("What data type is the object `['apple', 'banana', 'cherry']`?", "tuple", "set", "list", "dictionary", "C"),
        ("Which method removes the last item from a list and returns it?", "pop()", "remove()", "last()", "delete()", "A"),
        ("How do you start a `for` loop to iterate five times (from 0 to 4)?", "for i in range(5):", "for i in range(1, 5):", "for i in 5:", "for i in [0..4]:", "A"),
        ("What is the result of the expression `3 / 2` in Python 3?", "1", "1.5", "2", "Error", "B"),
        ("Which of the following is used to create a dictionary in Python?", "[]", "()", "{}", "<<>>", "C"),
        ("Which operator is used to check if two values are equal?", "=", "==", "is", "!=", "B"),
        ("What does the `str(123)` function do?", "Returns a string representation of the object", "Causes a syntax error", "Checks if 123 is a string", "Slices a string", "A")
    ],
    "ds 3860": [
        ("What does SQL stand for?", "Structured Query Language", "Strong Question Language", "Standard Query Language", "Sequential Query Language", "A"),
        ("Which SQL clause is used to filter the results of a query?", "FILTER", "GROUP BY", "ORDER BY", "WHERE", "D"),
        ("What is a PRIMARY KEY used for in a database table?", "To uniquely identify each record", "To link two tables together", "To be the first column of a table", "To sort the data automatically", "A"),
        ("What is the main goal of database normalization?", "To increase query speed", "To reduce data redundancy", "To make the database larger", "To complicate the schema", "B"),
        ("Which type of JOIN returns all records from the left table and the matched records from the right table?", "INNER JOIN", "RIGHT JOIN", "LEFT JOIN", "FULL OUTER JOIN", "C"),
        ("A FOREIGN KEY in one table points to a __________ in another table.", "FOREIGN KEY", "PRIMARY KEY", "UNIQUE KEY", "INDEX", "B"),
        ("Which SQL statement is used to add new data to a database?", "ADD RECORD", "INSERT INTO", "UPDATE", "CREATE", "B"),
        ("The First Normal Form (1NF) deals with eliminating what?", "Transitive dependencies", "Partial dependencies", "Repeating groups and ensuring atomicity", "Redundant data", "C"),
        ("The structure of a database, including its tables, columns, and relationships, is called its:", "Schema", "Instance", "Index", "View", "A"),
        ("Which normal form deals with removing transitive partial dependencies?", "1NF", "2NF", "3NF", "BCNF", "C")
    ],
    "hist 4093": [
        ("In which New York City borough did hip hop culture originate in the 1970s?", "Brooklyn", "The Bronx", "Queens", "Manhattan", "B"),
        ("Who is often called the 'father' of hip hop for his pioneering use of 'breakbeats'?", "Grandmaster Flash", "Afrika Bambaataa", "DJ Kool Herc", "Sugarhill Gang", "C"),
        ("Which of the following is NOT considered one of the four traditional elements of hip hop culture?", "DJing", "MCing", "Fashion", "Graffiti Art", "C"),
        ("Which group released the socially conscious and influential track 'The Message' in 1982?", "Run-DMC", "Public Enemy", "N.W.A.", "Grandmaster Flash and the Furious Five", "D"),
        ("Who founded the Universal Zulu Nation, an organization promoting hip hop culture?", "Russell Simmons", "Afrika Bambaataa", "Rick Rubin", "Dr. Dre", "B"),
        ("What 1979 song by The Sugarhill Gang is widely considered the first commercially successful hip hop record?", "Planet Rock", "The Breaks", "Rapper's Delight", "King Tim III", "C"),
        ("The 'Golden Age' of hip hop is most commonly associated with which time period?", "1979-1984", "Late 1980s to mid-1990s", "Late 1990s to early 2000s", "2010-present", "B"),
        ("N.W.A. was a pioneering and controversial group in which subgenre of hip hop?", "Conscious Hip Hop", "Jazz Rap", "Gangsta Rap", "Trap", "C"),
        ("Which producer was the primary architect of the 'G-funk' sound and a co-founder of Death Row Records?", "DJ Premier", "The RZA", "J Dilla", "Dr. Dre", "D"),
        ("What is the art of improvised, freestyle rapping in a competitive setting often called?", "Spitting", "Flowing", "Battling", "Storytelling", "C")
    ],
    "mkt 4100": [
        ("A tax imposed by a government on imported goods is called a(n):", "Quota", "Embargo", "Tariff", "Subsidy", "C"),
        ("The practice of selling goods in a foreign market at a price below their cost of production is known as:", "Dumping", "Licensing", "Exporting", "Countertrade", "A"),
        ("Which global market entry strategy offers the lowest risk but also the least control?", "Joint Venture", "Direct Investment", "Licensing", "Exporting", "D"),
        ("The BRICS countries, a major bloc of emerging economies, includes Brazil, Russia, India, China, and which other country?", "Singapore", "South Korea", "South Africa", "Spain", "C"),
        ("Modifying a product's features, packaging, or quality to meet the needs of a specific foreign market is called:", "Product Standardization", "Product Invention", "Product Adaptation", "Product Diversification", "C"),
        ("An unconscious belief that one's own culture and way of doing things is superior is known as:", "Polycentrism", "Geocentrism", "Regiocentrism", "Ethnocentrism", "D"),
        ("A 'gray market' refers to:", "A market for second-hand goods", "The sale of goods through unofficial or unauthorized channels", "A market with very little government regulation", "A market for environmentally friendly products", "B"),
        ("When two or more companies join to create a new business entity to enter a foreign market, it's called a:", "Franchise", "Strategic Alliance", "Joint Venture", "Merger", "C"),
        ("Using the exact same marketing strategy and mix in all international markets is known as:", "Adapted global marketing", "Standardized global marketing", "Concentrated global marketing", "Localized global marketing", "B"),
        ("Hofstede's cultural dimensions theory is primarily used to understand:", "Economic development across nations", "Political stability in a region", "Differences in cultural values across countries", "Global supply chain logistics", "C")
    ]
}

def create_database():
    """Creates the database and populates it with tables and questions."""
    
    # Remove the old database file if it exists to start fresh
    if os.path.exists(DATABASE_FILE):
        os.remove(DATABASE_FILE)
        print(f"Removed old database file: {DATABASE_FILE}")

    try:
        # Connect to the SQLite database (this will create the file)
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        print(f"Successfully connected to database '{DATABASE_FILE}'")

        # Loop through the questions dictionary to create and populate each table
        for table_name, questions_list in QUESTIONS.items():
            
            # 1. Create the table
            # Using f-string with quotes to handle table names with spaces
            create_table_sql = f'''
            CREATE TABLE IF NOT EXISTS "{table_name}" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_answer TEXT NOT NULL
            );
            '''
            cursor.execute(create_table_sql)
            
            # 2. Populate the table
            # Using executemany for efficiency
            insert_sql = f'INSERT INTO "{table_name}" (question, option_a, option_b, option_c, option_d, correct_answer) VALUES (?, ?, ?, ?, ?, ?)'
            cursor.executemany(insert_sql, questions_list)
            
            print(f"- Table '{table_name}' created and populated with {len(questions_list)} questions.")

        # Commit the changes to the database
        conn.commit()
        print("\nAll changes have been committed to the database.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        # Close the connection
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    create_database()
