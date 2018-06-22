#!/usr/bin/env python
"""
https://github.com/vidhiJain/ryu_application
This is a simple web "crawler" that fetches a bunch of urls using a pool to
control the number of outbound connections. It has as many simultaneously open
connections as coroutines in the pool.

The prints in the body of the fetch function are there to demonstrate that the
requests are truly made in parallel.
"""
import eventlet
import requests
import csv
import time
#s_no=1
flag=1
s=requests.Session()
baseurl='http://localhost:8080/stats/'
switches_url=baseurl+'switches'
switch_list=s.get(switches_url)

files_list=['port','aggregateflow','flow']
urls = []
sl=switch_list.json()
for i in files_list:
	for s_no in switch_list.json():
		#fp=open(i+'_'+str(s_no)+'.csv', 'a')
		urls += [baseurl+i+'/'+str(s_no)]

def fetch(url):
#print("opening", url)
	global flag
	r = s.get(url)
	body=r.json()
	sno=url[-1]
	data=body[sno]
	fp=open(url[len(baseurl):-2]+'_'+sno+'.csv', 'a')
	if fp.tell()==0:
		flag=0
	csvwriter=csv.writer(fp)
	for item in data:
		if flag == 0:
			csvwriter.writerow(item.keys())
			flag=1
	   	csvwriter.writerow(item.values())
	return url

pool = eventlet.GreenPool(200)
while(1):
	for url in pool.imap(fetch, urls):
 		time.sleep(0.5)
 	

    
	