import sqlite3

def connect_db():
    return sqlite3.connect('StarField.db')

def search_names(query):
    connect = connect_db()
    query = '%' + query + '%'
    try:
        cursor = connect.cursor()
        cursor.execute("SELECT Name FROM manufactured WHERE Name LIKE ?;", (query,))
        results = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"An error occurred: {e.args[0]}")
    finally:
        connect.close()

    return [name[0] for name in results]