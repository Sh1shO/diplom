from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# Database configuration (PostgreSQL)
engine = create_engine('postgresql://postgres:1234@localhost:5432/asd')
Base = declarative_base()
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True)
    password = Column(String)
    role_id = Column(Integer, ForeignKey('role.id'))
    can_edit = Column(Integer, default=0)  # 0: False, 1: True
    can_delete = Column(Integer, default=0)
    can_view = Column(Integer, default=1)  # By default, users can view
    role = relationship("Role", back_populates="users")

class Role(Base):
    __tablename__ = 'role'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    users = relationship("User", back_populates="role")

class Unit(Base):
    __tablename__ = 'unit'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    products = relationship("Product", back_populates="unit")

class ProductType(Base):
    __tablename__ = 'product_type'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    products = relationship("Product", back_populates="type")

class DeliveryCondition(Base):
    __tablename__ = 'delivery_condition'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    products = relationship("Product", back_populates="condition")

class Supplier(Base):
    __tablename__ = 'supplier'
    id = Column(Integer, primary_key=True, autoincrement=True)
    inn = Column(String)
    name = Column(String)
    phone = Column(String)
    deliveries = relationship("Delivery", back_populates="supplier")

class Product(Base):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    unit_id = Column(Integer, ForeignKey('unit.id'))
    type_id = Column(Integer, ForeignKey('product_type.id'))
    condition_id = Column(Integer, ForeignKey('delivery_condition.id'))
    unit = relationship("Unit", back_populates="products")
    type = relationship("ProductType", back_populates="products")
    condition = relationship("DeliveryCondition", back_populates="products")
    product_in_deliveries = relationship("ProductInDelivery", back_populates="product")

class Delivery(Base):
    __tablename__ = 'delivery'
    id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_id = Column(Integer, ForeignKey('supplier.id'))
    planned_date = Column(Date)
    actual_date = Column(Date)
    doc_number = Column(String)
    supplier = relationship("Supplier", back_populates="deliveries")
    product_in_deliveries = relationship("ProductInDelivery", back_populates="delivery")

class ProductInDelivery(Base):
    __tablename__ = 'product_in_delivery'
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('product.id'))
    delivery_id = Column(Integer, ForeignKey('delivery.id'))
    planned_quantity = Column(Integer)
    planned_price = Column(Integer)
    actual_quantity = Column(Integer)
    actual_price = Column(Integer)
    rejection_reason = Column(String, nullable=True)  # New column for rejection reason
    product = relationship("Product", back_populates="product_in_deliveries")
    delivery = relationship("Delivery", back_populates="product_in_deliveries")

# Create tables
Base.metadata.create_all(engine)