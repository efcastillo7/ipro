import json
import urllib2 as ur
import csv

switches_url=ur.urlopen('http://localhost:8080/stats/switches')
L=json.loads(switches_url.read())
for switch_no in L:
	port_url=ur.urlopen('http://localhost:8080/stats/port/'+ str(switch_no))
	#f=ur.urlopen(url)
	#print url.read()
	port_parsed = json.loads(port_url.read())

	port_data = port_parsed['1']

	# open a file for writing

	port_stat_data = open('port_flow_'+str(switch_no)+'.csv', 'w')

	# create the csv writer object

	csvwriter = csv.writer(port_stat_data)

	count = 0

	for flow in port_data:

	      if count == 0:

	             header = flow.keys()

	             csvwriter.writerow(header)

	             count += 1

	      csvwriter.writerow(flow.values())

	port_stat_data.close()