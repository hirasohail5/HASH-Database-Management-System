import os
import json
from .collection import Collection

class Database:
    def __init__(self, name):
        self.name = name
        self.collections = {}  # Key is collection name, value is Collection object
        self.db_file = f"{name}/database.json"  # Database file to store collection info

        # Create a folder for the database if it doesn't exist
        if not os.path.exists(self.name):
            os.makedirs(self.name)
            print(f"Database folder '{self.name}' created.")
        
        # Load collections from file if it exists
        if os.path.exists(self.db_file):
            self.load_collections()

    def load_collections(self):
        """Load collections from the database file."""
        with open(self.db_file, 'r') as file:
            data = json.load(file)
            for collection_name in data.get('collections', []):
                self.collections[collection_name] = Collection(collection_name, self.name)

    def save_collections(self):
        """Save collections to a database file."""
        with open(self.db_file, 'w') as file:
            data = {
                'collections': list(self.collections.keys())
            }
            json.dump(data, file)

    # def create_collection(self, collection_name):
    #     if collection_name not in self.collections:
    #         collection = Collection(collection_name, self.name)
    #         self.collections[collection_name] = collection
    #         self.save_collections()  # Save after creating a collection
    #         print(f"Collection '{collection_name}' created.")
    #     else:
    #         print(f"Collection '{collection_name}' already exists.")
    
    def create_collection(self, collection_name):
        if not collection_name.strip():
            message="Collection name cannot be empty."
            return {"message": message, "records": []}

        if collection_name not in self.collections:
            collection = Collection(collection_name, self.name)
            self.collections[collection_name] = collection
            self.save_collections()
            message=f"Collection '{collection_name}' created."
            return {"message": message, "records": []}
        else:
            message=f"Collection '{collection_name}' already exists."
            return {"message": message, "records": []}


    def show_all_collections(self):
        if not self.collections:
            print("No collections available.")
            return []  # Return empty list if none

        return list(self.collections.keys())  # Return list of collection names


    def get_collection(self, collection_name):
        return self.collections.get(collection_name)

    def delete_collection(self, collection_name):
        collection = self.collections.get(collection_name)
        if not collection:
            message = f"Collection '{collection_name}' does not exist."
            print(f"[ERROR] {message}")
            return {"success": False, "message": message}

        try:
            # Delete the main collection file
            collection_path = os.path.join(self.name, f"{collection_name}.json")
            if os.path.exists(collection_path):
                os.remove(collection_path)
                print(f"[INFO] Deleted collection file: {collection_path}")

            # Delete the index metadata file
            index_metadata_path = os.path.join(self.name, f"{collection_name}_indexes.json")
            if os.path.exists(index_metadata_path):
                os.remove(index_metadata_path)
                print(f"[INFO] Deleted index metadata file: {index_metadata_path}")

            # Delete all attribute index files
            if hasattr(collection, "indexes"):
                for attribute_name in collection.indexes.keys():
                    attr_index_file = os.path.join(self.name, f"{collection_name}_{attribute_name}_index.json")
                    if os.path.exists(attr_index_file):
                        os.remove(attr_index_file)
                        print(f"[INFO] Deleted attribute index file: {attr_index_file}")

            # Remove from memory
            del self.collections[collection_name]

            # Save updated metadata
            self.save_collections()

            message = f"Collection '{collection_name}' deleted successfully."
            print(f"[SUCCESS] {message}")
            return {"success": True, "message": message, "deleted": collection_name}

        except Exception as e:
            message = f"Failed to delete collection '{collection_name}': {e}"
            print(f"[ERROR] {message}")
            return {"success": False, "message": message}




    def rename_collection(self, old_name, new_name):
        if new_name in self.collections:
            print(f"Collection '{new_name}' already exists. Choose a different name.")
            return

        collection = self.collections.get(old_name)
        if not collection:
            print(f"Collection '{old_name}' not found.")
            return

        # Paths for collection and index files
        old_path = collection.collection_file
        new_path = f"{self.name}/{new_name}.json"
        
        old_index_path = f"{self.name}/{old_name}_indexes.json"
        new_index_path = f"{self.name}/{new_name}_indexes.json"
        
        try:
            # Rename collection file
            os.rename(old_path, new_path)
            
            # Rename index file if it exists
            if os.path.exists(old_index_path):
                os.rename(old_index_path, new_index_path)
                
            # Rename other index files associated with the collection's attributes
            # Assuming collection.data gives the attributes (adjust if it's different in your class)
            for attribute_name in collection.indexes.keys():  # Change this line if you store attributes differently
                old_index_file = f"{self.name}/{old_name}_{attribute_name}_index.json"
                new_index_file = f"{self.name}/{new_name}_{attribute_name}_index.json"
                if os.path.exists(old_index_file):
                    os.rename(old_index_file, new_index_file)
            
        except Exception as e:
            print(f"Failed to rename collection or index files: {e}")
            return

        # Update collection object
        collection.name = new_name
        collection.collection_file = new_path

        # Update internal collections dict
        self.collections[new_name] = collection
        del self.collections[old_name]

        # ✅ Update database.json with new collection names
        self.save_collections()

        print(f"Collection '{old_name}' successfully renamed to '{new_name}'.")
