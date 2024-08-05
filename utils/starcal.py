import sqlite3

def connect_db():
    return sqlite3.connect('StarField.db')

def search_names(query):
    connect = connect_db()
    query = '%' + query + '%'
    results = []
    try:
        cursor = connect.cursor()
        cursor.execute("SELECT Name FROM manufactured WHERE Name LIKE ?;", (query,))
        results = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"An error occurred: {e.args[0]}")
    finally:
        connect.close()

    return [name[0] for name in results]
#print(search_names('a'))

def fullRawRequire(item):
    
    connect = connect_db()
    query = '%' + item + '%'
    requirement_count = {}
    try:
        cursor = connect.cursor()
        cursor.execute("SELECT * FROM recipes WHERE Output = ?;", (item,))
        result = cursor.fetchall()
        for entry in result:
            for i in range(2, len(entry), 2):
                if entry[i] is not None and entry[i+1] is not None:
                    requirement_num = entry[i]
                    requirement_desc = entry[i+1]

                    # Check if this requirement is an output of another recipe
                    cursor.execute("SELECT * FROM recipes WHERE Output = ?", (requirement_desc,))
                    recursive_results = cursor.fetchall()

                    if not recursive_results:  # Base material, not an output of another recipe
                        if requirement_desc in requirement_count:
                            requirement_count[requirement_desc] += requirement_num
                        else:
                            requirement_count[requirement_desc] = requirement_num
                    else:  # Recursive case
                        sub_requirements = rawRequire(requirement_desc)
                        for sub_req, sub_count in sub_requirements.items():
                            if sub_req in requirement_count:
                                requirement_count[sub_req] += sub_count * requirement_num
                            else:
                                requirement_count[sub_req] = sub_count * requirement_num

                    
    except sqlite3.Error as e:
        print(f"An error occurred: {e.args[0]}")
    finally:
        connect.close()

    return dict(sorted(requirement_count.items()))
def rawRequire(item):
    connect = connect_db()
    requirement_count = {}
    try:
        cursor = connect.cursor()
        
        # Retrieve the recipe for the given item
        cursor.execute("SELECT * FROM recipes WHERE Output = ?;", (item,))
        result = cursor.fetchall()

        for entry in result:
            for i in range(2, len(entry), 2):
                if entry[i] is not None and entry[i+1] is not None:
                    requirement_num = entry[i]
                    requirement_desc = entry[i+1]

                    # Add or update the requirement count in the dictionary
                    if requirement_desc in requirement_count:
                        requirement_count[requirement_desc] += requirement_num
                    else:
                        requirement_count[requirement_desc] = requirement_num

    except sqlite3.Error as e:
        print(f"An error occurred: {e.args[0]}")
    finally:
        connect.close()

    return dict(sorted(requirement_count.items()))

# Example usage
#print(rawRequire('Vytinium Fuel Rod'))

def manufacturedRequire(item):
    connect = connect_db()
    manufacturing_items = {}
    try:
        cursor = connect.cursor()
        
        # Retrieve the recipe for the given item
        cursor.execute("SELECT * FROM recipes WHERE Output = ?;", (item,))
        result = cursor.fetchall()

        for entry in result:
            for i in range(2, len(entry), 2):
                if entry[i] is not None and entry[i+1] is not None:
                    requirement_num = entry[i]
                    requirement_desc = entry[i+1]

                    # Check if this requirement is a manufactured item
                    cursor.execute("SELECT Name FROM manufactured WHERE Name = ?;", (requirement_desc,))
                    manufactured_item = cursor.fetchone()

                    if manufactured_item:
                        if manufactured_item[0] in manufacturing_items:
                            manufacturing_items[manufactured_item[0]] += requirement_num
                        else:
                            manufacturing_items[manufactured_item[0]] = requirement_num

    except sqlite3.Error as e:
        print(f"An error occurred: {e.args[0]}")
    finally:
        connect.close()

    return dict(sorted(manufacturing_items.items()))

# Example usage
#print("Manufactured items required:", manufacturedRequire('Vytinium Fuel Rod'))

def organicRequire(item):
    connect = connect_db()
    organic_items = {}
    try:
        cursor = connect.cursor()
        
        # Retrieve the recipe for the given item
        cursor.execute("SELECT * FROM recipes WHERE Output = ?;", (item,))
        result = cursor.fetchall()

        for entry in result:
            for i in range(2, len(entry), 2):
                if entry[i] is not None and entry[i+1] is not None:
                    requirement_num = entry[i]
                    requirement_desc = entry[i+1]

                    # Check if this requirement is an organic item
                    cursor.execute("SELECT Name FROM organic WHERE Name = ?;", (requirement_desc,))
                    organic_item = cursor.fetchone()

                    if organic_item:
                        if organic_item[0] in organic_items:
                            organic_items[organic_item[0]] += requirement_num
                        else:
                            organic_items[organic_item[0]] = requirement_num

    except sqlite3.Error as e:
        print(f"An error occurred: {e.args[0]}")
    finally:
        connect.close()

    return dict(sorted(organic_items.items()))
#print("Organic items required:", organicRequire('Polytextile'))

def inorganicRequire(item):
    connect = connect_db()
    inorganic_items = {}
    try:
        cursor = connect.cursor()
        
        # Retrieve the recipe for the given item
        cursor.execute("SELECT * FROM recipes WHERE Output = ?;", (item,))
        result = cursor.fetchall()

        for entry in result:
            for i in range(2, len(entry), 2):
                if entry[i] is not None and entry[i+1] is not None:
                    requirement_num = entry[i]
                    requirement_desc = entry[i+1]

                    # Check if this requirement is an inorganic item
                    cursor.execute("SELECT Name FROM inorganic WHERE Name = ?;", (requirement_desc,))
                    inorganic_item = cursor.fetchone()

                    if inorganic_item:
                        if inorganic_item[0] in inorganic_items:
                            inorganic_items[inorganic_item[0]] += requirement_num
                        else:
                            inorganic_items[inorganic_item[0]] = requirement_num

    except sqlite3.Error as e:
        print(f"An error occurred: {e.args[0]}")
    finally:
        connect.close()

    return dict(sorted(inorganic_items.items()))

# Example usage
#print("Inorganic items required:", inorganicRequire('Vytinium Fuel Rod'))

