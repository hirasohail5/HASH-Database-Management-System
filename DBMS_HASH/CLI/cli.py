import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Backend.dbms import DBMS
from Backend.query_processor import query_processor  


def main_menu(dbms):
    while True:
        print("\n--- Main Menu ---")
        print("1. Show Databases")
        print("2. Create Database")
        print("3. Set Current Database")
        print("4. New Query")  # ✅ Add option
        print("5. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            dbms.show_databases()
        elif choice == '2':
            db_name = input("Enter database name: ")
            dbms.create_database(db_name)
        elif choice == '3':
            db_name = input("Enter database name to set as current: ")
            dbms.set_current_database(db_name)
            collection_menu(dbms)
        elif choice == '4':
            query_processor(dbms)  # ✅ Call query processor
        elif choice == '5':
            break
        else:
            print("Invalid choice! Please try again.")



def collection_menu(dbms):
    current_db = dbms.get_current_database()
    if not current_db:
        print("No database selected. Returning to main menu.")
        return

    while True:
        print("\n--- Collection Menu ---")
        print("1. Create Collection")
        print("2. Show All Collections")
        print("3. Select Collection")
        print("4. Return to Main Menu")
        choice = input("Enter your choice: ")

        if choice == '1':
            collection_name = input("Enter collection name: ")
            current_db.create_collection(collection_name)
        elif choice == '2':
            current_db.show_all_collections()
        elif choice == '3':
            collection_name = input("Enter collection name: ")
            collection = current_db.get_collection(collection_name)
            if collection:
                object_menu(collection)
            else:
                print(f"Collection '{collection_name}' does not exist.")
        elif choice == '4':
            break
        else:
            print("Invalid choice! Please try again.")

def object_menu(collection):
    while True:
        print("\n--- Object Menu ---")
        print("1. Create Object")
        print("2. Show All Objects")
        print("3. Return to Collection Menu")
        choice = input("Enter your choice: ")

        if choice == '1':
            print("Enter the attributes of the object:")
            attributes = {}
            while True:
                key = input("Enter attribute name (or 'done' to finish): ")
                if key == 'done':
                    break
                value = input(f"Enter value for '{key}': ")
                attributes[key] = value
            collection.create_object(**attributes)
        elif choice == '2':
            collection.show_all()
        elif choice == '3':
            break
        else:
            print("Invalid choice! Please try again.")

# Initialize dbms
dbms = DBMS()

# Start CLI Menu
main_menu(dbms)
