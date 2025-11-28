import os
import uuid
from flask import Flask, render_template, redirect, request, url_for, jsonify, session, abort
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from dbhandler import DBHandler
app = Flask(__name__)
app.secret_key = "mytestkey"
mydb = DBHandler()


@app.before_request
def ensure_session_role():
    """Populate session role for logged in users."""
    user_id = session.get('user') or session.get('user_id')
    if user_id and not session.get('role'):
        role = mydb.fetch_user_role(user_id)
        if role:
            session['role'] = role
    if user_id and not session.get('user_id'):
        session['user_id'] = user_id
    if user_id and not session.get('user'):
        session['user'] = user_id


def get_current_user():
    """Return (user_id, role) and hydrate session role if missing."""
    user_id = session.get('user') or session.get('user_id')
    role = session.get('role')
    if user_id and not role:
        role = mydb.fetch_user_role(user_id)
        if role:
            session['role'] = role
    if user_id and not session.get('user_id'):
        session['user_id'] = user_id
    if user_id and not session.get('user'):
        session['user'] = user_id
    return user_id, role


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


@app.route('/recipe/<int:recipe_id>', methods=['GET', 'POST'])
def recipe(recipe_id: int):
    session_user, session_role = get_current_user()
    is_admin = session_role == 'admin'

    recipe_row = mydb.fetch_recipe_detail(recipe_id, include_inactive=is_admin)
    if not recipe_row:
        abort(404)
    if recipe_row.get("status") != "active" and not is_admin:
        abort(404)

    image_path = recipe_row.get("cover_img_path")
    rating_value = float(recipe_row.get("rating") or 0)
    ingredients = recipe_row.get("ingredients", [])
    tags = recipe_row.get("tags", [])
    is_favorited = False
    if session_user:
        is_favorited = mydb.has_user_liked_recipe(session_user, recipe_id)

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'toggle_favorite':
            if not session_user:
                return redirect(url_for('login'))
            if is_favorited:
                mydb.remove_recipe_like(session_user, recipe_id)
            else:
                mydb.add_recipe_like(session_user, recipe_id)
        elif action == 'add_review':
            if not session_user:
                return redirect(url_for('login'))
            rating = request.form.get('rating')
            comment = request.form.get('comment', '')
            if rating and rating.isdigit():
                rating_val = int(rating)
                if 1 <= rating_val <= 5:
                    try:
                        mydb.cursor.execute(
                            "insert into Ratings (recipe_id, user_id, rating, comment) values (%s, %s, %s, %s)",
                            (recipe_id, session_user, rating_val, comment)
                        )
                        mydb.cnx.commit()
                    except Exception as err:
                        print("Failed to add review:", err)
            return redirect(url_for('recipe', recipe_id=recipe_id))

        return redirect(url_for('recipe', recipe_id=recipe_id))

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

    procedure_text = (recipe_row.get("procedure_description") or "").strip()
    if not procedure_text:
        procedure_text = "Follow the recipe instructions."

    reviews_raw = recipe_row.get("reviews", [])
    reviews = []
    for review in reviews_raw:
        reviews.append({
            "author": review.get("author") or "User",
            "rating": int(round(review.get("rating"))) if review.get("rating") else 5,
            "content": review.get("content") or ""
        })

    recipe_data = {
        "id": recipe_row["id"],
        "title": recipe_row["title"],
        "category":recipe_row["category"],
        "difficulty":recipe_row["difficulty"],
        "rating": rating_value,
        "rating_count": recipe_row.get("rating_count") or len(reviews),
        "image": image_path or url_for('static', filename='media/registration.png'),
        "author_id": recipe_row.get("author_id"),
        "author_name": recipe_row.get("author_name"),
        "ingredients": ingredients,
        "nutrition": nutrition,
        "stats": stats,
        "procedure": procedure_text,
        "tags": tags,
        "reviews": reviews,
        "is_favorited": is_favorited,
        "status": recipe_row.get("status"),
        "is_admin": is_admin
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

@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('profile_view', user_id=session['user']))

