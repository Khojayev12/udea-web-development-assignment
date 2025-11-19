from flask import Flask, render_template, redirect, request, url_for, jsonify, session
from werkzeug.security import check_password_hash, generate_password_hash
from dbhandler import DBHandler
app = Flask(__name__)
app.secret_key = "mytestkey"
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



@app.route('/signout', methods=['GET', 'POST'])
def signout():
    if request.method == 'POST':
        session.clear()
    return redirect(url_for('index'))



@app.route('/')
def index():
    return render_template('pages/home.html')


@app.route('/feed')
def feed():
    return render_template('pages/feed.html')


@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('pages/home.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('pages/profile.html')

@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('pages/add.html')

@app.route('/notifications', methods=['GET', 'POST'])
def notifications():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('pages/notifications.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        user_id = authenticate_user(email, password)
        if user_id:
            app.user_id = user_id
            session['user'] = user_id
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


if __name__ == '__main__':
    app.run(debug=True)
