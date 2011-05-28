from dingus import Dingus, DingusTestCase
from nose.tools import assert_raises

from scalymongo.connection import DocumentProxy, Connection
import scalymongo.connection as mod


class DescribeConnectionClass(object):

    def should_extend_pymongo_connection(self):
        assert issubclass(Connection, mod.pymongo.Connection)


class BaseConnectionTest(DingusTestCase(Connection)):

    def setup(self):
        super(BaseConnectionTest, self).setup()
        # Resetting this back to the old __init__ seems to break
        # DescribeConnectionClass.
        Connection.__init__ = Dingus(return_value=None)
        self.connection = Connection()


class DescribeConnectDocument(BaseConnectionTest):

    def setup(self):
        BaseConnectionTest.setup(self)
        class MyDoc(object):
            pass
        self.document = MyDoc

        self.returned = self.connection.connect_document(self.document)

    def should_return_subclass_of_original(self):
        assert issubclass(self.returned, self.document)

    def should_set_connection_on_returned(self):
        assert self.returned.connection == self.connection


class DescribeModelsGetter(BaseConnectionTest):

    def setup(self):
        BaseConnectionTest.setup(self)

        self.returned = self.connection.models

    def should_create_document_proxy(self):
        assert mod.DocumentProxy.calls(
            '()', self.connection, mod.get_concrete_classes())

    def should_return_document_proxy(self):
        assert mod.DocumentProxy.calls('()').once()
        assert self.returned == mod.DocumentProxy()


class DescribeDocumentProxyInit(object):

    def setup(self):
        self.connection = Dingus('connection')
        self.registered = [
            Dingus(__name__='0'), Dingus(__name__='1'), Dingus(__name__='2')]

        self.returned = DocumentProxy(self.connection, self.registered)

    def should_save_connection(self):
        assert self.returned.connection == self.connection

    def should_map_concrete_names_to_classes(self):
        assert self.returned.registered == {
            '0': self.registered[0],
            '1': self.registered[1],
            '2': self.registered[2],
        }


class DescribeDocumentProxy(object):

    def setup(self):
        self.connection = Dingus('connection')
        self.registered = Dingus('registered')
        self.document_proxy = DocumentProxy(self.connection, self.registered)


class WhenGettingUnregisteredItem(DescribeDocumentProxy):

    def should_raise_key_error(self):
        assert_raises(KeyError, self.document_proxy.__getitem__, 'Document')


class WhenGettingUnregisteredViaAttr(DescribeDocumentProxy):

    def should_raise_key_error(self):
        assert_raises(AttributeError, getattr, self.document_proxy, 'Document')


class BaseDocumentRegistered(DescribeDocumentProxy):

    def setup(self):
        DescribeDocumentProxy.setup(self)
        self.cls = Dingus('Document')
        self.document_proxy.registered['Document'] = self.cls

    def should_connect_document(self):
        assert self.connection.calls('connect_document', self.cls)

    def should_return_connected_document(self):
        assert self.connection.calls('connect_document').once()
        assert self.returned == self.connection.connect_document()


class WhenGettingItem(BaseDocumentRegistered):

    def setup(self):
        BaseDocumentRegistered.setup(self)
        self.returned = self.document_proxy['Document']


class WhenGettingAttr(BaseDocumentRegistered):

    def setup(self):
        BaseDocumentRegistered.setup(self)
        self.returned = self.document_proxy.Document