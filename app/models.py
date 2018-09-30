from app import db, login, app
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from marshmallow import Schema, fields
from flask_login import UserMixin
from sqlalchemy import func
import phonenumbers

# --- MODELS ---

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128))
    is_verified = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, username, email):
        self.username = username
        self.email = email

    def __repr__(self):
        return '<User {} {}>'.format(self.username, self.email)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def save(self):
        db.session.add(self)
        db.session.commit()


class PhoneNumber(db.Model):
    __tablename__ = "phone_numbers"
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.Unicode(20), index=True, unique=True)
    nickname = db.Column(db.String(30))
    messages = db.relationship("Message", back_populates="phone_number", lazy='dynamic')

    def __init__(self, phone_number):
        self.phone_number = phone_number

    def __repr__(self):
        e164_number = phonenumbers.format_number(phonenumbers.parse(self.phone_number, 'US'),
                                                 phonenumbers.PhoneNumberFormat.E164)
        return '<PhoneNumber {}>'.format(e164_number)

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def number_exists(phone_number):
        phone_number = phonenumbers.format_number(phonenumbers.parse(phone_number, 'US'), phonenumbers.PhoneNumberFormat.E164)
        return PhoneNumber.query.filter_by(phone_number=phone_number).count()

class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    phone_number_id = db.Column(db.Integer, db.ForeignKey('phone_numbers.id'))
    message_text = db.Column(db.String(255))
    phone_number = db.relationship('PhoneNumber', back_populates="messages")
    sequence = db.Column(db.Integer)

    def __init__(self, phone_number_id, message_text):
        self.phone_number_id = phone_number_id
        self.message_text = message_text
        self.sequence = (db.session.query(func.max(Message.sequence)).scalar() or 0) + 1

    def __repr__(self):
        return '<Message {} {}>'.format(self.phone_number.phone_number, self.message_text, self.sequence)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def insert_in_sequence(self, new_sequence):
        if new_sequence < self.sequence:
            for row in Message.query.filter(Message.sequence >= new_sequence, Message.sequence < self.sequence):
                row.sequence = row.sequence + 1
                db.session.commit()
        else:
            for row in Message.query.filter(Message.sequence > self.sequence, Message.sequence <= new_sequence):
                row.sequence = row.sequence - 1
                db.session.commit()
        self.sequence = new_sequence
        db.session.commit()

    def delete(self):
        sequence = self.sequence
        db.session.delete(self)
        db.session.commit()
        for row in Message.query.filter(Message.sequence > sequence):
            row.sequence = row.sequence - 1
            db.session.commit()


# --- SCHEMAS ---


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str()
    email = fields.Str()
    is_verified = fields.Bool()

class PhoneNumberSchema(Schema):
    id = fields.Int(dump_only=True)
    phone_number = fields.Str()

class MessageSchema(Schema):
    id = fields.Int(dump_only=True)
    sequence = fields.Int()
    message_text = fields.Str()
    phone_number = fields.Nested(PhoneNumberSchema)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
