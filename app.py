from flask import Flask, render_template, redirect, request, url_for

app = Flask(__name__)

@app.route('/')
def index():
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
        # TODO: implement registration logic
        return redirect(url_for('login'))
    return render_template('pages/signup.html')

if __name__ == '__main__':
    app.run(debug=True)
