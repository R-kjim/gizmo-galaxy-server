import base64, datetime, os
from flask import request,make_response
from flask_restful import Resource
from dotenv import load_dotenv
import requests


load_dotenv()#parses contents in the .env file and makess it available in that file
