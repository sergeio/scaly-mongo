import pymongo

from scalymongo.document import get_concrete_classes


class Connection(pymongo.Connection):

    def connect_document(self, document):
        """Connect a document by injecting this connection into it.
        """
        class _ConnectedDocument(document):
            connection = self
        return _ConnectedDocument

    @property
    def models(self):
        return DocumentProxy(self, get_concrete_classes())


class DocumentProxy(object):
    """A proxy object for accessing or creating :class:`Document` models."""

    def __init__(self, connection, registered):
        self.connection = connection
        self.registered = {}
        for cls in registered:
            self.registered[cls.__name__] = cls

    def __getitem__(self, name):
        cls = self._find_document_class(name)
        if not cls:
            raise KeyError('Unknown document {0}'.format(repr(name)))
        return cls

    def __getattr__(self, name):
        cls = self._find_document_class(name)
        if not cls:
            raise AttributeError('Unknown document {0}'.format(repr(name)))
        return cls

    def _find_document_class(self, name):
        cls = self.registered.get(name)
        if not cls:
            return None
        return self.connection.connect_document(cls)