from flask import Flask, render_template, redirect, request, url_for, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from dbhandler import DBHandler
app = Flask(__name__)

mydb = DBHandler()


def create_user_account(name: str, email: str, password: str) -> bool:
    """Create a new user account and return True on success."""
    if not all([name, email, password]):
        return False
    hashed_password = generate_password_hash(password)
    return mydb.register_new_user(name.strip(), email.strip().lower(), hashed_password)


def authenticate_user(email: str, password: str):
    """Return the user_id if credentials are valid, otherwise None."""
    if not all([email, password]):
        return None
    user_record = mydb.check_user_login(email.strip().lower())
    if user_record and check_password_hash(user_record[1], password):
        return user_record[0]
    return None


@app.route('/')
def index():
    return render_template('pages/home.html')


@app.route('/feed')
def feed():
    return render_template('pages/feed.html')


@app.route('/home', methods=['GET', 'POST'])
def home():
    print("home: ", getattr(app, 'user_id', None))
    if request.method == 'POST':
        # TODO: implement authentication logic
        return redirect(url_for('index'))
    return render_template('pages/home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        user_id = authenticate_user(email, password)
        if user_id:
            app.user_id = user_id
            return redirect(url_for('home'))
        return render_template('pages/login.html', error='Invalid email or password.')
    return render_template('pages/login.html', error=None)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        created = create_user_account(name, email, password)
        if created:
            return redirect(url_for('login'))
        return render_template(
            'pages/signup.html',
            error='Unable to create account, please try again.'
        )
    return render_template('pages/signup.html', error=None)


# test: http://127.0.0.1:5000/api/login?email=emily.thompson@example.com&password=pbkdf2_sha256$demo$emily
# API CALLS


@app.route('/api/login', methods=['GET'])
def loginApi():
    if request.method == 'GET':
        user_email = request.args.get('email', None)
        user_password = request.args.get('password', None)
        user_id = authenticate_user(user_email, user_password)
        if user_id:
            app.user_id = user_id
            return redirect(url_for('home'))
        return render_template('pages/login.html', error='Invalid email or password.')
    return render_template('pages/login.html', error=None)


@app.route('/api/signup', methods=['POST'])
def signupApi():
    if request.method == 'POST':
        payload = request.get_json(silent=True) or request.form
        user_email = payload.get('email')
        user_name = payload.get('name')
        user_password = payload.get('password')
        created = create_user_account(user_name, user_email, user_password)
        if created:
            return jsonify({'message': 'User created'}), 201
        return jsonify({'message': 'Unable to create account'}), 400
    return jsonify({'message': 'Unsupported method'}), 405


if __name__ == '__main__':
    app.run(debug=True)
