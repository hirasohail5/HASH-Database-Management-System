import json
import os

class BPlusTreeNode:
    def __init__(self, is_leaf=True):
        self.is_leaf = is_leaf
        self.keys = []  # List of tuples: (key, doc_id)
        self.children = []  # Child nodes or pointers
        self.parent = None

    def to_dict(self):
        # Only store the keys (attribute value and doc_id)
        return {
            "is_leaf": self.is_leaf,
            "keys": self.keys,
            "children": [child.to_dict() for child in self.children] if not self.is_leaf else []
        }

class BPlusTree:
    def __init__(self, order=3, index_file="index.json"):
        self.root = BPlusTreeNode()
        self.order = order
        self.index_file = index_file

    def insert(self, key, doc_id):
        leaf_node = self._find_leaf_node(key)
        
        # Check if the key already exists
        for idx, (existing_key, doc_ids) in enumerate(leaf_node.keys):
            if existing_key == key:
                # Append the doc_id if it's not already there
                if doc_id not in doc_ids:
                    doc_ids.append(doc_id)
                break
        else:
            # Insert new key with a list of doc_ids containing the current doc_id
            leaf_node.keys.append((key, [doc_id]))
        
        leaf_node.keys.sort()

        if len(leaf_node.keys) > self.order:
            self._split_node(leaf_node)

        self.save_index()


    def _find_leaf_node(self, key):
        node = self.root
        while not node.is_leaf:
            for i, (node_key, _) in enumerate(node.keys):
                if key < node_key:
                    node = node.children[i]
                    break
            else:
                node = node.children[-1]
        return node

    def _split_node(self, node):
        mid_index = len(node.keys) // 2
        mid_key = node.keys[mid_index]

        new_node = BPlusTreeNode(is_leaf=node.is_leaf)
        new_node.keys = node.keys[mid_index:]
        node.keys = node.keys[:mid_index]

        if node == self.root:
            new_root = BPlusTreeNode(is_leaf=False)
            new_root.keys = [mid_key]
            new_root.children = [node, new_node]
            node.parent = new_root
            new_node.parent = new_root
            self.root = new_root
        else:
            parent = node.parent
            new_node.parent = parent
            parent.keys.append(mid_key)
            parent.children.append(new_node)
            parent.keys.sort()
            if len(parent.keys) > self.order:
                self._split_node(parent)

    def search(self, key):
        leaf_node = self._find_leaf_node(key)
        for k, doc_ids in leaf_node.keys:
            if k == key:
                return doc_ids  # Return list of doc_ids
        return []  # Return empty list if no match found


    def save_index(self):
        # Save the index in a way that avoids serializing full objects
        try:
            with open(self.index_file, 'w') as file:
                json.dump(self.root.to_dict(), file, indent=4)
        except Exception as e:
            print(f"Error saving index: {e}")

    def load_index(self):
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r') as file:
                    data = json.load(file)
                self.root = self._rebuild_from_data(data)
            except Exception as e:
                print(f"Error loading index: {e}")
        else:
            print("No index file found. Starting with an empty index.")

    def _rebuild_from_data(self, data):
        node = BPlusTreeNode(is_leaf=data["is_leaf"])
        node.keys = [(k, v) for k, v in data["keys"]]
        if not node.is_leaf:
            node.children = [self._rebuild_from_data(child) for child in data["children"]]
            for child in node.children:
                child.parent = node
        return node
    
    def remove(self, key, doc_id=None):
        leaf_node = self._find_leaf_node(key)
        original_len = len(leaf_node.keys)

        # If doc_id is provided, remove exact match; else remove all entries with that key
        if doc_id is not None:
            for i, (k, doc_ids) in enumerate(leaf_node.keys):
                if k == key and doc_id in doc_ids:
                    doc_ids.remove(doc_id)
                    if not doc_ids:
                        leaf_node.keys.pop(i)  # Remove the key if no doc_ids remain
                    break
        else:
            leaf_node.keys = [(k, doc_ids) for (k, doc_ids) in leaf_node.keys if k != key]

        if len(leaf_node.keys) < original_len:
            print(f"Removed key={key} doc_id={doc_id}")
        else:
            print(f"No matching entry found for key={key} doc_id={doc_id}")

        self.save_index()


