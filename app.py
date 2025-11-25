from flask import Flask, render_template, redirect, request, url_for, jsonify, session, abort
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
    recent_recipes = mydb.fetch_recent_recipes()
    more_recipes = mydb.fetch_more_recipes()
    popular_recipes = mydb.fetch_popular_recipes()
    return render_template('pages/home.html', recent_recipes=recent_recipes, more_recipes=more_recipes, popular_recipes=popular_recipes)


@app.route('/feed')
def feed():
    category = request.args.get('category') or None
    difficulty = request.args.get('difficulty') or None
    max_time_raw = request.args.get('max_time')
    max_time = None
    if max_time_raw and max_time_raw.isdigit():
        max_time = int(max_time_raw)

    page_raw = request.args.get('page', '1')
    page = int(page_raw) if page_raw.isdigit() and int(page_raw) > 0 else 1
    per_page = 12
    offset = (page - 1) * per_page

    filters = mydb.fetch_feed_filters()
    total_count = mydb.fetch_feed_count(category=category, difficulty=difficulty, max_time=max_time)
    recipes = mydb.fetch_feed_recipes(category=category, difficulty=difficulty, max_time=max_time, limit=per_page, offset=offset)
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    prev_page = page - 1 if page > 1 else None
    next_page = page + 1 if page < total_pages else None

    return render_template(
        'pages/feed.html',
        recipes=recipes,
        filters=filters,
        active_category=category,
        active_difficulty=difficulty,
        active_max_time=max_time_raw or "",
        page=page,
        total_pages=total_pages,
        prev_page=prev_page,
        next_page=next_page
    )


@app.route('/recipe/<int:recipe_id>')
def recipe(recipe_id: int):
    recipe_row = mydb.fetch_recipe_detail(recipe_id)
    if not recipe_row:
        abort(404)

    image_path = recipe_row.get("cover_img_path")
    rating_value = float(recipe_row.get("rating") or 0)
    ingredients = recipe_row.get("ingredients", [])
    tags = recipe_row.get("tags", [])

    nutrition = []
    nutrition_map = {
        "Protein": recipe_row.get("protein"),
        "Carbs": recipe_row.get("carbs"),
        "Fats": recipe_row.get("fats"),
        "Sugar": recipe_row.get("sugar"),
        "Fiber": recipe_row.get("fiber"),
    }
    for label, value in nutrition_map.items():
        if value is not None:
            nutrition.append({"label": label, "value": f"{value}".rstrip('0').rstrip('.') if isinstance(value, float) else str(value)})

    stats = [
        {"label": "Ingredients", "value": str(len(ingredients))},
        {"label": "Minutes", "value": str(recipe_row.get("prepare_time") or 0)},
        {"label": "Calories", "value": str(recipe_row.get("calories") or 0)},
    ]

    procedure_text = recipe_row.get("procedure_description") or ""
    procedure_lines = [line.strip() for line in procedure_text.split("\n") if line.strip()]
    steps = []
    if procedure_lines:
        steps = [{"title": f"Step {idx}", "items": [line]} for idx, line in enumerate(procedure_lines, start=1)]
    else:
        steps = [{"title": "Step 1", "items": ["Follow the recipe instructions."]}]

    reviews_raw = recipe_row.get("reviews", [])
    reviews = []
    for review in reviews_raw:
        reviews.append({
            "author": review.get("author") or "User",
            "rating": int(round(rating_value)) if rating_value else 5,
            "content": review.get("content") or ""
        })

    recipe_data = {
        "id": recipe_row["id"],
        "title": recipe_row["title"],
        "rating": rating_value,
        "rating_count": recipe_row.get("rating_count") or len(reviews),
        "image": image_path or url_for('static', filename='media/registration.png'),
        "ingredients": ingredients,
        "nutrition": nutrition,
        "stats": stats,
        "steps": steps,
        "tags": tags,
        "reviews": reviews
    }

    return render_template('pages/recipe.html', recipe=recipe_data)


@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    recent_recipes = mydb.fetch_recent_recipes()
    more_recipes = mydb.fetch_more_recipes()
    popular_recipes = mydb.fetch_popular_recipes()
    return render_template('pages/home.html', recent_recipes=recent_recipes, more_recipes=more_recipes, popular_recipes=popular_recipes)

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
            session.clear()
            session.permanent = True
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
