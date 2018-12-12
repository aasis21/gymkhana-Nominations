import pprint
import requests
from bs4 import BeautifulSoup, Comment
import re


def getRecord(username):
    roll = str(username)

    req = requests.get("https://search.pclub.in/api/student", params={'username':roll})
    soup = BeautifulSoup(req.text,"lxml")
    record = {}

    data = soup.findChildren('p')
    datalist = data[0].text.split('","')
    datalist = [ word.split(':"')[1] for word in datalist ]
    record['email'] = roll+"@iitk.ac.in"
    
    record['roll']= datalist[5]
    image = 'http://oa.cc.iitk.ac.in/Oa/Jsp/Photo/' + datalist[5] + '_0.jpg'
    record['image'] = image

    if not record['roll']:
        return None

    record['program'] = datalist[7]

    record['department'] = datalist[2]

    record['hall'] = datalist[4]
    record['room'] = datalist[8]
    record['name'] = datalist[6]
    record['blood'] = datalist[1]
    record['gender'] = datalist[3]
    record['mobile'] = "0000000000"
    print(record)
    return record
