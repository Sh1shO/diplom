from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

# Настройка базы данных (предполагается PostgreSQL)
engine = create_engine('postgresql://acbs:1234@95.174.93.180:5432/magazin')
Base = declarative_base()
# Функция для получения сессии базы данных
Session = sessionmaker(bind=engine)

# Модель для таблицы Пользователь
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True)
    password = Column(String)
    role_id = Column(Integer, ForeignKey('role.id'))

    # Связи
    role = relationship("Role", back_populates="users")

# Модель для таблицы Роль
class Role(Base):
    __tablename__ = 'role'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    # Связь с Пользователь (один ко многим)
    users = relationship("User", back_populates="role")

# Модель для таблицы ЕдиницыИзмерения
class Unit(Base):
    __tablename__ = 'unit'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    # Связь с Товары (один ко многим)
    products = relationship("Product", back_populates="unit")

# Модель для таблицы ТипыТоваров
class ProductType(Base):
    __tablename__ = 'product_type'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    # Связь с Товары (один ко многим)
    products = relationship("Product", back_populates="type")

# Модель для таблицы УсловияПоставки
class DeliveryCondition(Base):
    __tablename__ = 'delivery_condition'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    # Связь с Товары (один ко многим)
    products = relationship("Product", back_populates="condition")

# Модель для таблицы Поставщики
class Supplier(Base):
    __tablename__ = 'supplier'
    id = Column(Integer, primary_key=True, autoincrement=True)
    inn = Column(String)
    name = Column(String)
    phone = Column(String)

    # Связь с Поставки (один ко многим)
    deliveries = relationship("Delivery", back_populates="supplier")

# Модель для таблицы Товары
class Product(Base):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    unit_id = Column(Integer, ForeignKey('unit.id'))
    type_id = Column(Integer, ForeignKey('product_type.id'))
    condition_id = Column(Integer, ForeignKey('delivery_condition.id'))

    # Связи
    unit = relationship("Unit", back_populates="products")
    type = relationship("ProductType", back_populates="products")
    condition = relationship("DeliveryCondition", back_populates="products")
    product_in_deliveries = relationship("ProductInDelivery", back_populates="product")

# Модель для таблицы Поставки
class Delivery(Base):
    __tablename__ = 'delivery'
    id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_id = Column(Integer, ForeignKey('supplier.id'))
    planned_date = Column(Date)
    actual_date = Column(Date)
    doc_number = Column(String)
    doc_date = Column(Date)

    # Связи
    supplier = relationship("Supplier", back_populates="deliveries")
    product_in_deliveries = relationship("ProductInDelivery", back_populates="delivery")

# Модель для таблицы ТоварыВПоставке
class ProductInDelivery(Base):
    __tablename__ = 'product_in_delivery'
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('product.id'))
    delivery_id = Column(Integer, ForeignKey('delivery.id'))
    planned_quantity = Column(Integer)
    planned_price = Column(Integer)
    actual_quantity = Column(Integer)
    actual_price = Column(Integer)

    # Связи
    product = relationship("Product", back_populates="product_in_deliveries")
    delivery = relationship("Delivery", back_populates="product_in_deliveries")

# Создание таблиц в базе данных
Base.metadata.create_all(engine)