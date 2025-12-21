import os
import uuid
from pathlib import Path
from flask import Flask, render_template, redirect, request, url_for, jsonify, session, abort
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from dbhandler import DBHandler


BASE_DIR = Path(__file__).resolve().parent


def load_env_file(filepath=".env"):
    """Simple .env loader: key=value pairs, ignores comments/blank lines."""
    env_path = Path(filepath)
    if not env_path.exists():
        # Try relative to project root
        env_path = BASE_DIR / filepath
        if not env_path.exists():
            return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and not os.environ.get(key):
            os.environ[key] = value


#load_env_file()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(32)
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true",
)
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


def generate_csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = uuid.uuid4().hex
        session["csrf_token"] = token
    return token


@app.before_request
def csrf_protect():
    if request.method == "POST":
        session_token = session.get("csrf_token")
        form_token = request.form.get("csrf_token")
        header_token = request.headers.get("X-CSRFToken") or request.headers.get("X-CSRF-Token")
        json_payload = request.get_json(silent=True) or {}
        json_token = json_payload.get("csrf_token") if isinstance(json_payload, dict) else None
        token = form_token or header_token or json_token
        if not session_token or not token or session_token != token:
            abort(400)


@app.context_processor
def inject_csrf():
    return {"csrf_token": generate_csrf_token}


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


def validate_image_file(upload_file, allowed_ext):
    """Validate uploaded image file for size and type; return (ext, error_message)."""
    if not upload_file or not upload_file.filename:
        return None, "No file provided."
    filename = secure_filename(upload_file.filename)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in allowed_ext:
        return None, "Please upload a valid image file."

    upload_file.stream.seek(0, os.SEEK_END)
    size = upload_file.stream.tell()
    upload_file.stream.seek(0)
    if size > MAX_UPLOAD_SIZE:
        return None, "Image is too large. Please upload a file under 10MB."

    header = upload_file.read(512)
    upload_file.seek(0)
    detected = detect_image_type(header)
    if detected not in allowed_ext:
        return None, "Please upload a valid image file."

    return ext, None


def detect_image_type(header_bytes: bytes):
    """Simple signature-based image detection for png/jpg/gif/webp."""
    if header_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if header_bytes[:3] == b"\xff\xd8\xff":
        return "jpg"
    if header_bytes.startswith(b"GIF87a") or header_bytes.startswith(b"GIF89a"):
        return "gif"
    if header_bytes[8:12] == b"WEBP" or header_bytes.startswith(b"RIFF") and header_bytes[8:12] == b"WEBP":
        return "webp"
    return None


def build_difficulty_collections():
    """Return home page collections for easy/medium/difficult recipes."""
    difficulty_levels = [
        {"value": "Easy", "title": "Easy recipes"},
        {"value": "Medium", "title": "Medium recipes"},
        {"value": "Difficult", "title": "Difficult recipes"},
    ]
    collections = []
    for level in difficulty_levels:
        latest = mydb.fetch_latest_recipe_by_difficulty(level["value"])
        collections.append({
            "title": level["title"],
            "difficulty": level["value"],
            "image": latest["image"] if latest else None,
        })
    return collections


# adding comment, making change
@app.route('/signout', methods=['GET', 'POST'])
def signout():
    session.clear()
    return redirect(url_for('index'))


@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(e):
    return "File too large. Maximum upload size is 10MB.", 413

def test_git():
    pass

@app.route('/')
def index():
    recent_recipes = mydb.fetch_recent_recipes()
    more_recipes = mydb.fetch_recent_recipes(offset=4)
    popular_recipes = mydb.fetch_popular_recipes()
    difficulty_collections = build_difficulty_collections()
    return render_template(
        'pages/home.html',
        recent_recipes=recent_recipes,
        more_recipes=more_recipes,
        popular_recipes=popular_recipes,
        difficulty_collections=difficulty_collections
    )


@app.route('/api/search')
def api_search():
    """Autocomplete search endpoint for recipe titles, categories, and ingredients."""
    query = (request.args.get('q') or "").strip()
    limit_raw = request.args.get('limit')
    try:
        limit = int(limit_raw) if limit_raw else 5
    except ValueError:
        limit = 5
    limit = max(1, min(limit, 15))

    results = mydb.search_recipes(query, limit=limit, offset=0)
    return jsonify([
        {
            "id": r.get("id"),
            "title": r.get("title"),
            "image": r.get("image"),
            "rating": r.get("rating"),
        } for r in results
    ])


