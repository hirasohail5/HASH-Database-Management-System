import json
import uuid

class Object:
    def __init__(self, **attributes):
        self.id = str(uuid.uuid4())  # Generate a unique ID using uuid
        self.attributes = attributes  # Store attributes as a dictionary

    def __repr__(self):
        return f"Object(ID={self.id}, Attributes={self.attributes})"

class Collection:
    def __init__(self, name):
        self.name = name
        self.records = {}  # Key is the UUID-based ID, value is the Object

    def create_object(self, **attributes):
        new_object = Object(**attributes)  # Create object with dynamic attributes
        self.records[new_object.id] = new_object  # Store object with UUID as key
        print(f"Object created with ID: {new_object.id}")
        self.save_to_file()

    def show_all(self):
        if not self.records:
            print("No records in this collection.")
        for obj_id, obj in self.records.items():
            print(f"ID: {obj_id}, {obj}")

    def save_to_file(self):
        with open(f"{self.name}.json", "w") as file:
            # Save objects with attributes as a dictionary to JSON
            json.dump({key: obj.attributes for key, obj in self.records.items()}, file, indent=4)

class Database:
    def __init__(self, name):
        self.name = name
        self.collections = {}  # Key is collection name, value is Collection object

    def create_collection(self, collection_name):
        if collection_name not in self.collections:
            self.collections[collection_name] = Collection(collection_name)
            print(f"Collection '{collection_name}' created.")
        else:
            print(f"Collection '{collection_name}' already exists.")

    def show_all_collections(self):
        if not self.collections:
            print("No collections in this database.")
        for collection_name, collection in self.collections.items():
            print(f"Collection: {collection_name}")

    def get_collection(self, collection_name):
        return self.collections.get(collection_name)

class OODMS:
    def __init__(self):
        self.databases = {}  # Key is database name, value is Database object
        self.current_database = None

    def create_database(self, db_name):
        if db_name not in self.databases:
            self.databases[db_name] = Database(db_name)
            print(f"Database '{db_name}' created.")
        else:
            print(f"Database '{db_name}' already exists.")

    def show_databases(self):
        if not self.databases:
            print("No databases available.")
        for db_name in self.databases:
            print(f"Database: {db_name}")

    def set_current_database(self, db_name):
        if db_name in self.databases:
            self.current_database = self.databases[db_name]
            print(f"Current database set to '{db_name}'.")
        else:
            print(f"Database '{db_name}' does not exist.")

    def get_current_database(self):
        return self.current_database

# CLI Menu System
def main_menu(oodms):
    while True:
        print("\n--- Main Menu ---")
        print("1. Show Databases")
        print("2. Create Database")
        print("3. Set Current Database")
        print("4. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            oodms.show_databases()
        elif choice == '2':
            db_name = input("Enter database name: ")
            oodms.create_database(db_name)
        elif choice == '3':
            db_name = input("Enter database name to set as current: ")
            oodms.set_current_database(db_name)
            collection_menu(oodms)
        elif choice == '4':
            break
        else:
            print("Invalid choice! Please try again.")

def collection_menu(oodms):
    current_db = oodms.get_current_database()
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

# Initialize OODMS
oodms = OODMS()

# Start CLI Menu
main_menu(oodms)
