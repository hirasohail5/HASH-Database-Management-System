import uuid

class Object:
    def __init__(self, **attributes):
        self.id = str(uuid.uuid4())  # Unique ID for each object
        self.attributes = attributes  # A dictionary of attribute names and values

    def to_dict(self):
        """Return only JSON-serializable attributes."""
        return self.attributes
