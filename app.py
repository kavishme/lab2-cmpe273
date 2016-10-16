import logging
import requests
import re
import operator
from datetime import datetime
from spyne import Application, srpc, ServiceBase, Decimal, String, Double # Iterable, UnsignedInteger, String

from spyne.protocol.json import JsonDocument
from spyne.protocol.http import HttpRpc
from spyne.server.wsgi import WsgiApplication


class CrimeReportService(ServiceBase):
    __service_name__ = "crimereport"

    @srpc(Decimal, Decimal, Decimal, _returns=String)
    def checkcrime(lat, lon, radius):
        try:
            url = "https://api.spotcrime.com/crimes.json?lat={0}&lon={1}&radius={2}&key=.".format(lat,lon,radius)
            data = requests.get(url).json()

            totalcrime = 0
            crimetypecount = {}
            eventtimecount = [0,0,0,0,0,0,0,0]
            addresscount = {}
            AddGrpIndex = 0
            stRegex = r'(?:.*BLOCK OF\s)?((?:\w+\s){1,3}(?:(?:ST)|(?:AV)|(?:BLVD)|(?:DR)|(?:WY)|(?:RD)|(?:LOOP)|(?:PL)|(?:AL)|(?:LN)|(?:CT)))'
            #r'(([NSEW]\s)(\w+\s){1,}((ST)|(AV)|(BLVD)|(DR)))|(\w+\s((ST)|(AV)|(BLVD)|(DR)))'
            regexp = re.compile(stRegex, re.I|re.U)
            crimes = data['crimes']

            for crime in crimes:
                logging.info(crime)
                #if not crime['address'] or not crime['date'] or not crime['type']:
                #    continue
                matchobject = regexp.match(crime['address'])
                if matchobject:
                    logging.info(matchobject.groups())
                else:
                    logging.info("None Match")

                totalcrime += 1

                if matchobject and matchobject.groups()[AddGrpIndex]:
                    address = matchobject.groups()[AddGrpIndex]
                else:
                    address = crime['address']

                #if not(addresscount[address]):
                #   addresscount[address] = 0
                #else:

                addresscount[address] = addresscount.get(address,0) + 1
                #if not(crimetypecount[crime['type']]):
                #    crimetypecount[crime['type']] = 0
                #else:

                crimetypecount[crime['type']] = crimetypecount.get(crime['type'],0) + 1
                #if not(eventtimecount[crime['date']]):
                #    eventtimecount[crime['date']] = 0
                #else:

                dt = datetime.strptime(crime['date'], '%m/%d/%y %I:%M %p')
                eventtimecount[dt.hour/3] += 1

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
            adrslst = []
            for adrs in addSorted[:3]:
                adrslst.append(adrs[0])

            result = {
                     "total_crime" : totalcrime,
                     "the_most_dangerous_streets" : adrslst,
                     "crime_type_count" : crimetypecount,
                     "event_time_count" : {
                         '12.01am-3am':eventtimecount[0],
                         '3.01am-6am':eventtimecount[1],
                         '6.01am-9am':eventtimecount[2],
                         '9.01am-12noon':eventtimecount[3],
                         '12.01pm-3pm':eventtimecount[4],
                         '3.01pm-6pm':eventtimecount[5],
                         '6.01pm-9pm':eventtimecount[6],
                         '9.01pm-12midnight':eventtimecount[7]
                     }
                     }
            #logging.info(result)
           # logging.info(totalcrime)
            logging.info(addSorted)
            #logging.info(crimetypecount)
           # logging.info(eventtimecount)
            return result
        except Exception as e:
            logging.error(e)
            return e


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
