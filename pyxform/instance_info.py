

class InstanceInfo(object):
    """Standardise Instance details relevant during XML generation."""

    def __init__(self, type, context, name, instance):
        self.type = type
        self.context = context
        self.name = name
        self.instance = instance
