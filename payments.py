import base64, datetime, os
from flask import request,make_response
from flask_restful import Resource
from dotenv import load_dotenv
from models import Payment,db,Order,OrderProducts
import requests
from flask_jwt_extended import get_jwt_identity,jwt_required

load_dotenv() #parses contents in the .env file and makes available the variables in that file
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

def create_password(shortcode,passkey,timestamp):
    plain_text = shortcode+passkey+timestamp
    bytes_obj = bytes(plain_text, 'utf-8')
    bs4 = base64.b64encode(bytes_obj)
    bs4 = bs4.decode()
    return bs4

def format_phone_number(number):
    number_str=str(number)
    if number_str.startswith('07') or number_str.startswith('01'):
        return int('254' + number_str[1:])
    
    elif number_str.startswith('254'):
        return int(number_str)
    else:
        return None
    
    
class Initiate_Payment(Resource):
    #To post a payment, we need a reference to its order
    #post an order and consecutively post a payment and update the two accordingly after the response from the payment api
    @jwt_required()
    def post(self):
        data=request.get_json()
        print(data)
        if not all(attr in data for attr in ['amount','shipping_address','products',"taxes","phone_number"]):
            return make_response({"msg":"Required data is missing"},400)
        
        #validate phone number and amount received for the purpose of proceeding witht th etransaction
        number=data["phone_number"]
        amount=data["amount"]
        if not format_phone_number(number=number):
            return make_response({"msg":"Invalid phone number"},400)
        if not str(amount).isdigit():
            return make_response({"msg":"Invalid amount"},400)
        #create the order first
        new_order=Order(amount=data.get("amount"),status="Pending",taxes=data.get("taxes"),shipping_address=data.get("shipping_address"),
                            date=datetime.datetime.now(),user_id=get_jwt_identity(),payment_status="Pending")
        db.session.add(new_order)
        db.session.commit()
        #get the products key, an array of product details to be associated with the newly created order
        products=data.get("products") #an array of product details that are specific to the order created above
        for item in products:
            new_order_product=OrderProducts(product_id=item.get("product_id"),quantity=item.get("quantity"),order_id=new_order.id)
            db.session.add(new_order_product)
            db.session.commit()
        order_id=new_order.id
        
        formated_phone_number=format_phone_number(number=number)
        time=generate_timestamp()
        password=create_password("174379","bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919",time)
        payload={    
                "BusinessShortCode": 174379,    
                "Password":password,
                "Timestamp":time,    
                "TransactionType": "CustomerPayBillOnline",    
                "Amount": amount,    
                "PartyA":"254708374149",    
                "PartyB":174379,
                "PhoneNumber":formated_phone_number,    
                "CallBackURL": "https://gizmo.nullchemy.com/payment-result",    
                "AccountReference":"Test",    
                "TransactionDesc":"Payment for gizmo galaxy"
                }
        token = authorization('https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials')
        headers={"Authorization": 'Bearer '+token}
        res = requests.post('https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest', headers=headers, json=payload)
        response_data=res.json()
        #create a payment record that will be updated once the callback url is called
        new_transaction=Payment(transaction_id=response_data.get("CheckoutRequestID"),order_id=order_id,
                                    date=datetime.datetime.now(),status="Processing",amount=amount)
        db.session.add(new_transaction)
        db.session.commit()
        print(new_order.to_dict())
        return make_response(new_order.to_dict(),res.status_code)
    
class Payment_result(Resource):
    def post(self):
        #update  the order and payment records accordingly
        callback_data=request.json
        checkout_request_id = callback_data['Body']['stkCallback']['CheckoutRequestID']
        result_code=callback_data["Body"]["stkCallback"]["ResultCode"]
        transaction=Payment.query.filter_by(transaction_id=checkout_request_id).first()
        if not transaction:
            return make_response({"msg":"Transaction not found"},400)
        order=Order.query.filter_by(id=transaction.order_id).first()
        if result_code!=0:
            setattr(transaction,"status","Failed")
            setattr(order,"payment_status","Failed")
            db.session.commit()
            return make_response(order.to_dict(),200)
        setattr(transaction,"status","Success")
        setattr(order,"payment_status","Success")
        db.session.commit()
        return make_response(order.to_dict(),200)