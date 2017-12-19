

class InstanceInfo(object):
    """Standardise Instance details relevant during XML generation."""

    def __init__(self, type, context, name, unique_id, instance):
        self.type = type
        self.context = context
        self.name = name
        self.unique_id = unique_id
        self.instance = instance
