from lib2to3 import fixer_base
from lib2to3.pgen2 import token


class FixUnicode(fixer_base.BaseFix):
    """
    Renames:
       def __unicode__(self):
    to:
       def __str__(self):

    2to3 already handles converting unicode() to str().
    """

    _accept_type = token.NAME

    def match(self, node):
        if node.value == '__unicode__':
            return True
        return False

    def transform(self, node, results):
        node.value = '__str__'
        node.changed()
