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


# adding comment, making change
@app.route('/signout', methods=['GET', 'POST'])
def signout():
    if request.method == 'POST':
        session.clear()
    return redirect(url_for('index'))

def test_git():
    pass

@app.route('/')
def index():
    return render_template('pages/home.html')


@app.route('/feed')
def feed():
    return render_template('pages/feed.html')


@app.route('/recipe/<int:recipe_id>')
def recipe(recipe_id: int):
    recipe_data = {
        "id": recipe_id,
        "title": "Chicken Pasta",
        "rating": 4.5,
        "rating_count": 146,
        "image": url_for('static', filename='media/registration.png'),
        "ingredients": [
            "225g fettuccine or any pasta of your choice",
            "450g boneless, skinless chicken breasts, cut into bite-sized pieces",
            "salt",
            "black pepper",
            "2 tablespoons olive oil",
            "3 cloves garlic, minced",
            "240ml heavy cream",
            "100g grated parmesan cheese",
            "fresh parsley, chopped (for garnish)",
            "tomato, chopped (for garnish)",
        ],
        "nutrition": [
            {"label": "Protein", "value": "45g"},
            {"label": "Carbs", "value": "50g"},
            {"label": "Fats", "value": "40g"},
            {"label": "Sugar", "value": "2g"},
            {"label": "Fiber", "value": "3g"},
        ],
        "stats": [
            {"label": "Ingredients", "value": "8"},
            {"label": "Minutes", "value": "15"},
            {"label": "Calories", "value": "720"},
        ],
        "steps": [
            {
                "title": "Cook the Pasta",
                "items": [
                    "Cook the pasta according to the package instructions. Drain and set aside.",
                ],
            },
            {
                "title": "Cook the Chicken",
                "items": [
                    "Season chicken pieces with salt and pepper.",
                    "In a pan, heat olive oil over medium heat.",
                    "Add chicken and cook until browned and fully cooked. Set aside.",
                ],
            },
            {
                "title": "Make the Alfredo Sauce",
                "items": [
                    "In the same pan, add minced garlic and sauté for 1 minute.",
                    "Pour in the heavy cream and bring to a gentle simmer.",
                    "Stir in Parmesan cheese until melted and the sauce is smooth.",
                ],
            },
            {
                "title": "Combine and Serve",
                "items": [
                    "Add the cooked chicken to the sauce.",
                    "Toss in the cooked pasta until well coated.",
                    "Garnish with chopped parsley.",
                    "Enjoy your quick and tasty Easy Chicken Alfredo Pasta!",
                ],
            },
        ],
        "tags": ["pasta", "chicken pasta", "pasta recipe", "creamy pasta", "homemade dinner", "quick & easy"],
        "reviews": [
            {"author": "Name", "rating": 5, "content": "Lorem ipsum dolor sit amet consectetur. Fusce orci elementum eu tortor blandit. Et sollicitudin quis cras tellus. Nam tristique faucibus ultrices sit dictum senectus."},
            {"author": "Name", "rating": 5, "content": "Lorem ipsum dolor sit amet consectetur. Fusce orci elementum eu tortor blandit. Et sollicitudin quis cras tellus. Nam tristique faucibus ultrices sit dictum senectus. Quam sed pulvinar ipsum tortor vulputate quis mattis."},
            {"author": "Name", "rating": 5, "content": "Lorem ipsum dolor sit amet consectetur. Fusce orci elementum eu tortor blandit."},
        ],
    }
    return render_template('pages/recipe.html', recipe=recipe_data)


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
