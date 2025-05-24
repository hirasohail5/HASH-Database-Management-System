import os
import shutil
import atexit
import signal
import sys

class TransactionManager:
    def __init__(self, root_path="."):
        self.root_path = root_path
        self.backup_path = os.path.join(self.root_path, "__backup")
        self.transaction_active = False
        self.transaction_committed = False

        # Register cleanup function for graceful shutdown
        atexit.register(self.cleanup)

        # Register a handler for abrupt program termination (e.g., Ctrl+C, etc.)
        signal.signal(signal.SIGTERM, self.handle_termination)
        signal.signal(signal.SIGINT, self.handle_termination)

    def begin(self):
        if self.transaction_active:
            print("Transaction already in progress.")
            return

        if os.path.exists(self.backup_path):
            shutil.rmtree(self.backup_path)  # Clean old backup

        # Make deep copy of the root DBMS folder
        os.makedirs(self.backup_path, exist_ok=True)

        for item in os.listdir(self.root_path):
            src = os.path.join(self.root_path, item)
            dest = os.path.join(self.backup_path, item)

            # Skip backup folder itself and Python files
            if item == "__backup" or item.endswith(".py") or item == "__pycache__":
                continue

            if os.path.isdir(src):
                shutil.copytree(src, dest)
            elif os.path.isfile(src):
                shutil.copy2(src, dest)

        self.transaction_active = True
        print("Transaction started.")

    def commit(self):
        if not self.transaction_active:
            print("No active transaction to commit.")
            return

        shutil.rmtree(self.backup_path)
        self.transaction_active = False
        print("Transaction committed.")
        
        
    def rollback(self):
        if not self.transaction_active:
            print("No active transaction to rollback.")
            return

        # Delete current data
        for item in os.listdir(self.root_path):
            path = os.path.join(self.root_path, item)
            if item == "__backup" or item.endswith(".py") or item == "__pycache__":
                continue
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                elif os.path.isfile(path):
                    os.remove(path)
            except Exception as e:
                print(f"Failed to remove {path}: {e}")

        # Restore backup
        for item in os.listdir(self.backup_path):
            src = os.path.join(self.backup_path, item)
            dest = os.path.join(self.root_path, item)
            if os.path.isdir(src):
                shutil.copytree(src, dest)
            else:
                shutil.copy2(src, dest)

        shutil.rmtree(self.backup_path)
        self.transaction_active = False
        print("Transaction rolled back.")


    def create_backup(self):
        """Create a deep copy (backup) of the database system"""
        if not os.path.exists(self.backup_path):
            os.makedirs(self.backup_path)
        # Create a backup of your DBMS (implement according to your system)
        print(f"Backup folder created at {self.backup_path}")

    def restore_backup(self):
        """Restore the backup"""
        if os.path.exists(self.backup_path):
            print(f"Restoring backup from {self.backup_path}")
            # Restore logic (copy data back)
            shutil.rmtree(self.backup_path)  # Assuming you want to delete after restoring

    def apply_changes(self, dbms):
        """Apply changes made during the transaction (e.g., commit changes to DBMS)"""
        print("Changes have been applied to the database.")

    def cleanup(self):
        """Clean up the backup if no commit or rollback occurred."""
        if self.transaction_active and not self.transaction_committed:
            print(f"Transaction ended without commit or rollback. Cleaning up backup folder at {self.backup_path}")
            shutil.rmtree(self.backup_path, ignore_errors=True)  # Delete the backup folder
        else:
            print(f"Transaction committed or rolled back, no need to clean up backup.")


    def handle_termination(self, signum, frame):
        """Handle abrupt program termination (e.g., SIGINT, SIGTERM)."""
        print("Program is terminating abruptly. Cleaning up backup folder...")
        self.cleanup()
        sys.exit(1)  # Exit the program after cleanup