@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
def profile_view(user_id: int):
    profile_data = mydb.fetch_user_basic(user_id)
    if not profile_data:
        abort(404)

    session_user = session.get('user')
    is_owner = session_user == user_id
    if request.method == 'POST':
        if not session_user:
            return redirect(url_for('login'))
        action = request.form.get('action')
        if action == 'follow' and not is_owner:
            mydb.follow_user(user_id, session_user)
        elif action == 'unfollow' and not is_owner:
            mydb.unfollow_user(user_id, session_user)
        return redirect(url_for('profile_view', user_id=user_id))

    stats = mydb.fetch_user_stats(user_id)
    recipes = mydb.fetch_user_recipes(user_id, limit=4)
    favorites = mydb.fetch_user_liked_recipes(user_id, limit=4) if is_owner else []
    is_following = False
    if session_user and not is_owner:
        is_following = mydb.is_following_user(user_id, session_user)

    return render_template(
        'pages/profile.html',
        profile=profile_data,
        stats=stats,
        recipes=recipes,
        favorites=favorites,
        is_owner=is_owner,
        is_following=is_following
    )

@app.route('/add', methods=['GET', 'POST'])
def add():
    session_user, session_role = get_current_user()
    if not session_user:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = (request.form.get('title') or "").strip()
        ingredients_raw = request.form.getlist('ingredients[]')
        procedure_text = (request.form.get('procedure') or "").strip()
        tags = request.form.getlist('tags[]')
        prep_minutes_raw = request.form.get('prep_minutes')
        calories_raw = request.form.get('calories')
        ingredients = [i.strip() for i in ingredients_raw if i and i.strip()]

        photo_file = request.files.get('photo')
        cover_img_path = None
        allowed_ext = {"png", "jpg", "jpeg", "gif", "webp"}

        def parse_number(val):
            if val is None or val == "":
                return None
            try:
                return float(val)
            except ValueError:
                return None

        nutrition_labels = request.form.getlist('nutrition_label[]')
        nutrition_values = request.form.getlist('nutrition_value[]')
        nutrition_map = {}
        for label, value in zip(nutrition_labels, nutrition_values):
            key = (label or "").strip().lower()
            if key in {"protein", "carbs", "fats", "sugar", "fiber"}:
                nutrition_map[key] = parse_number(value)

        prepare_time = parse_number(prep_minutes_raw)
        calories = parse_number(calories_raw)

        if not title or not ingredients or not procedure_text:
            error = "Title, ingredients, and procedure are required."
            return render_template('pages/add.html', error=error)

        if photo_file and photo_file.filename:
            filename = secure_filename(photo_file.filename)
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            if ext in allowed_ext:
                upload_dir = os.path.join(app.root_path, "static", "media", "recipes")
                os.makedirs(upload_dir, exist_ok=True)
                final_name = f"{uuid.uuid4().hex}_{filename}"
                file_path = os.path.join(upload_dir, final_name)
                photo_file.save(file_path)
                cover_img_path = f"/static/media/recipes/{final_name}"
            else:
                error = "Please upload a valid image file."
                return render_template('pages/add.html', error=error)

        recipe_id = mydb.create_recipe(
            title=title,
            author_id=session_user,
            procedure=procedure_text,
            prepare_time=prepare_time,
            calories=calories,
            cover_img_path=cover_img_path,
            nutrition=nutrition_map,
            status="inactive",
        )
        if recipe_id:
            mydb.add_recipe_ingredients(recipe_id, ingredients)
            mydb.add_recipe_tags(recipe_id, [t.strip() for t in tags if t.strip()])
            if session_role == 'admin':
                return redirect(url_for('recipe', recipe_id=recipe_id))
            return render_template('pages/add.html', success="Your recipe was submitted for admin approval.")

        return render_template('pages/add.html', error="Could not save recipe. Please try again.")

    return render_template('pages/add.html')

@app.route('/admin/recipes', methods=['GET', 'POST'])
def admin_recipes():
    user_id, role = get_current_user()
    print("USER ID AND ROLE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(user_id, role)
    if not user_id:
        return redirect(url_for('login'))
    if role != 'admin':
        abort(403)

    if request.method == 'POST':
        recipe_id_raw = request.form.get('recipe_id')
        action = request.form.get('action')
        if recipe_id_raw and recipe_id_raw.isdigit():
            recipe_id = int(recipe_id_raw)
            if action == 'activate':
                mydb.update_recipe_status(recipe_id, 'active')
            elif action == 'delete':
                mydb.delete_recipe(recipe_id)
        return redirect(url_for('admin_recipes'))

    pending_recipes = mydb.fetch_inactive_recipes()
    return render_template('pages/admin_recipes.html', recipes=pending_recipes)

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
            session['user_id'] = user_id
            session_role = mydb.fetch_user_role(user_id)
            if session_role:
                session['role'] = session_role
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
