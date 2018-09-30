import os
import jwt
import datetime
from flask import render_template, redirect, request, url_for, flash, make_response, jsonify, json
from flask_login import current_user, login_user, logout_user, login_required
from twilio.request_validator import RequestValidator

from app.forms import LoginForm
from app.forms import RegistrationForm
from app.models import User, PhoneNumber, Message, UserSchema, PhoneNumberSchema, MessageSchema
from werkzeug.urls import url_parse
from functools import wraps
from twilio.twiml.messaging_response import MessagingResponse
from app import app, db

user_schema = UserSchema()
users_schema = UserSchema(many=True)
phone_number_schema = PhoneNumberSchema()
phone_numbers_schema = PhoneNumberSchema(many=True)
message_schema = MessageSchema()
messages_schema = MessageSchema(many=True)


@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    login_form = LoginForm(prefix="login-form")
    register_form = RegistrationForm()
    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()
        if user is None or not user.check_password(login_form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=login_form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', login_form=login_form, register_form=register_form)


@app.route('/register', methods=['POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    register_form = RegistrationForm()
    login_form = LoginForm()
    if register_form.validate_on_submit():
        user = User(username=register_form.username.data, email=register_form.email.data)
        user.set_password(register_form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations {}, you are now a registered user!'.format(user.username))
        return redirect(url_for('login'))
    return render_template('login.html', title='Sign In', login_form=login_form, register_form=register_form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/messages', methods=["GET"])
@login_required
def get_messages():
    messages = Message.query.order_by(Message.sequence).all()
    result = messages_schema.dump(messages).data
    return jsonify({'messages': result})


@app.route('/delete/message/<int:message_id>', methods=['DELETE'])
@login_required
def delete_message(message_id):
    message = Message.query.get(message_id)
    if message:
        message.delete()
        return jsonify({'message': 'message deleted successfully'}), 200
    return jsonify({'message': 'message does not exist'}), 400


@app.route('/update/message-sequence', methods=["POST", "GET"])
@login_required
def update_message_sequence():
    print(request.json)
    if not request.json or not 'message_id' in request.json or not 'new_sequence' in request.json:
        return make_response('Missing arguments', 400)
    message_id = request.json['message_id']
    message = Message.query.get(message_id)
    if message is None:
        return make_response('That message does not exist', 404)
    message.insert_in_sequence(request.json['new_sequence'])
    return make_response('Sequence successfully updated', 200)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        print("header")
        print(auth_header)
        if auth_header:
            auth_token = auth_header.split(" ")[1]
        else:
            auth_token = ''
        if not auth_token:
            return jsonify({'message': 'Token is missing!'}), 403
        print(auth_token)
        try:
            data = jwt.decode(auth_token, app.config['SECRET_KEY'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 403
        return f(*args, **kwargs)

    return decorated

def validate_twilio_request(f):
    """Validates that incoming requests genuinely originated from Twilio"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Create an instance of the RequestValidator class
        validator = RequestValidator(os.environ.get('TWILIO_AUTH_TOKEN'))

        # Validate the request using its URL, POST data,
        # and X-TWILIO-SIGNATURE header
        request_valid = validator.validate(
            request.url,
            request.form,
            request.headers.get('X-TWILIO-SIGNATURE', ''))

        # Continue processing the request if it's valid, return a 403 error if
        # it's not
        if request_valid:
            return f(*args, **kwargs)
        else:
            return jsonify({'message': 'Unable to validate twilio request'}), 403
    return decorated_function

@app.route('/api/login', methods=['POST'])
def api_login():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    email = request.json.get('email', None)
    password = request.json.get('password', None)
    if not email:
        return jsonify({"msg": "Missing email parameter"}), 400
    if not password:
        return jsonify({"msg": "Missing password parameter"}), 400
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        access_token = jwt.encode({'user': user.username,
                                   'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)},
                                  app.config['SECRET_KEY']).decode('utf-8')

        return jsonify({
            'message': 'Logged in as {}'.format(user.username),
            'access_token': access_token,
        }), 200
    return jsonify({'message': 'Wrong credentials'}), 401

    # Identity can be any data that is json serializable
    access_token = create_access_token(identity=email)
    return jsonify(access_token=access_token), 200


@app.route('/api/register/phone-number', methods=["POST"])
@token_required
def register_phone_number():
    if not request.json or not 'phone_number' in request.json or not 'secret_code' in request.json:
        return make_response('Missing arguments', 400)

    if request.json['secret_code'] == os.environ['SECRET_CODE']:
        phone_number = PhoneNumber.query.filter_by(phone_number=request.json['phone_number']).first()
        if phone_number is not None:
            return make_response('PhoneNumber already exists', 400)
        phone_number = PhoneNumber(request.json['phone_number'])
        phone_number.save()
        result = phone_number_schema.dump(phone_number).data
        return jsonify(result)
    else:
        return make_response('Invalid secret_code', 404)


@app.route('/api/users', methods=["GET"])
@token_required
def get_users():
    users = User.query.all()
    result = users_schema.dump(users).data
    return jsonify({'users': result})


@app.route('/api/users/<username>', methods=["GET"])
@token_required
def get_user(username):
    user = User.query.filter_by(username=username).first()
    if user is not None:
        result = user_schema.dump(user).data
        return jsonify(result)
    return make_response('No user found with that username', 404)


@app.route('/api/create/message', methods=["POST"])
@token_required
def create_message():
    if not request.json or not 'phone_number' in request.json or not 'message_text' in request.json:
        return make_response('Missing arguments', 400)
    phone_number = PhoneNumber.query.filter_by(phone_number=request.json['phone_number']).first()
    if phone_number is not None:
        m = Message(phone_number.id, request.json['message_text'])
        if len(m.message_text) > 255:
            return make_response('Message text is too long', 400)
        db.session.add(m)
        db.session.commit()
        return make_response('Message added', 200)
    else:
        return make_response('Phone number not whitelisted', 401)


@app.route('/api/phone-numbers', methods=["GET"])
@login_required
def get_phone_numbers():
    phone_numbers = PhoneNumber.query.all()
    result = phone_numbers_schema.dump(phone_numbers).data
    return jsonify({'phone_numbers': result})


@app.route('/api/messages', methods=["GET"])
@token_required
def api_get_messages():
    messages = Message.query.order_by(Message.sequence).all()
    result = messages_schema.dump(messages).data
    return jsonify({'messages': result})


@app.route('/api/pop-message', methods=["GET"])
@token_required
def api_pop_message():
    message = Message.query.order_by(Message.sequence).first()
    result = message_schema.dump(message).data
    message.delete()
    return jsonify(result)


@validate_twilio_request
@app.route('/sms', methods=['GET', 'POST'])
def handle_sms():
    from_number = request.values.get('From')
    body = request.values.get('Body', None)
    resp = MessagingResponse()
    if PhoneNumber.number_exists(from_number):
        if body != '':
            phone_number = PhoneNumber.query.filter_by(phone_number=from_number).first()
            m = Message(phone_number.id, body)
            if len(m.message_text) < 255:
                resp.message('Bleep bloop, your message has been added to the queue.')
                m.save()
            else:
                resp.message('Your message is too long! Please send one with fewer than 255 characters')
        else:
            resp.message('Your message is empty!')
    elif body == app.config['SECRET_CODE']:
        resp.message('You have submitted the correct message, your number is now in the whitelist. You may send a '
                     'message to be added to the Greeterbot queue.')
        p = PhoneNumber(from_number)
        p.save()
    else:
        resp.message('Your phone number is not in the whitelist. Please send the secret message to be added.')

    return str(resp)
