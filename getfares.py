#!/usr/bin/python
# https://github.com/czivar

# How to use:
# 1 - Modify script for your needs
# 2 - Run it: ./getfares.py

import urllib, urllib2, json, sys
from lxml import etree

# Script parameters
# Get your API key at http://api.staging.cleartrip.com/register
api_key = 'xxxxxxxxxxxxxxx'

api_url = 'http://api.staging.cleartrip.com/air/1.0/search'
params = {
    'from' : 'GLA',
    'to' : 'BUD',
    'depart-date' : '2013-12-12',
    'adults' : 1,
    'children' : 0,
    'infants' : 0,
    #'carrier' : 'KL', # Airline specification
    'sort' : 'asc'
}
currency = 'GBP'
number_of_results = 30

# Initialize and place cleartip API request, returns everything that CT sends
def call_api():
    request = urllib2.Request(api_url+'?'+urllib.urlencode(params))
    request.add_header('X-CT-API-KEY', api_key) 
    return urllib2.urlopen(request).read()

# Currency convert
def get_rate():
    curl = 'http://rate-exchange.appspot.com/currency?from=INR&to=' + currency
    crequest = urllib2.urlopen(curl)
    rate_dict = json.loads(crequest.read())
    return rate_dict['rate']

# This function gets the interesting information from the XML object
def get_solutions(xml, change_rate):
    results = []
    for solution in xml.xpath("//*/solution"):
        price = solution.find('pricing-summary').find('total-fare').text
        flights = solution.find('flights').find('flight')
        segments = flights.find('segments')
        departure_time = segments.find('segment').find('departure-date-time').text
        arrival_time = segments.find('segment').find('arrival-date-time').text
        departure_airport = segments.find('segment').find('departure-airport').text
        route = departure_airport
        for segment in segments.iterchildren('segment'):
            airline = segment.find('airline').text
            route = route + '-(' + airline + ')-' + segment.find('arrival-airport').text
            arrival_time = segment.find('arrival-date-time').text
        cprice = float(price) * change_rate
        results.append([departure_time, arrival_time, route, str(round(cprice, 2)) + ' ' +currency])
    return results

# Print list of lists into tables
def print_results(table):
    table.insert(0, ['Departure', 'Arrival', 'Route (Airline)', 'Fare'])
    width_list = [max(len(x) for x in col) for col in zip(*table)]
    for line in table:
        print "| " + " | ".join("{0:{1}}".format(x, width_list[i]) 
            for i, x in enumerate(line)) + " |"

try:
    # Call CT API
    response = call_api()
    # Get rid of the annoying namespace
    response = response.replace(' xmlns=', ' xmlnamespace=')
    xml = etree.fromstring(response)
    change_rate = get_rate()
    results = get_solutions(xml, change_rate)
    
    #Printing out the results
    sol_from = 0
    sol_to = number_of_results
    print_results(results[sol_from:sol_to])
    while( raw_input('Show more (y/n): ') == 'y' and sol_to < len(results)):
        sol_from = sol_to
        sol_to += number_of_results
        print_results(results[sol_from:sol_to])

except etree.XMLSyntaxError:
    # A simple plain error message can arrive
    print response.strip()
except urllib2.HTTPError as e:
    # CT or currency change API call fails (e.g. invalid parameters)
    print e
except KeyError as e:
    # KeyError from get_rate (e.g. invalid currency)
    print e
except urllib2.URLError as e:
    # URL error
    print e
