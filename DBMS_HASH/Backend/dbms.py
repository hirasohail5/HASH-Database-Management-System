import os
import json
import shutil
from .database import Database
from .transaction import TransactionManager

class DBMS:
    def __init__(self,root_path="."):
        self.root_path = root_path  # Set the root_path before using it
        self.databases = {}  # Key is database name, value is Database object
        self.current_database = None
        self.transaction_manager = TransactionManager(self.root_path)
        self.load_databases()

    def load_databases(self):
        """Load all databases from the 'databases.json' file."""
        if os.path.exists("databases.json"):
            with open("databases.json", "r") as file:
                data = json.load(file)
                for db_name in data:
                    self.databases[db_name] = Database(db_name)

    def save_databases(self):
        """Save all databases to the 'databases.json' file."""
        with open("databases.json", "w") as file:
            json.dump(list(self.databases.keys()), file)
    
    def create_database(self, db_name):
        if not db_name.strip():  # Check for empty or whitespace-only input
            message = "Database name cannot be empty."
            print(f"[ERROR] {message}")
            return {"message": message, "records": []}

        if db_name not in self.databases:
            self.databases[db_name] = Database(db_name)
            self.save_databases()  # Save after creating a database
            message = f"Database '{db_name}' created successfully."
            print(f"[INFO] {message}")
            return {"message": message, "records": [{"name": db_name}]}
        else:
            message = f"Database '{db_name}' already exists."
            print(f"[WARNING] {message}")
            return {"message": message, "records": []}


    
    def delete_database(self, db_name):
        if db_name in self.databases:
            shutil.rmtree(db_name, ignore_errors=True)
            del self.databases[db_name]
            if self.current_database and self.current_database.name == db_name:
                self.current_database = None
            self.save_databases()
            print(f"Database '{db_name}' deleted.")
        else:
            print(f"Database '{db_name}' does not exist.")

    def rename_database(self, old_name, new_name):
        if old_name not in self.databases:
            print(f"Database '{old_name}' does not exist.")
            return

        if new_name in self.databases:
            print(f"A database named '{new_name}' already exists.")
            return

        # Rename the database folder
        try:
            os.rename(old_name, new_name)
        except Exception as e:
            print(f"Failed to rename database folder: {e}")
            return

        # Update the database object in memory
        database = self.databases.pop(old_name)
        database.name = new_name
        self.databases[new_name] = database

        # Update collection file paths to reflect the new database name
        for collection in database.collections.values():
            old_path = collection.collection_file
            new_path = old_path.replace(old_name, new_name)
            collection.collection_file = new_path  # Update the collection file path
            
            try:
                os.rename(old_path, new_path)  # Rename collection file
            except Exception as e:
                print(f"Failed to rename collection file: {e}")

        # If you're tracking the current database, update the reference
        if self.current_database == old_name:
            self.current_database = new_name

        self.save_databases()
        print(f"Database renamed from '{old_name}' to '{new_name}'.")

    def delete_collection(self, collection_name):
        db = self.get_current_database()
        if db:
            db.delete_collection(collection_name)
        else:
            print("No current database selected.")
            
    def show_databases(self):
        if not self.databases:
            print("No databases available.")
            return []  # Return empty list if no databases

        return list(self.databases.keys())  # Return the list of database names


    def set_current_database(self, db_name):
        if db_name in self.databases:
            self.current_database = self.databases[db_name]
            print(f"Current database set to '{db_name}'.")
        else:
            print(f"Database '{db_name}' does not exist.")

    def get_current_database(self):
        return self.current_database
