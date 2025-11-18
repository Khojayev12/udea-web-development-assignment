from flask import Flask, render_template, redirect, request, url_for
from dbhandler import DBHandler
app = Flask(__name__)

mydb = DBHandler()

@app.route('/')
def index():
    return render_template('pages/home.html')


@app.route('/home', methods=['GET', 'POST'])
def home():
    print("home: ", app.user_id)
    if request.method == 'POST':
        # TODO: implement authentication logic
        return redirect(url_for('index'))
    return render_template('pages/home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # TODO: implement authentication logic
        return redirect(url_for('index'))
    return render_template('pages/login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        return redirect(url_for('login'))
    return render_template('pages/signup.html')

# test: http://127.0.0.1:5000/api/login?email=emily.thompson@example.com&password=pbkdf2_sha256$demo$emily
# API CALLS

@app.route('/api/login', methods=['GET'])
def loginApi():
    if request.method == 'GET':
        user_email = request.args.get('email', None)
        user_password = request.args.get('password', None)
        check_result = mydb.check_user_login(user_email, user_password)
        print(check_result)
        app.user_id = check_result
        #return home(check_result)
        # TODO: implement authentication logic
        return redirect(url_for('home'))
    return render_template('pages/login.html')



@app.route('/api/signup', methods=['POST'])
def signupApi():
    if request.method == 'POST':
        # TODO: implement registration logic 
        return redirect(url_for('login'))
    return render_template('pages/signup.html')




if __name__ == '__main__':
    app.run(debug=True)
