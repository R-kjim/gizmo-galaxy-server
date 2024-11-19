import base64, datetime, os
from flask import request,make_response
from flask_restful import Resource
from dotenv import load_dotenv
import requests


load_dotenv()#parses contents in the .env file and makess it available in that file
#get the variables as declared
consumer_key=os.getenv("Consumer_key") 
consumer_secret_key=os.getenv("Consumer_secret")

def authorization(url):
    plain_text=f'{consumer_key}:{consumer_secret_key}'
    bytes_obj=bytes(plain_text,'utf-8')
    bs4=base64.b64encode(bytes_obj)
    bs4str=bs4.decode()
    headers={
        'Authorization':'Basic ' + bs4str
    }
    res=requests.get(url,headers=headers)
    return res.json().get('access_token')

def generate_timestamp():
    time=datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    return time