@app.route('/search')
def search():
    user_id, _ = get_current_user()
    query = (request.args.get('q') or "").strip()
    page_raw = request.args.get('page', '1')
    page = int(page_raw) if page_raw.isdigit() and int(page_raw) > 0 else 1
    per_page = 12
    offset = (page - 1) * per_page

    recipes = mydb.search_recipes(query, limit=per_page, offset=offset, user_id=user_id) if query else []
    total_count = mydb.search_recipes_count(query) if query else 0
    total_pages = max(1, (total_count + per_page - 1) // per_page) if query else 1
    prev_page = page - 1 if page > 1 and page <= total_pages else None
    next_page = page + 1 if page < total_pages else None

    return render_template(
        'pages/search.html',
        query=query,
        recipes=recipes,
        page=page,
        total_pages=total_pages,
        prev_page=prev_page,
        next_page=next_page,
        total_count=total_count,
    )


@app.route('/feed')
def feed():
    user_id, _ = get_current_user()
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
    recipes = mydb.fetch_feed_recipes(
        category=category,
        difficulty=difficulty,
        max_time=max_time,
        limit=per_page,
        offset=offset,
        user_id=user_id
    )
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

@app.route('/api/recipes/<int:recipe_id>/favorite', methods=['POST', 'DELETE'])
def api_favorite_recipe(recipe_id: int):
    """Toggle a recipe in the current user's favorites or redirect to login."""
    user_id, _ = get_current_user()
    if not user_id:
        return jsonify({"redirect": url_for('login')}), 401
    if request.method == 'DELETE':
        if not mydb.remove_recipe_like(user_id, recipe_id):
            return jsonify({"error": "Unable to unlike recipe"}), 500
        return jsonify({"liked": False})
    if not mydb.add_recipe_like(user_id, recipe_id):
        return jsonify({"error": "Unable to like recipe"}), 500
    return jsonify({"liked": True})


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
                    if not mydb.add_rating(recipe_id, session_user, rating_val, comment):
                        print("Failed to add review via add_rating helper")
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

    recommendations = mydb.fetch_recommended_recipes(recipe_id, limit=5)

    return render_template('pages/recipe.html', recipe=recipe_data, recommendations=recommendations)


@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    recent_recipes = mydb.fetch_recent_recipes()
    more_recipes = mydb.fetch_recent_recipes(offset=4)
    popular_recipes = mydb.fetch_popular_recipes()
    difficulty_collections = build_difficulty_collections()
    return render_template(
        'pages/home.html',
        recent_recipes=recent_recipes,
        more_recipes=more_recipes,
        popular_recipes=popular_recipes,
        difficulty_collections=difficulty_collections
    )

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

    session_user, _ = get_current_user()
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
    recipes = mydb.fetch_user_recipes(user_id, limit=4, viewer_id=session_user)
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

@app.route('/editprofile', methods=['GET', 'POST'])
def edit_profile():
    session_user, _ = get_current_user()
    if not session_user:
        return redirect(url_for('login'))

    profile_data = mydb.fetch_user_profile_full(session_user) or {}
    if not profile_data:
        profile_data = {"email": "", "name": "", "surname": "", "about": "", "profile_img_path": None}
    error = None
    success = None
    current_creds = mydb.fetch_user_credentials(session_user) or {}

    if request.method == 'POST':
        name = (request.form.get('name') or "").strip()
        surname = (request.form.get('surname') or "").strip()
        email = (request.form.get('email') or "").strip().lower()
        about = (request.form.get('about') or "").strip()
        new_password = request.form.get('password') or ""
        current_password = request.form.get('current_password') or ""
        photo_file = request.files.get('photo')
        allowed_ext = {"png", "jpg", "jpeg", "gif", "webp"}

        if not name or not email:
            error = "Name and email are required."
        else:
            profile_img_path = None
            if photo_file and photo_file.filename:
                ext, validation_error = validate_image_file(photo_file, allowed_ext)
                if validation_error:
                    return render_template('pages/edit_profile.html', profile=profile_data, error=validation_error, success=None)
                upload_dir = os.path.join(app.root_path, "static", "img", "profile")
                os.makedirs(upload_dir, exist_ok=True)
                final_name = f"{session_user}.{ext}"
                file_path = os.path.join(upload_dir, final_name)
                photo_file.save(file_path)
                profile_img_path = f"/static/img/profile/{final_name}"

            hashed_password = generate_password_hash(new_password) if new_password else None

            if (new_password or email != current_creds.get("email")):
                stored_hash = current_creds.get("password_hash")
                if not current_password or not stored_hash or not check_password_hash(stored_hash, current_password):
                    error = "Current password is required to change email or password."
                    return render_template('pages/edit_profile.html', profile=profile_data, error=error, success=None)

            if not error:
                updated = mydb.update_user_profile(
                    session_user,
                    email=email,
                    password=hashed_password,
                    name=name,
                    surname=surname if surname else None,
                    about=about if about else None,
                    profile_img_path=profile_img_path
                )
                if updated:
                    success = "Profile updated successfully."
                    profile_data = mydb.fetch_user_profile_full(session_user) or profile_data
                else:
                    error = "Could not update profile. Please try again."

        # refresh form values on error
        profile_data.update({
            "email": email,
            "name": name,
            "surname": surname,
            "about": about,
        })

    return render_template('pages/edit_profile.html', profile=profile_data, error=error, success=success)

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
        category = (request.form.get('category') or "").strip()
        difficulty_raw = (request.form.get('difficulty') or "").strip().lower()
        difficulty_options = {"easy": "Easy", "medium": "Medium", "difficult": "Difficult"}
        difficulty = difficulty_options.get(difficulty_raw)
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

        if not title or not ingredients or not procedure_text or not category:
            error = "Title, category, ingredients, and procedure are required."
            return render_template('pages/add.html', error=error)
        if not difficulty:
            error = "Please select a difficulty level."
            return render_template('pages/add.html', error=error)

        if photo_file and photo_file.filename:
            ext, error_message = validate_image_file(photo_file, allowed_ext)
            if error_message:
                return render_template('pages/add.html', error=error_message)
            upload_dir = os.path.join(app.root_path, "static", "media", "recipes")
            os.makedirs(upload_dir, exist_ok=True)
            final_name = f"{uuid.uuid4().hex}.{ext}"
            file_path = os.path.join(upload_dir, final_name)
            photo_file.save(file_path)
            cover_img_path = f"/static/media/recipes/{final_name}"

        recipe_id = mydb.create_recipe(
            title=title,
            author_id=session_user,
            procedure=procedure_text,
            prepare_time=prepare_time,
            calories=calories,
            category=category,
            difficulty=difficulty,
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
        if action == 'activate_all':
            mydb.activate_all_pending_recipes()
        elif action == 'delete_rating':
            rate_id_raw = request.form.get('rate_id')
            if rate_id_raw and rate_id_raw.isdigit():
                mydb.delete_rating(int(rate_id_raw))
        elif recipe_id_raw and recipe_id_raw.isdigit():
            recipe_id = int(recipe_id_raw)
            if action == 'activate':
                mydb.update_recipe_status(recipe_id, 'active', actor_id=user_id)
            elif action == 'delete':
                mydb.delete_recipe(recipe_id, actor_id=user_id)
        return redirect(url_for('admin_recipes', reviews_page=request.args.get('reviews_page', '1')))

    pending_recipes = mydb.fetch_inactive_recipes()

    reviews_page_raw = request.args.get('reviews_page', '1')
    reviews_page = int(reviews_page_raw) if reviews_page_raw.isdigit() and int(reviews_page_raw) > 0 else 1
    reviews_per_page = 20
    reviews_offset = (reviews_page - 1) * reviews_per_page
    reviews_total = mydb.fetch_ratings_count()
    reviews_total_pages = max(1, (reviews_total + reviews_per_page - 1) // reviews_per_page)
    reviews_prev = reviews_page - 1 if reviews_page > 1 else None
    reviews_next = reviews_page + 1 if reviews_page < reviews_total_pages else None
    ratings = mydb.fetch_ratings_admin(limit=reviews_per_page, offset=reviews_offset)

    return render_template(
        'pages/admin_recipes.html',
        recipes=pending_recipes,
        ratings=ratings,
        reviews_page=reviews_page,
        reviews_total_pages=reviews_total_pages,
        reviews_prev=reviews_prev,
        reviews_next=reviews_next,
    )

@app.route('/notifications', methods=['GET', 'POST'])
def notifications():
    if 'user' not in session:
        return redirect(url_for('login'))
    user_id, _ = get_current_user()
    items = mydb.fetch_unread_notifications(user_id)
    return render_template('pages/notifications.html', notifications=items)


@app.route('/notifications/mark-read', methods=['POST'])
def notifications_mark_read():
    user_id, _ = get_current_user()
    if not user_id:
        return jsonify({"redirect": url_for('login')}), 401
    notif_id_raw = request.form.get('notification_id')
    if not notif_id_raw or not notif_id_raw.isdigit():
        return jsonify({"error": "Invalid id"}), 400
    notif_id = int(notif_id_raw)
    if mydb.mark_notification_read(user_id, notif_id):
        return jsonify({"ok": True})
    return jsonify({"error": "Not updated"}), 400


@app.route('/notifications/mark-all', methods=['POST'])
def notifications_mark_all():
    user_id, _ = get_current_user()
    if not user_id:
        return jsonify({"redirect": url_for('login')}), 401
    if mydb.mark_all_notifications_read(user_id):
        return jsonify({"ok": True})
    return jsonify({"error": "Not updated"}), 400


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


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true", port=8000)
