import mysql.connector
from mysql.connector import Error

class DBHandler():
    def __init__(self):
        try:
            self.cnx = mysql.connector.connect(user='root', password='Scripter1211#',
                                host='localhost', port='3306',
                                database='recipedb')
            self.cursor = self.cnx.cursor()
            print("DBhandler initiated")
            self._user_rating_column = None
        except Error as e:
            print("Failed to connect!", e)
    def closer_connection(self):
        self.cnx.close()
        print("Database connection closed!")
    def check_user_login(self, login):
        query = "select user_id, password from Users where email=%s"
        self.cursor.execute(query, (login,))
        result = self.cursor.fetchone()
        print("result: ", result)
        return result
    
    def register_new_user(self, name, login, password):
        query = (
            "insert into Users(email, password, name, surname, about_me, profile_img_path, date_registered, role) "
            "values(%s, %s, %s, NULL, NULL, NULL, DATE_ADD(NOW(), INTERVAL 5 HOUR), 'user')"
        )
        try:
            self.cursor.execute(query, (login, password, name))
            self.cnx.commit()
            return True
        except Error as err:
            print(err)
            self.cnx.rollback()
            return False

    def fetch_user_role(self, user_id: int):
        """Return the role for the given user id."""
        try:
            self.cursor.execute("select role from Users where user_id = %s", (user_id,))
            row = self.cursor.fetchone()
            return row[0] if row else None
        except Error as err:
            print("Failed to fetch user role:", err)
            return None

    def _user_rating_column_available(self):
        """Check once whether Users table has a rating column to persist profile rating."""
        if self._user_rating_column is not None:
            return self._user_rating_column
        try:
            self.cursor.execute("show columns from Users like 'rating'")
            self._user_rating_column = self.cursor.fetchone() is not None
        except Error as err:
            print("Failed to inspect Users.rating column:", err)
            self._user_rating_column = False
        return self._user_rating_column

    def _fetch_recipe_author(self, recipe_id: int):
        """Return the author_id for a recipe or None if not found."""
        try:
            self.cursor.execute("select author_id from Recipes where recipe_id = %s", (recipe_id,))
            row = self.cursor.fetchone()
            return row[0] if row else None
        except Error as err:
            print("Failed to fetch recipe author:", err)
            return None

    def fetch_recent_recipes(self, limit=4):
        """Return a list of the most recent recipes with id, title, and cover image."""
        query = """
            select recipe_id, title, cover_img_path
            from Recipes
            where status = 'active'
            order by date_posted desc
            limit %s
        """
        try:
            self.cursor.execute(query, (limit,))
            rows = self.cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "image": row[2]
                } for row in rows
            ]
        except Error as err:
            print("Failed to fetch recent recipes:", err)
            return []

    def fetch_more_recipes(self, limit=4, offset=4):
        """Return the next set of recent recipes after the top batch."""
        query = """
            select recipe_id, title, cover_img_path
            from Recipes
            where status = 'active'
            order by date_posted desc
            limit %s offset %s
        """
        try:
            self.cursor.execute(query, (limit, offset))
            rows = self.cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "image": row[2]
                } for row in rows
            ]
        except Error as err:
            print("Failed to fetch more recipes:", err)
            return []

    def fetch_popular_recipes(self, limit=3):
        """Return top recipes by rating (fallback to date order if rating null)."""
        query = """
            select recipe_id, title, cover_img_path
            from Recipes
            where status = 'active'
            order by rating desc, date_posted desc
            limit %s
        """
        try:
            self.cursor.execute(query, (limit,))
            rows = self.cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "image": row[2]
                } for row in rows
            ]
        except Error as err:
            print("Failed to fetch popular recipes:", err)
            return []

    def fetch_inactive_recipes(self):
        """Return recipes that are not active for admin review."""
        query = """
            select r.recipe_id, r.title, r.cover_img_path, r.rating, r.prepare_time, r.status,
                   coalesce(concat_ws(' ', u.name, u.surname), 'User') as author_name
            from Recipes r
            left join Users u on r.author_id = u.user_id
            where r.status <> 'active'
            order by r.date_posted desc
        """
        try:
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "image": row[2],
                    "rating": row[3],
                    "prepare_time": row[4],
                    "status": row[5],
                    "author_name": row[6],
                } for row in rows
            ]
        except Error as err:
            print("Failed to fetch inactive recipes:", err)
            return []

    def update_recipe_status(self, recipe_id: int, status: str):
        """Update a recipe's status."""
        if status not in ("active", "inactive"):
            return False
        query = "update Recipes set status = %s where recipe_id = %s"
        try:
            self.cursor.execute(query, (status, recipe_id))
            self.cnx.commit()
            return True
        except Error as err:
            print("Failed to update recipe status:", err)
            self.cnx.rollback()
            return False

    def activate_all_pending_recipes(self):
        """Mark all inactive recipes as active."""
        try:
            self.cursor.execute("update Recipes set status = 'active' where status = 'inactive'")
            self.cnx.commit()
            return True
        except Error as err:
            print("Failed to activate all recipes:", err)
            self.cnx.rollback()
            return False

    def delete_recipe(self, recipe_id: int):
        """Delete a recipe by id."""
        try:
            self.cursor.execute("delete from Recipes where recipe_id = %s", (recipe_id,))
            self.cnx.commit()
            return True
        except Error as err:
            print("Failed to delete recipe:", err)
            self.cnx.rollback()
            return False

    def create_recipe(self, *, title: str, author_id: int, procedure: str, prepare_time=None, calories=None,
                      category=None, difficulty=None, cover_img_path=None, nutrition=None, status="inactive"):
        """Create a new recipe and return its id."""
        query = """
            insert into Recipes (title, author_id, category, difficulty, cover_img_path,
                                 prepare_time, calories, procedure_description, protein, carbs, fats, sugar, fiber,
                                 status)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        nutrition = nutrition or {}
        try:
            self.cursor.execute(
                query,
                (
                    title,
                    author_id,
                    category,
                    difficulty,
                    cover_img_path,
                    prepare_time,
                    calories,
                    procedure,
                    nutrition.get("protein"),
                    nutrition.get("carbs"),
                    nutrition.get("fats"),
                    nutrition.get("sugar"),
                    nutrition.get("fiber"),
                    status,
                ),
            )
            self.cnx.commit()
            return self.cursor.lastrowid
        except Error as err:
            print("Failed to create recipe:", err)
            self.cnx.rollback()
            return None

    def add_recipe_ingredients(self, recipe_id: int, ingredients: list[str]):
        """Bulk insert ingredients for a recipe."""
        if not ingredients:
            return True
        query = "insert into Ingredients (recipe_id, ingredient) values (%s, %s)"
        try:
            self.cursor.executemany(query, [(recipe_id, ing) for ing in ingredients])
            self.cnx.commit()
            return True
        except Error as err:
            print("Failed to insert ingredients:", err)
            self.cnx.rollback()
            return False

    def add_recipe_tags(self, recipe_id: int, tags: list[str]):
        """Bulk insert tags for a recipe."""
        if not tags:
            return True
        query = "insert into Tags (recipe_id, tag_name) values (%s, %s)"
        try:
            self.cursor.executemany(query, [(recipe_id, tag) for tag in tags])
            self.cnx.commit()
            return True
        except Error as err:
            print("Failed to insert tags:", err)
            self.cnx.rollback()
            return False

    def fetch_recipe_detail(self, recipe_id: int, include_inactive: bool = False):
        """Return full recipe details for a given recipe_id."""
        recipe_query = """
            select recipe_id, title, category, difficulty, rating, cover_img_path, prepare_time, calories,
                   protein, carbs, fats, sugar, fiber, procedure_description, status,
                   author_id,
                   (select concat_ws(' ', u.name, u.surname) from Users u where u.user_id = r.author_id) as author_name
            from Recipes r
            where r.recipe_id = %s {status_clause}
        """
        ing_query = "select ingredient from Ingredients where recipe_id = %s order by ingredient_id"
        tag_query = "select tag_name from Tags where recipe_id = %s order by tag_id"
        review_query = """
            select coalesce(u.name, 'User') as name, coalesce(u.surname, '') as surname, r.comment, r.rating
            from Ratings r
            left join Users u on r.user_id = u.user_id
            where r.recipe_id = %s
            order by r.date_posted desc
            limit 5
        """
        try:
            status_clause = "" if include_inactive else "and r.status = 'active'"
            self.cursor.execute(recipe_query.format(status_clause=status_clause), (recipe_id,))
            recipe_row = self.cursor.fetchone()
            if not recipe_row:
                return None

            self.cursor.execute(ing_query, (recipe_id,))
            ing_rows = self.cursor.fetchall()

            self.cursor.execute(tag_query, (recipe_id,))
            tag_rows = self.cursor.fetchall()

            self.cursor.execute(review_query, (recipe_id,))
            review_rows = self.cursor.fetchall()

            recipe = {
                "id": recipe_row[0],
                "title": recipe_row[1],
                "category": recipe_row[2],
                "difficulty": recipe_row[3],
                "rating": recipe_row[4],
                "cover_img_path": recipe_row[5],
                "prepare_time": recipe_row[6],
                "calories": recipe_row[7],
                "protein": recipe_row[8],
                "carbs": recipe_row[9],
                "fats": recipe_row[10],
                "sugar": recipe_row[11],
                "fiber": recipe_row[12],
                "procedure_description": recipe_row[13] or "",
                "status": recipe_row[14],
                "author_id": recipe_row[15],
                "author_name": recipe_row[16] or "User",
                "ingredients": [row[0] for row in ing_rows],
                "tags": [row[0] for row in tag_rows],
                "reviews": [
                    {
                        "author": (row[0] + (" " + row[1] if row[1] else "")).strip(),
                        "content": row[2],
                        "rating": row[3] or 0
                    } for row in review_rows if row[2] or row[3] is not None
                ],
            }
            recipe["rating_count"] = len(review_rows)
            return recipe
        except Error as err:
            print("Failed to fetch recipe detail:", err)
            return None

    def recalc_user_rating(self, user_id: int, auto_commit: bool = True):
        """Recalculate average rating for a user based on their recipes' ratings."""
        try:
            self.cursor.execute(
                """
                select avg(rt.rating)
                from Ratings rt
                join Recipes r on rt.recipe_id = r.recipe_id
                where r.author_id = %s
                """,
                (user_id,),
            )
            row = self.cursor.fetchone()
            avg_rating = float(row[0]) if row and row[0] is not None else None

            if self._user_rating_column_available():
                self.cursor.execute("update Users set rating = %s where user_id = %s", (avg_rating, user_id))

            if auto_commit:
                self.cnx.commit()
            return avg_rating
        except Error as err:
            print("Failed to recalc user rating:", err)
            if auto_commit:
                self.cnx.rollback()
            raise

    def recalc_recipe_rating(self, recipe_id: int, auto_commit: bool = True):
        """Recalculate recipe.rating from all posted ratings and update the author rating."""
        try:
            self.cursor.execute("select avg(rating) from Ratings where recipe_id = %s", (recipe_id,))
            row = self.cursor.fetchone()
            avg_rating = float(row[0]) if row and row[0] is not None else None

            self.cursor.execute("update Recipes set rating = %s where recipe_id = %s", (avg_rating, recipe_id))

            author_id = self._fetch_recipe_author(recipe_id)
            if author_id:
                # Update the author's profile rating whenever a recipe rating changes.
                self.recalc_user_rating(author_id, auto_commit=False)

            if auto_commit:
                self.cnx.commit()
            return avg_rating
        except Error as err:
            print("Failed to recalc recipe rating:", err)
            if auto_commit:
                self.cnx.rollback()
            raise

    def add_rating(self, recipe_id: int, user_id: int, rating: int, comment: str = ""):
        """Insert a new rating, then refresh recipe and author aggregates."""
        try:
            self.cursor.execute(
                "insert into Ratings (recipe_id, user_id, rating, comment) values (%s, %s, %s, %s)",
                (recipe_id, user_id, rating, comment),
            )
            self.recalc_recipe_rating(recipe_id, auto_commit=False)
            self.cnx.commit()
            return True
        except Error as err:
            print("Failed to add rating:", err)
            self.cnx.rollback()
            return False

    def fetch_ratings_admin(self, limit=10, offset=0):
        """Fetch ratings/comments with user and recipe info for admin view."""
        query = """
            select rat.rate_id,
                   rat.rating,
                   rat.comment,
                   rat.date_posted,
                   concat_ws(' ', u.name, u.surname) as user_name,
                   rec.title
            from Ratings rat
            join Users u on rat.user_id = u.user_id
            join Recipes rec on rat.recipe_id = rec.recipe_id
            order by rat.date_posted desc
            limit %s offset %s
        """
        try:
            self.cursor.execute(query, (limit, offset))
            rows = self.cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "rating": row[1],
                    "comment": row[2],
                    "date_posted": row[3],
                    "user_name": row[4],
                    "recipe_title": row[5],
                }
                for row in rows
            ]
        except Error as err:
            print("Failed to fetch ratings for admin:", err)
            return []

    def fetch_ratings_count(self):
        """Return total ratings count."""
        try:
            self.cursor.execute("select count(*) from Ratings")
            row = self.cursor.fetchone()
            return row[0] if row else 0
        except Error as err:
            print("Failed to count ratings:", err)
            return 0

    def delete_rating(self, rate_id: int):
        """Delete a rating/comment by id."""
        try:
            recipe_id = None
            self.cursor.execute("select recipe_id from Ratings where rate_id = %s", (rate_id,))
            row = self.cursor.fetchone()
            if row:
                recipe_id = row[0]

            self.cursor.execute("delete from Ratings where rate_id = %s", (rate_id,))

            if recipe_id:
                self.recalc_recipe_rating(recipe_id, auto_commit=False)

            self.cnx.commit()
            return True
        except Error as err:
            print("Failed to delete rating:", err)
            self.cnx.rollback()
            return False

    def fetch_feed_recipes(self, category=None, difficulty=None, max_time=None, limit=12, offset=0):
        """Fetch recipes for the feed with optional filters."""
        base = [
            "select recipe_id, title, cover_img_path, rating, prepare_time",
            "from Recipes",
            "where 1=1"
        ]
        params = []
        if category:
            base.append("and category = %s")
            params.append(category)
        if difficulty:
            base.append("and difficulty = %s")
            params.append(difficulty)
        if max_time is not None:
            base.append("and prepare_time <= %s")
            params.append(max_time)
        base.append("and status = 'active'")
        base.append("order by date_posted desc limit %s offset %s")
        params.extend([limit, offset])

        query = " ".join(base)
        try:
            self.cursor.execute(query, tuple(params))
            rows = self.cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "image": row[2],
                    "rating": row[3],
                    "prepare_time": row[4]
                } for row in rows
            ]
        except Error as err:
            print("Failed to fetch feed recipes:", err)
            return []

    def fetch_feed_filters(self):
        """Return distinct categories and difficulties for filters."""
        categories = []
        difficulties = []
        try:
            self.cursor.execute(
                "select distinct category from Recipes where category is not null and status = 'active' order by category"
            )
            categories = [row[0] for row in self.cursor.fetchall() if row[0]]
            self.cursor.execute(
                "select distinct difficulty from Recipes where difficulty is not null and status = 'active' order by difficulty"
            )
            difficulties = [row[0] for row in self.cursor.fetchall() if row[0]]
        except Error as err:
            print("Failed to fetch filter lists:", err)
        return {"categories": categories, "difficulties": difficulties}

    def fetch_feed_count(self, category=None, difficulty=None, max_time=None):
        """Count recipes matching filters."""
        base = ["select count(*) from Recipes where status = 'active'"]
        params = []
        if category:
            base.append("and category = %s")
            params.append(category)
        if difficulty:
            base.append("and difficulty = %s")
            params.append(difficulty)
        if max_time is not None:
            base.append("and prepare_time <= %s")
            params.append(max_time)
        query = " ".join(base)
        try:
            self.cursor.execute(query, tuple(params))
            row = self.cursor.fetchone()
            return row[0] if row else 0
        except Error as err:
            print("Failed to count feed recipes:", err)
            return 0

    def fetch_user_basic(self, user_id: int):
        """Return basic user profile info."""
        query = "select user_id, name, surname, about_me, profile_img_path from Users where user_id = %s"
        try:
            self.cursor.execute(query, (user_id,))
            row = self.cursor.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "name": row[1],
                "surname": row[2] or "",
                "about": row[3] or "",
                "profile_img_path": row[4]
            }
        except Error as err:
            print("Failed to fetch user basic:", err)
            return None

    def fetch_user_stats(self, user_id: int):
        """Return basic stats for user profile."""
        stats = {"likes": 0, "followers": 0, "reviews": 0, "posted": 0, "rating_avg": 0, "rating_count": 0}
        try:
            self.cursor.execute(
                """
                select count(*) from Likes l
                join Recipes r on l.recipe_id = r.recipe_id
                where r.author_id = %s and r.status = 'active'
                """,
                (user_id,)
            )
            stats["likes"] = self.cursor.fetchone()[0] or 0

            self.cursor.execute("select count(*) from Followers where user_id = %s", (user_id,))
            stats["followers"] = self.cursor.fetchone()[0] or 0

            self.cursor.execute(
                """
                select count(*) from Ratings rt
                join Recipes r on rt.recipe_id = r.recipe_id
                where r.author_id = %s and r.status = 'active'
                """,
                (user_id,)
            )
            stats["reviews"] = self.cursor.fetchone()[0] or 0

            self.cursor.execute("select count(*) from Recipes where author_id = %s and status = 'active'", (user_id,))
            stats["posted"] = self.cursor.fetchone()[0] or 0

            self.cursor.execute(
                """
                select avg(rt.rating), count(rt.rating)
                from Ratings rt
                join Recipes r on rt.recipe_id = r.recipe_id
                where r.author_id = %s and r.status = 'active'
                """,
                (user_id,)
            )
            rating_row = self.cursor.fetchone()
            if rating_row:
                stats["rating_avg"] = float(rating_row[0]) if rating_row[0] is not None else 0
                stats["rating_count"] = rating_row[1] or 0
        except Error as err:
            print("Failed to fetch user stats:", err)
        return stats

    def search_recipes(self, query: str, limit: int = 12, offset: int = 0):
        """Search recipes by title, ingredient, or category for active recipes."""
        if not query or not query.strip():
            return []
        like_pattern = f"%{query.strip()}%"
        sql = """
            select r.recipe_id, r.title, r.cover_img_path, r.rating, r.prepare_time
            from Recipes r
            left join Ingredients i on i.recipe_id = r.recipe_id
            where r.status = 'active'
              and (
                  r.title like %s
                  or r.category like %s
                  or i.ingredient like %s
              )
            group by r.recipe_id, r.title, r.cover_img_path, r.rating, r.prepare_time
            order by r.date_posted desc
            limit %s offset %s
        """
        try:
            self.cursor.execute(sql, (like_pattern, like_pattern, like_pattern, limit, offset))
            rows = self.cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "image": row[2],
                    "rating": row[3],
                    "prepare_time": row[4],
                }
                for row in rows
            ]
        except Error as err:
            print("Failed to search recipes:", err)
            return []

    def search_recipes_count(self, query: str):
        """Return total count of recipes that match the search query."""
        if not query or not query.strip():
            return 0
        like_pattern = f"%{query.strip()}%"
        sql = """
            select count(distinct r.recipe_id)
            from Recipes r
            left join Ingredients i on i.recipe_id = r.recipe_id
            where r.status = 'active'
              and (
                  r.title like %s
                  or r.category like %s
                  or i.ingredient like %s
              )
        """
        try:
            self.cursor.execute(sql, (like_pattern, like_pattern, like_pattern))
            row = self.cursor.fetchone()
            return row[0] if row else 0
        except Error as err:
            print("Failed to count search recipes:", err)
            return 0

    def fetch_user_recipes(self, user_id: int, limit=8):
        query = """
            select recipe_id, title, cover_img_path, rating, prepare_time
            from Recipes
            where author_id = %s and status = 'active'
            order by date_posted desc
            limit %s
        """
        try:
            self.cursor.execute(query, (user_id, limit))
            rows = self.cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "image": row[2],
                    "rating": row[3],
                    "prepare_time": row[4],
                } for row in rows
            ]
        except Error as err:
            print("Failed to fetch user recipes:", err)
            return []

    def fetch_user_liked_recipes(self, user_id: int, limit=8):
        query = """
            select r.recipe_id, r.title, r.cover_img_path, r.rating, r.prepare_time
            from Likes l
            join Recipes r on l.recipe_id = r.recipe_id
            where l.user_id = %s and r.status = 'active'
            order by l.date_liked desc
            limit %s
        """
        try:
            self.cursor.execute(query, (user_id, limit))
            rows = self.cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "image": row[2],
                    "rating": row[3],
                    "prepare_time": row[4],
                } for row in rows
            ]
        except Error as err:
            print("Failed to fetch liked recipes:", err)
            return []

    def has_user_liked_recipe(self, user_id: int, recipe_id: int):
        query = "select 1 from Likes where user_id = %s and recipe_id = %s limit 1"
        try:
            self.cursor.execute(query, (user_id, recipe_id))
            return self.cursor.fetchone() is not None
        except Error as err:
            print("Failed to check like:", err)
            return False

    def add_recipe_like(self, user_id: int, recipe_id: int):
        query = "insert ignore into Likes (recipe_id, user_id) values (%s, %s)"
        try:
            self.cursor.execute(query, (recipe_id, user_id))
            self.cnx.commit()
            return True
        except Error as err:
            print("Failed to like recipe:", err)
            self.cnx.rollback()
            return False

    def remove_recipe_like(self, user_id: int, recipe_id: int):
        query = "delete from Likes where recipe_id = %s and user_id = %s"
        try:
            self.cursor.execute(query, (recipe_id, user_id))
            self.cnx.commit()
            return True
        except Error as err:
            print("Failed to unlike recipe:", err)
            self.cnx.rollback()
            return False

    def is_following_user(self, target_user_id: int, follower_id: int):
        query = "select 1 from Followers where user_id = %s and follower_id = %s limit 1"
        try:
            self.cursor.execute(query, (target_user_id, follower_id))
            return self.cursor.fetchone() is not None
        except Error as err:
            print("Failed to check following:", err)
            return False

    def follow_user(self, target_user_id: int, follower_id: int):
        if target_user_id == follower_id:
            return False
        query = "insert ignore into Followers (user_id, follower_id) values (%s, %s)"
        try:
            self.cursor.execute(query, (target_user_id, follower_id))
            self.cnx.commit()
            return True
        except Error as err:
            print("Follow failed:", err)
            self.cnx.rollback()
            return False

    def unfollow_user(self, target_user_id: int, follower_id: int):
        if target_user_id == follower_id:
            return False
        query = "delete from Followers where user_id = %s and follower_id = %s"
        try:
            self.cursor.execute(query, (target_user_id, follower_id))
            self.cnx.commit()
            return True
        except Error as err:
            print("Unfollow failed:", err)
            self.cnx.rollback()
            return False
