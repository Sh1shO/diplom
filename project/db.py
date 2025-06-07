from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

# Настройка базы данных (предполагается PostgreSQL)
engine = create_engine('postgresql://postgres:1234@localhost:5432/diplom')
Base = declarative_base()
# Функция для получения сессии базы данных
Session = sessionmaker(bind=engine)

# Модель для таблицы Расшифровка
class Decoding(Base):
    __tablename__ = 'decoding'
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String)
    short_name = Column(String)

    # Связь с Учреждение (один ко многим)
    institutions = relationship("Institution", back_populates="decoding")

# Модель для таблицы Учреждение
class Institution(Base):
    __tablename__ = 'institution'
    id = Column(Integer, primary_key=True, autoincrement=True)
    decoding_id = Column(Integer, ForeignKey('decoding.id'))
    name = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))

    # Связи
    decoding = relationship("Decoding", back_populates="institutions")
    user = relationship("User", back_populates="institutions")
    events = relationship("Event", back_populates="organizer")
    attendances = relationship("Attendance", back_populates="institution")

# Модель для таблицы Пользователь
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True)
    password = Column(String)
    role_id = Column(Integer, ForeignKey('role.id'))

    # Связи
    role = relationship("Role", back_populates="users")
    institutions = relationship("Institution", back_populates="user")

# Модель для таблицы Роль
class Role(Base):
    __tablename__ = 'role'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    # Связь с Пользователь (один ко многим)
    users = relationship("User", back_populates="role")

# Модель для таблицы ФорматыМероприятий
class EventFormat(Base):
    __tablename__ = 'event_format'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    # Связь с Мероприятия (один ко многим)
    events = relationship("Event", back_populates="format")

# Модель для таблицы КлассификацииМероприятий
class EventClassification(Base):
    __tablename__ = 'event_classification'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    # Связь с Мероприятия (один ко многим)
    events = relationship("Event", back_populates="classification")

# Модель для таблицы НаправленияДеятельности
class ActivityDirection(Base):
    __tablename__ = 'activity_direction'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    # Связь с Мероприятия (один ко многим)
    events = relationship("Event", back_populates="direction")

# Модель для таблицы ФормаМероприятия
class EventType(Base):
    __tablename__ = 'event_type'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    # Связь с Мероприятия (один ко многим)
    events = relationship("Event", back_populates="event_type")

# Модель для таблицы ЦелеваяАудитория
class TargetAudience(Base):
    __tablename__ = 'target_audience'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    # Связь с Мероприятия (один ко многим)
    events = relationship("Event", back_populates="target_audience")

# Модель для таблицы МестоПроведения
class Venue(Base):
    __tablename__ = 'venue'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    # Связь с Мероприятия (один ко многим)
    events = relationship("Event", back_populates="venue")

# Модель для таблицы Мероприятия
class Event(Base):
    __tablename__ = 'event'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date)
    venue_id = Column(Integer, ForeignKey('venue.id'))
    organizer_id = Column(Integer, ForeignKey('institution.id'))
    event_type_id = Column(Integer, ForeignKey('event_type.id'))
    name = Column(String)
    description = Column(String)
    target_audience_id = Column(Integer, ForeignKey('target_audience.id'))
    format_id = Column(Integer, ForeignKey('event_format.id'))
    classification_id = Column(Integer, ForeignKey('event_classification.id'))
    direction_id = Column(Integer, ForeignKey('activity_direction.id'))

    # Связи
    venue = relationship("Venue", back_populates="events")
    organizer = relationship("Institution", back_populates="events")
    event_type = relationship("EventType", back_populates="events")
    target_audience = relationship("TargetAudience", back_populates="events")
    format = relationship("EventFormat", back_populates="events")
    classification = relationship("EventClassification", back_populates="events")
    direction = relationship("ActivityDirection", back_populates="events")
    attendances = relationship("Attendance", back_populates="event")

# Модель для таблицы Посещения
class Attendance(Base):
    __tablename__ = 'attendance'
    id = Column(Integer, primary_key=True, autoincrement=True)
    institution_id = Column(Integer, ForeignKey('institution.id'))
    event_id = Column(Integer, ForeignKey('event.id'))
    total_attendees = Column(Integer)  # Охват (Количество посетителей)
    child_attendees = Column(Integer)  # ДетейПосетителей
    volunteers = Column(Integer)  # КоличествоВолонтёров
    at_risk_teens = Column(Integer)  # ПодросткиГруппыРиска

    # Связи
    institution = relationship("Institution", back_populates="attendances")
    event = relationship("Event", back_populates="attendances")

# Создание таблиц в базе данных
Base.metadata.create_all(engine)

