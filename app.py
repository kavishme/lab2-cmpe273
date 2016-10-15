import logging
import requests
import re
from spyne import Application, srpc, ServiceBase, Decimal # Iterable, UnsignedInteger, String

from spyne.protocol.json import JsonDocument
from spyne.protocol.http import HttpRpc
from spyne.server.wsgi import WsgiApplication


class CrimeReportService(ServiceBase):
    __service_name__ = "crimereport"

    @srpc(Decimal, Decimal, Decimal, _returns=String)
    def checkcrime(lat, lon, rad):
        url = "https://api.spotcrime.com/crimes.json?lat={0}&lon={1}&radius={2}&key=.".format(lat,lon,rad)
        data = requests.get(url).json()

        totalcrime = 0
        crimetypecount = {}
        eventtimecount = {}
        addresscount = {}
        AddGrpIndex = 1
        stRegex = r'(([NSEW]\s)(\w+\s){1,}((ST)|(AV)))|(\w+\s((ST)|(AV)))'
        for crime in data['crimes']:
            matchobject = re.match(stRegex, crime.address)
            print(matchobject)

            totalcrime++
            address = !matchobject[AddGrpIndex] ? crime.address : matchobject[AddGrpIndex]
            !addresscount[address] &&  ? addresscount[address] = 0 : addresscount[address] += 1
            !crimetypecount[crime.type] ? crimetypecount[crime.type] = 0 : crimetypecount[crime.type] += 1
            !eventtimecount[crime.date] ? eventtimecount[crime.date] = 0 : eventtimecount[crime.date] += 1

         #{"total_crime" : 24
         #   "the_most_dangerous_streets" : [ "E SANTA CLARA ST", "E SAN FERNANDO ST" , "N 11TH ST" ],
         #   "crime_type_count" : {
         #       "Assault" : 10,
         #       "Arrest" : 8,
         #       "Burglary" : 6,
         #       "Robbery" : 4,
         #       "Theft" : 2,
         #       "Other" : 1
         #        },
         #   "event_time_count" : {
         #       "12:01am-3am" : 5,
         #       "3:01am-6am" : 0,
         #       "6:01am-9am" : 1,
         #       "9:01am-12noon" : 2,
         #       "12:01pm-3pm" : 2,
         #       "3:01pm-6pm" : 1,
         #       "6:01pm-9pm" : 0,
         #       "9:01pm-12midnight" : 9
         #       }
         #   }
        addSorted = sorted(addresscount.items(), key=operator.itemgetter(1), reverse = True)
        result = {
                 "total_crime" : totalcrime,
                 "the_most_dangerous_streets" : addSorted[:3],
                 "crime_type_count" : crimetypecount,
                 "event_time_count" : eventtimecount
                 }

        return result


if __name__=='__main__':
    from wsgiref.simple_server import make_server
    logging.basicConfig(level=logging.DEBUG)

    # Instantiate the application by giving it:
    #   * The list of services it should wrap,
    #   * A namespace string.
    #   * An input protocol.
    #   * An output protocol.
    application = Application([CrimeReportService], 'cmpe273.lab2.httprpc',
            # The input protocol is set as HttpRpc to make our service easy to
            # call. Input validation via the 'soft' engine is enabled. (which is
            # actually the the only validation method for HttpRpc.)
            in_protocol=HttpRpc(validator='soft'),

            # The ignore_wrappers parameter to JsonDocument simplifies the reponse
            # dict by skipping outer response structures that are redundant when
            # the client knows what object to expect.
            out_protocol=JsonDocument(ignore_wrappers=True),)

    # Now that we have our application, we must wrap it inside a transport.
    # In this case, we use Spyne's standard Wsgi wrapper. Spyne supports 
    # popular Http wrappers like Twisted, Django, Pyramid, etc. as well as
    # a ZeroMQ (REQ/REP) wrapper.
    wsgi_application = WsgiApplication(application)

    # More daemon boilerplate
    server = make_server('127.0.0.1', 8000, wsgi_application)

    logging.info("listening to http://127.0.0.1:8000")
    logging.info("wsdl is at: http://localhost:8000/?wsdl")

    server.serve_forever()
