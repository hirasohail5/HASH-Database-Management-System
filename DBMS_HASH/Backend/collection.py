import json
import os
from .hashtable import HashTable
from .object import Object
from .indexing import BPlusTree
import re


class Collection:
    def __init__(self, name, db_name):
        self.name = name
        self.db_name = db_name  # Database name
        self.records = HashTable()  # Using custom hash table
        self.collection_file = f"{db_name}/{name}.json"  # Path to the collection file
        self.indexes = {}  # Dictionary to hold B+ Tree indexes for attributes
        self.index_metadata_file = f"{db_name}/{name}_indexes.json"

        if not os.path.exists(self.collection_file):
            with open(self.collection_file, 'w') as file:
                json.dump({}, file)
        else:
            self.load_from_file()
        self.load_index_metadata()
        self.load_indexes()
    
    
    def load_index_metadata(self):
        """Load index metadata that tells us which attributes have indexes."""
        if os.path.exists(self.index_metadata_file):
            with open(self.index_metadata_file, "r") as file:
                indexed_attributes = json.load(file)
            for attr in indexed_attributes:
                index_file = f"{self.db_name}/{self.name}_{attr}_index.json"
                bptree = BPlusTree(order=3, index_file=index_file)
                bptree.load_index()
                self.indexes[attr] = bptree

    def load_indexes(self):
        """
        Load the B+ tree indexes for all attributes.
        """
        for attr, bptree in self.indexes.items():
            bptree.load_index()

    def load_from_file(self):
        with open(self.collection_file, "r") as file:
            data = json.load(file)
            for obj_id, attrs in data.items():
                obj = Object(**attrs)
                self.records.insert(obj_id, obj)

    def create_object(self, **attributes):
        new_object = Object(**attributes)
        self.records.insert(new_object.id, new_object)

        for attr, bptree in self.indexes.items():
            if attr in attributes:
                bptree.insert(attributes[attr], new_object.id)

        self.save_to_file()
        message = f"Object created with ID: {new_object.id}"
        return message, [{"ID": new_object.id, **new_object.attributes}]


    def show_all(self):
        all_records = []
        for record_list in self.records.table:
            for obj_id, obj in record_list:
                all_records.append({"ID": obj_id, **obj.attributes})

        if not all_records:
            message = "No records in this collection."
        else:
            message = f"{len(all_records)} record(s) found."

        return message, all_records
                    
    
    def save_to_file(self):
        data = {}
        for record_list in self.records.table:
            for obj_id, obj in record_list:
                data[obj_id] = obj.attributes
        with open(self.collection_file, "w") as file:
            json.dump(data, file, indent=4)
            
            # Save indexes as well
        for bptree in self.indexes.values():
            bptree.save_index()  # Save each index after saving data
        
        # Save index metadata
        with open(self.index_metadata_file, "w") as file:
            json.dump(list(self.indexes.keys()), file)



    def find_with_conditions(self, condition_str, selected_fields=None, sort_key=None, sort_order="asc", offset=0, limit=None):
        matched = []
        
        if not condition_str.strip():
            print("[Linear Search] No condition provided, returning all records.")
            for record_list in self.records.table:
                for obj_id, obj in record_list:
                    matched.append((obj_id, obj))
            return self._format_results(matched, selected_fields, sort_key, sort_order, offset, limit)
        # Normalize the condition string
        normalized = condition_str.replace(" and ", " AND ").replace(" or ", " OR ")

        # Replace operators safely
        normalized = normalized.replace("=", "==").replace("===", "==")  # Avoid triple equal
        normalized = normalized.replace("<==", "<=").replace(">==", ">=")
        normalized = re.sub(r"\bAND\b", "and", normalized)
        normalized = re.sub(r"\bOR\b", "or", normalized)

        # Replace conditions with obj.attributes.get(...)
        condition_pattern = re.compile(r'(\w+)\s*(==|!=|>=|<=|>|<)\s*("[^"]*"|\d+|\w+@?\w*\.\w*)')
        def repl(match):
            field, op, val = match.groups()
            val = val if val.startswith('"') else f'"{val}"'
            return f'obj.attributes.get("{field}", "") {op} {val}'

        try:
            safe_condition = condition_pattern.sub(repl, normalized)
        except Exception as e:
            print(f"Failed to parse condition: {e}")
            return []

        # Try index-based optimization if it's a simple equality condition like: rollno == "5"
        simple_match = re.fullmatch(r'obj\.attributes\.get\("(\w+)", ""\) == "([\w@.]*)"', safe_condition)
        if simple_match:
            field, value = simple_match.groups()
            if field in self.indexes:
                print(f"[Indexed Search] Using index for {field} = {value}")
                doc_ids = self.indexes[field].search(value)
                if doc_ids:
                    for doc_id in doc_ids:
                        for record_list in self.records.table:
                            for obj_id, obj in record_list:
                                if obj_id == doc_id:
                                    matched.append((obj_id, obj))
                else:
                    print(f"[Index] No matching record found in index for {field} = {value}")

                formatted_results = self._format_results(matched, selected_fields, sort_key, sort_order, offset, limit)
                print("[Results Found]:")
                for record in formatted_results:
                    print(record)
                return formatted_results

        print("[Linear Search] Complex condition or no index, scanning all records.")
        for record_list in self.records.table:
            for obj_id, obj in record_list:
                try:
                    if eval(safe_condition, {}, {"obj": obj}):
                        matched.append((obj_id, obj))
                except Exception as e:
                    print(f"Error in evaluating condition: {e}")

        formatted_results=self._format_results(matched, selected_fields, sort_key, sort_order, offset, limit)
        print("[Results Found]:")
        for record in formatted_results:
            print(record)
        return formatted_results

    def _format_results(self, matched, selected_fields, sort_key, sort_order, offset, limit):
        # Sort if needed
        if sort_key:
            matched.sort(key=lambda item: item[1].attributes.get(sort_key, ""), reverse=(sort_order == "desc"))

        # Offset and limit
        matched = matched[offset:]
        if limit is not None:
            matched = matched[:limit]

        # Format results
        results = []
        for obj_id, obj in matched:
            if selected_fields:
                output = {field: obj.attributes.get(field, '') for field in selected_fields}
            else:
                output = obj.attributes
            results.append({"ID": obj_id, **output})

        return results


    def update(self, condition_dict, update_dict):
        updated = False
        updated_records = []

        for record_list in self.records.table:
            for obj_id, obj in record_list:
                if all(obj.attributes.get(k) == v for k, v in condition_dict.items()):
                    for uk, uv in update_dict.items():
                        old_value = obj.attributes.get(uk)
                        obj.attributes[uk] = uv

                        # Update index if applicable
                        if uk in self.indexes:
                            bptree = self.indexes[uk]

                            try:
                                bptree.remove(old_value, obj_id)  # Remove old value
                            except Exception as e:
                                print(f"[Warning] Failed to remove old index: {e}")

                            try:
                                bptree.insert(uv, obj_id)  # Insert new value
                            except Exception as e:
                                print(f"[Warning] Failed to insert new index: {e}")

                    updated = True
                    updated_records.append({"ID": obj_id, **obj.attributes})

        if updated:
            self.save_to_file()
            message = "Records updated successfully."
        else:
            message = "No matching records found to update."

        return message, updated_records



    def delete(self, condition_dict): 
        deleted = False
        for record_list in self.records.table:
            i = 0
            while i < len(record_list):
                obj_id, obj = record_list[i]
                if all(obj.attributes.get(k) == v for k, v in condition_dict.items()):
                    record_list.pop(i)
                    # Remove from any indexes as well
                    for attr, bptree in self.indexes.items():
                        if attr in obj.attributes:
                            bptree.remove(obj.attributes[attr], obj_id)
                    deleted = True
                else:
                    i += 1
        if deleted:
            print("Records deleted successfully.")
            self.save_to_file()
        else:
            print("No matching records found to delete.")



    def sort_records_by(self, field, reverse=False):
        all_objects = []
        for record_list in self.records.table:
            for obj_id, obj in record_list:
                all_objects.append((obj_id, obj))

        try:
            sorted_objects = sorted(all_objects, key=lambda x: x[1].attributes.get(field, ""), reverse=reverse)
            for obj_id, obj in sorted_objects:
                print(f"ID: {obj_id}, {obj}")
        except Exception as e:
            print(f"Error while sorting: {e}")
            
    def create_index(self, attribute_name): 
        """Create a B+ Tree index for a specific attribute."""
        if attribute_name in self.indexes:
            print(f"Index on '{attribute_name}' already exists.")
            return

        if not self.records.table:
            raise ValueError("No records found in the collection to create an index.")

        index_file = f"{self.db_name}/{self.name}_{attribute_name}_index.json"
        index = BPlusTree(order=3, index_file=index_file)

        inserted = 0
        for record_list in self.records.table:
            for record in record_list:
                doc_id, document = record
                attr_value = document.attributes.get(attribute_name)
                if attr_value is not None:
                    index.insert(attr_value, doc_id)
                    inserted += 1

        if inserted == 0:
            print(f"Attribute '{attribute_name}' not found in any record. Index not created.")
            return

        self.indexes[attribute_name] = index

        # Save index metadata
        with open(self.index_metadata_file, "w") as file:
            json.dump(list(self.indexes.keys()), file)

        print(f"Index created on attribute '{attribute_name}'.")


    def remove_index(self, attribute_name):
        """
        Remove the index for a specific attribute.
        """
        if attribute_name in self.indexes:
            index_file = self.indexes[attribute_name].index_file
            del self.indexes[attribute_name]

            # Delete the index file from disk
            if os.path.exists(index_file):
                os.remove(index_file)

            # Update the index metadata file
            with open(self.index_metadata_file, "w") as file:
                json.dump(list(self.indexes.keys()), file)

            print(f"Index removed for attribute '{attribute_name}'.")
        else:
            print(f"No index exists on '{attribute_name}'.")

            
    def print_index(self, attribute):
        if attribute in self.indexes:
            bptree = self.indexes[attribute]
            print(f"Index for {attribute}: {bptree}")
        else:
            print(f"No index found for {attribute}")
            
    def find(self, field, value):
        found = False
        # Check if the field has an index
        if field in self.indexes:
            print(f"Using index to search for {field} = {value}")
            result = self.indexes[field].search(value)
            if result:
                print(f"Found by index: {result}")
                found = True
            else:
                print(f"No records found where {field} = {value} using index.")
        else:
            # If no index, do a linear search
            print(f"Using linear search for {field} = {value}")
            for record_list in self.records.table:
                for obj_id, obj in record_list:
                    if str(obj.attributes.get(field)).lower() == value.lower():
                        print(f"ID: {obj_id}, {obj}")
                        found = True
        if not found:
            print(f"No records found where {field} = {value}")






