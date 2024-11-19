from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import validates
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_serializer import SerializerMixin

metadata = MetaData()

db = SQLAlchemy(metadata=metadata)

class User(db.Model,SerializerMixin):
    __tablename__='users'

    id=db.Column(db.Integer,primary_key=True)
    first_name=db.Column(db.String, nullable=False)
    last_name=db.Column(db.String, nullable=False)
    email=db.Column(db.String, unique=True)
    password=db.Column(db.String,nullable=False)
    role=db.Column(db.String,nullable=False)
    status=db.Column(db.String, nullable=False)
    date_created=db.Column(db.DateTime)
    #Relationships
    products=db.relationship('Product',back_populates='admin')
    user_review=db.relationship("Review",back_populates="user")
    orders=db.relationship('Order',back_populates='user')
    #Serialize Rules
    serialize_rules=('-products','-user_review.user','-orders.user','-password')

class Product(db.Model,SerializerMixin):
    __tablename__="products"

    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String, nullable=False, unique=True)
    description=db.Column(db.String, nullable=False)
    category_id=db.Column(db.String,db.ForeignKey("categories.id"))
    purchase_price=db.Column(db.Float, nullable=False)
    purchase_price_excl_tax=db.Column(db.Float,nullable=False)
    selling_price=db.Column(db.Float, nullable=False)
    selling_price_excl_tax=db.Column(db.Float,nullable=False)
    discount=db.Column(db.Float, default=0)
    quantity=db.Column(db.Integer,default=0)
    rating=db.Column(db.Float, default=0)
    added_by=db.Column(db.Integer,db.ForeignKey('users.id'))
    tax_id=db.Column(db.Integer,db.ForeignKey("taxes.id"))
    date_added=db.Column(db.DateTime)
    #Relationships
    category=db.relationship("Category",back_populates="products")
    admin=db.relationship('User',back_populates='products') #points to the admin who added the product
    image_url=db.relationship("Images",back_populates='product')
    product_reviews=db.relationship("Review",back_populates="product")
    orders=db.relationship("OrderProducts", back_populates='product')
    features=db.relationship("Feature",back_populates='product')
    tax=db.relationship("Tax",back_populates="products")
    #serialize rules
    # serialize_rules=('-admin','-image_url.product','-product_reviews.product','-orders.product','-categories.products','-features.product','-tax',
    #                  '-category.products','-category_id','-category.id')
    serialize_only=('description','name','id','purchase_price',"purchase_price_excl_tax","selling_price","selling_price_excl_tax",
                    'quantity','category.name','image_url.image_url','features.description')

class Images(db.Model,SerializerMixin):
    #stores image urls of uploaded images relating to a certain product
    __tablename__='images'

    id=db.Column(db.Integer, primary_key=True)
    image_url=db.Column(db.String, nullable=False)
    product_id=db.Column(db.Integer, db.ForeignKey('products.id'))
    #Relationships
    product=db.relationship("Product",back_populates='image_url')

    #serialize rules
    serialize_rules=('-product',)

class Review(db.Model,SerializerMixin):
    __tablename__='reviews'

    id=db.Column(db.Integer,primary_key=True)
    rating=db.Column(db.Integer,nullable=False)
    description=db.Column(db.String(100))
    # status=db.Column(db.String)
    user_id=db.Column(db.Integer, db.ForeignKey('users.id'))
    product_id=db.Column(db.Integer, db.ForeignKey("products.id"))
    date_created=db.Column(db.DateTime)
    #Relationships
    user=db.relationship("User",back_populates="user_review")
    product=db.relationship("Product",back_populates='product_reviews')

    #serialize rules
    serialize_rules=('-user','-product')

class Order(db.Model,SerializerMixin):
    __tablename__='orders'

    id=db.Column(db.Integer, primary_key=True)
    amount=db.Column(db.Integer)
    status=db.Column(db.String)
    taxes=db.Column(db.Float)
    shipping_address=db.Column(db.String, nullable=False)
    date=db.Column(db.DateTime)
    user_id=db.Column(db.Integer, db.ForeignKey("users.id"))

    #relationships
    user=db.relationship("User",back_populates='orders')
    products=db.relationship("OrderProducts",back_populates='order')
    payment=db.relationship("Payment",back_populates='order')
    sale=db.relationship("Sales",back_populates="order")

    #serialize rules
    serialize_rules=("-user.orders",'-products.order','-payment.order','-sale.order',
                     '-products.id','-products.order_id','-sale')

class OrderProducts(db.Model,SerializerMixin):
    __tablename__='orderproducts'

    id=db.Column(db.Integer, primary_key=True)
    product_id=db.Column(db.Integer, db.ForeignKey("products.id"))
    order_id=db.Column(db.Integer, db.ForeignKey("orders.id"))
    quantity=db.Column(db.Integer, nullable=False)
    #relationships
    product=db.relationship("Product", back_populates='orders')
    order=db.relationship("Order", back_populates="products")

    #serialize rules
    serialize_rules=('-product.orders','-order')

class Payment(db.Model,SerializerMixin):
    __tablename__='payments'

    id=db.Column(db.Integer, primary_key=True)
    amount=db.Column(db.Integer, nullable=False)
    transaction_id=db.Column(db.String)
    order_id=db.Column(db.Integer, db.ForeignKey("orders.id"))
    #relationships
    order=db.relationship("Order", back_populates="payment")

    #serialize rules
    serialize_rules=('-order.payment')

class Category(db.Model,SerializerMixin):
    __tablename__='categories'

    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String, nullable=False)
    description=db.Column(db.String)
    #relationships
    products=db.relationship("Product",back_populates="category")
    #seriaise rules
    serialize_rules=('-products.category',)

class Feature(db.Model,SerializerMixin):
    __tablename__='features'

    id=db.Column(db.Integer,primary_key=True)
    description=db.Column(db.String,nullable=False)
    product_id=db.Column(db.Integer,db.ForeignKey("products.id"))
    #relationships
    product=db.relationship("Product",back_populates="features")
    #serialise rules
    serialize_rules=('-product',)

class Tax(db.Model,SerializerMixin):
    __tablename__='taxes'

    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String, nullable=False)
    value=db.Column(db.Float,nullable=False)
    #relationships
    products=db.relationship("Product",back_populates='tax')
    #serialise rules
    serialize_rules=('-products',)

class Sales(db.Model,SerializerMixin):
    __tablename__='sales'

    id=db.Column(db.Integer,primary_key=True)
    date=db.Column(db.DateTime,nullable=False)
    order_id=db.Column(db.Integer,db.ForeignKey("orders.id"))

    #relationships
    order=db.relationship("Order", back_populates="sale")
    #serialise rules
    serialize_rules=('-order.sale')