from .transaction import TransactionManager
def query_processor(dbms):
    transaction_manager = TransactionManager(dbms.root_path)  # Create a TransactionManager instance
    print("\n--- Query Mode (type 'exit' to quit) ---")
    while True:
        query = input(">> ").strip()
        if query.lower() == 'exit':
            transaction_manager.rollback()  # Manually call cleanup before exiting
            break
        process_query(query, dbms, transaction_manager)


def process_query(query, dbms,transaction_manager):
    tokens = query.split()
    if not tokens:
        raise SyntaxError("Empty query")  # No query

    cmd = tokens[0].lower()
    results = []
    if cmd == "begin":
            # Begin a new transaction
        transaction_manager.begin()

    elif cmd == "commit":
            # Commit the transaction
        transaction_manager.commit()

    elif cmd == "rollback":
            # Rollback the transaction
        transaction_manager.rollback()
        
    if cmd == "create":
        if tokens[1].lower() == "database":
            return dbms.create_database(tokens[2])
            
        elif tokens[1].lower() == "collection":
            db = dbms.get_current_database()
            if db:
                return db.create_collection(tokens[2])
                
        elif tokens[1].lower() == "index":
            # Ensure the format is correct: CREATE INDEX <index_name> ON <collection_name> (<attribute_name>)
            if len(tokens) != 6 or tokens[3].lower() != "on":
                print("Error: Invalid CREATE INDEX query format")
                return

            index_name = tokens[2]             # idx_rollno
            collection_name = tokens[4]        # Student
            attribute_token = tokens[5]        # (rollno)

            if not (attribute_token.startswith("(") and attribute_token.endswith(")")):
                print("Error: Invalid attribute format. Use (attribute_name)")
                return

            attribute_name = attribute_token[1:-1]  # Strip parentheses

            db = dbms.get_current_database()
            if db:
                collection = db.get_collection(collection_name)
                if collection:
                    collection.create_index(attribute_name)
                    print(f"Index '{index_name}' created on attribute '{attribute_name}' in collection '{collection_name}'.")
                else:
                    print(f"Collection '{collection_name}' not found.")
            else:
                print("No database selected.")


                
    elif cmd == "use":
        if len(tokens) >= 3 and tokens[1].lower() == "database":
            db_name = tokens[2]
            if not dbms.set_current_database(db_name):
                return None  # Invalid DB
        else:
            return None  # Invalid syntax

    elif cmd == "insert":
        if tokens[1].lower() == "into":
            collection_name = tokens[2]
            fields = {k: v for kv in tokens[3:] if '=' in kv for k, v in [kv.split('=')]}
            db = dbms.get_current_database()
            if db:
                collection = db.get_collection(collection_name)
                if collection:
                    message, inserted = collection.create_object(**fields)
                    return {"message": message, "records": inserted}
            raise ValueError("Collection not found.")

    elif cmd == "show":
        if len(tokens) < 2:
            raise SyntaxError("Missing keyword after SHOW")
        elif tokens[1].lower() == "databases":
            databases = dbms.show_databases()
            return [{"Database": name} for name in databases]

        elif tokens[1].lower() == "collections":
            db = dbms.get_current_database()
            if db:
                collections = db.show_all_collections()
                return [{"Collection": name} for name in collections]
            else:
                raise SyntaxError("No database selected")
        elif len(tokens) >= 3 and tokens[2].lower() == "records":
            collection_name = tokens[1]
            db = dbms.get_current_database()
            if not db:
                return None

            collection = db.get_collection(collection_name)
            if not collection:
                raise SyntaxError("Collection don't exist.")

            fields = None
            condition_str = ""
            sort_key = None
            sort_order = "asc"
            offset = 0
            limit = None

            # Convert query to lowercase for keywords but preserve original tokens for values
            lower_tokens = [token.lower() for token in tokens]

            # Handle SELECT fields
            if "select" in lower_tokens:
                select_index = lower_tokens.index("select")
                end_index = min([lower_tokens.index(kw) for kw in ["where", "sortby", "offset", "limit"] if kw in lower_tokens and lower_tokens.index(kw) > select_index] + [len(tokens)])
                fields = tokens[select_index + 1:end_index]

            # Handle WHERE condition
            if "where" in lower_tokens:
                where_index = lower_tokens.index("where")
                end_index = min([lower_tokens.index(kw) for kw in ["sortby", "offset", "limit"] if kw in lower_tokens and lower_tokens.index(kw) > where_index] + [len(tokens)])
                condition_str = " ".join(tokens[where_index + 1:end_index])

            # Handle SORTBY key [asc|desc]
            if "sortby" in lower_tokens:
                sort_index = lower_tokens.index("sortby")
                sort_key = tokens[sort_index + 1]
                if len(tokens) > sort_index + 2 and tokens[sort_index + 2].lower() in ["asc", "desc"]:
                    sort_order = tokens[sort_index + 2].lower()

            # Handle OFFSET
            if "offset" in lower_tokens:
                try:
                    offset = int(tokens[lower_tokens.index("offset") + 1])
                except:
                    offset = 0

            # Handle LIMIT
            if "limit" in lower_tokens:
                try:
                    limit = int(tokens[lower_tokens.index("limit") + 1])
                except:
                    limit = None

            records =  collection.find_with_conditions(condition_str, fields, sort_key, sort_order, offset, limit)
            message = f"{len(records)} record(s) found." if records else "No records found."
            return {"message": message, "records": records}

    elif cmd == "update":
        collection_name = tokens[1]
        if tokens[2].lower() == "set":
            update_key, update_value = tokens[3].split("=")
            if tokens[4].lower() == "where":
                cond_key, cond_value = tokens[5].split("=")
                db = dbms.get_current_database()
                if db:
                    collection = db.get_collection(collection_name)
                    if collection:
                        message, updated_records = collection.update(
                            {cond_key: cond_value}, {update_key: update_value}
                        )
                        return {"message": message, "records": updated_records}


    elif cmd == "delete":
        if tokens[1].lower() == "from":
            collection_name = tokens[2]
            if tokens[3].lower() == "where":
                key, value = tokens[4].split("=")
                db = dbms.get_current_database()
                if db:
                    collection = db.get_collection(collection_name)
                    if collection:
                        collection.delete({key: value})
                        
        elif tokens[1].lower() == "database":
            dbms.delete_database(tokens[2])   
            
        elif tokens[1].lower() == "collection":
            db = dbms.get_current_database()
            if db:
                return db.delete_collection(tokens[2])  

    elif cmd == "rename":
        if tokens[1].lower() == "database":
            dbms.rename_database(tokens[2], tokens[4])
        elif tokens[1].lower() == "collection":
            db = dbms.get_current_database()
            if db:
                db.rename_collection(tokens[2], tokens[4])
    
    elif cmd == "drop" and tokens[1].lower() == "index":
        index_name = tokens[2].lower()
        collection_name = tokens[4]

        db = dbms.get_current_database()
        if db:
            collection = db.get_collection(collection_name)
            if collection:
                collection.remove_index(index_name)
                print(f"Index '{index_name}' has been dropped from '{collection_name}'.")
            else:
                print(f"Collection '{collection_name}' not found.")
        else:
            print("No active database found.")
   

    return results if results else None
