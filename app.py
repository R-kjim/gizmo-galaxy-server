from models import db,User,Product,Payment,OrderProducts,Review,Images,Order,Feature
from flask_migrate import Migrate
from flask import Flask, request, make_response,jsonify
from flask_restful import Api, Resource
from flask_jwt_extended import JWTManager,create_access_token, create_refresh_token,jwt_required,get_jwt_identity
import secrets,datetime,os
from datetime import timedelta
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash,generate_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get(
    "DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")
    # "DB_URI", f"postgresql://robert:d0KU0b3VMlQkb6t4eH7qwyqUaNxDHdJx@dpg-csouttd6l47c73969tg0-a/gizmo_315a")

#upload images assist
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static')
ALLOWED_EXTENSIONS=set(['png','jpeg','jpg'])
def allowed_file(filename):
    return '.' in filename and filename.rsplit(".",1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] =secrets.token_hex(32)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=30)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER


migrate = Migrate(app, db)

db.init_app(app)
api=Api(app)
jwt=JWTManager(app)

# CORS(app, resources={r"/elections/*": {"origins": "https://electra-dummy-1.onrender.com"}})

class Home(Resource):
    def get(self):
        return make_response({"msg":"Homepage here"},200)

api.add_resource(Home,'/')
class Signup(Resource):
    def post(self):
        data=request.get_json()
        email=data.get("email")
        f_name=data.get("first_name")
        l_name=data.get("last_name")
        date=datetime.datetime.now()
        password=generate_password_hash(data.get("password"))
        role=data.get("role")
        if "@" in email and f_name and f_name!=" " and l_name and l_name!=" " and role and role!=" " and data.get("password") and data.get("password")!=" ":
            user=User.query.filter_by(email=email).first()
            if user:
                return make_response({"msg":f"{email} is already registered"},400)
            new_user=User(first_name=f_name,last_name=l_name,email=email,password=password,date_created=date,role=role)
            db.session.add(new_user)
            db.session.commit()
            return make_response(new_user.to_dict(),201)
        return make_response({"msg":"Invalid data entries"},400)
api.add_resource(Signup,'/signup')

class Login(Resource):
    def post(self):
        data=request.get_json()
        email=data.get("email")
        password=data.get("password")
        if "@" in email and password:
            user=User.query.filter_by(email=email).first()
            if user:
                if check_password_hash(user.password,password):
                    access_token=create_access_token(identity=user.id)
                    refresh_token=create_refresh_token(identity=user.id)
                    return make_response({"user":user.to_dict(),"access_token":access_token,"refresh_token":refresh_token},200)
                return make_response({"msg":"Incorrect password"},400)
            return make_response({"msg":"email not registered"},404)
        return make_response({"msg":"Invalid data"})
api.add_resource(Login,'/login')

class Product_By_Id(Resource):
    def get(self,id):
        product=Product.query.filter_by(id=id).first()
        if product:
            return make_response(product.to_dict(),200)
        return make_response({"msg":"Product not found"},404)
    def delete(self,id):
        product=Product.query.filter_by(id=id).first()
        if product:
            db.session.delete(product)
            db.session.commit()
            return make_response({"msg":"Product deleted successfully"},204)
        return make_response({"msg":"Product not found"},404)
    def patch(self,id):
        product=Product.query.filter_by(id=id).first()
        if product:
            data=request.get_json()
            #update product attributes only
            for attr in data:
                if attr in ['name','description','category_id','purchase_price','selling_price','discount','quantity','tax_id']:
                    setattr(product,attr,data.get(attr))
                db.session.add(product)
                db.session.commit()
                if attr=='features':
                    for feature in data.get("features"):
                        new_feature=Feature(description=feature,product_id=product.id)
                        db.session.add(new_feature)
                        db.session.commit()
                if attr=='images':
                    for image in data.get("images"):
                        new_image=Images(image_url=image,product_id=product.id)
                        db.session.add(new_image)
                        db.session.commit()
            return make_response(product.to_dict(),200)
        return make_response({"msg":"Product not found"},404)
api.add_resource(Product_By_Id,'/product/<int:id>')


class Add_Get_Product(Resource):
    def get(self):
        products=Product.query.all()
        return make_response([product.to_dict() for product in products],200)
    
    @jwt_required()
    def post(self):
        id=get_jwt_identity()
        if id:
            data=request.get_json()
            if 'name' in data and 'description' in data and 'category_id' in data and 'purchase_price' in data and 'selling_price' in data and 'images' in data and 'features' in data:
                new_product=Product(name=data.get("name"),description=data.get("description"),category_id="category_id",purchase_price=data.get("purchase_price"),
                                    selling_price=data.get("selling_price"),quantity=data.get("quantity",0),added_by=id,
                                    tax_id=data.get("tax_id",None),date_added=datetime.datetime.now())
                db.session.add(new_product)
                db.session.commit()
                images=data.get("images") #an array of images urls
                #loop through the images array to post each image and associate it with the newly added product
                for image in images:
                    new_image=Images(image_url=image,product_id=new_product.id)
                    db.session.add(new_image)
                    db.session.commit()
                features=data.get("features") #an array of product features
                #loop through the features array and add each feature, associating it with the newly added product
                for feature in features:
                    new_feature=Feature(description=feature,product_id=new_product.id)
                    db.session.add(new_feature)
                    db.session.commit()
                return make_response(new_product.to_dict(),201)
            return make_response({"msg":"Required data missing"},400)
        return make_response({"msg":"User session expired"},400)   
api.add_resource(Add_Get_Product,'/products')


if __name__=="__main__":
    app.run(debug=True)