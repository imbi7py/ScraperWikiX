# You can run this .tac file directly with:
#    twistd -ny datastore.tac

"""
This is the tac file for the datastore
"""
from twisted.application import service, internet
from twisted.python.log import ILogObserver, FileLogObserver
from twisted.python.logfile import DailyLogFile
from twisted.web import server, resource

from datastore import DatastoreFactory
from webdatastore import WebDatastoreResource

application = service.Application("datastore")

# attach the service to its parent application
service = service.MultiService()

port = 10000
ds_factory = DatastoreFactory()
ds_service = internet.TCPServer(port, ds_factory)
ds_service.setServiceParent( service )

root = resource.Resource()
root.putChild("", WebDatastoreResource())
internet.TCPServer(20000, server.Site(root)).setServiceParent(application)


service.setServiceParent(application)