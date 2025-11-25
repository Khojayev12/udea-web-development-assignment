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

    def fetch_recent_recipes(self, limit=4):
        """Return a list of the most recent recipes with id, title, and cover image."""
        query = "select recipe_id, title, cover_img_path from Recipes order by date_posted desc limit %s"
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
        query = "select recipe_id, title, cover_img_path from Recipes order by date_posted desc limit %s offset %s"
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

    def fetch_recipe_detail(self, recipe_id: int):
        """Return full recipe details for a given recipe_id."""
        recipe_query = """
            select recipe_id, title, rating, cover_img_path, prepare_time, calories,
                   protein, carbs, fats, sugar, fiber, procedure_description
            from Recipes
            where recipe_id = %s
        """
        ing_query = "select ingredient from Ingredients where recipe_id = %s order by ingredient_id"
        tag_query = "select tag_name from Tags where recipe_id = %s order by tag_id"
        review_query = """
            select coalesce(u.name, 'User') as name, coalesce(u.surname, '') as surname, r.comment
            from Ratings r
            left join Users u on r.user_id = u.user_id
            where r.recipe_id = %s
            order by r.date_posted desc
            limit 5
        """
        try:
            self.cursor.execute(recipe_query, (recipe_id,))
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
                "rating": recipe_row[2],
                "cover_img_path": recipe_row[3],
                "prepare_time": recipe_row[4],
                "calories": recipe_row[5],
                "protein": recipe_row[6],
                "carbs": recipe_row[7],
                "fats": recipe_row[8],
                "sugar": recipe_row[9],
                "fiber": recipe_row[10],
                "procedure_description": recipe_row[11] or "",
                "ingredients": [row[0] for row in ing_rows],
                "tags": [row[0] for row in tag_rows],
                "reviews": [
                    {
                        "author": (row[0] + (" " + row[1] if row[1] else "")).strip(),
                        "content": row[2]
                    } for row in review_rows if row[2]
                ],
            }
            recipe["rating_count"] = len(review_rows)
            return recipe
        except Error as err:
            print("Failed to fetch recipe detail:", err)
            return None

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
            self.cursor.execute("select distinct category from Recipes where category is not null order by category")
            categories = [row[0] for row in self.cursor.fetchall() if row[0]]
            self.cursor.execute("select distinct difficulty from Recipes where difficulty is not null order by difficulty")
            difficulties = [row[0] for row in self.cursor.fetchall() if row[0]]
        except Error as err:
            print("Failed to fetch filter lists:", err)
        return {"categories": categories, "difficulties": difficulties}

    def fetch_feed_count(self, category=None, difficulty=None, max_time=None):
        """Count recipes matching filters."""
        base = ["select count(*) from Recipes where 1=1"]
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
                where r.author_id = %s
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
                where r.author_id = %s
                """,
                (user_id,)
            )
            stats["reviews"] = self.cursor.fetchone()[0] or 0

            self.cursor.execute("select count(*) from Recipes where author_id = %s", (user_id,))
            stats["posted"] = self.cursor.fetchone()[0] or 0

            self.cursor.execute(
                """
                select avg(rt.rating), count(rt.rating)
                from Ratings rt
                join Recipes r on rt.recipe_id = r.recipe_id
                where r.author_id = %s
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

    def fetch_user_recipes(self, user_id: int, limit=8):
        query = """
            select recipe_id, title, cover_img_path, rating, prepare_time
            from Recipes
            where author_id = %s
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
            where l.user_id = %s
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
