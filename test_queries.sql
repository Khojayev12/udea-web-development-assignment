USE recipedb;

-- Recipes with author information and aggregate engagement
SELECT
  r.recipe_id,
  r.title,
  CONCAT(u.name, ' ', u.surname) AS author_name,
  COUNT(DISTINCT l.like_id) AS like_count,
  COUNT(DISTINCT rat.rate_id) AS rating_count,
  AVG(rat.rating) AS avg_user_rating
FROM Recipes r
JOIN Users u ON r.author_id = u.user_id
LEFT JOIN Likes l ON l.recipe_id = r.recipe_id
LEFT JOIN Ratings rat ON rat.recipe_id = r.recipe_id
GROUP BY r.recipe_id, r.title, author_name
ORDER BY like_count DESC, rating_count DESC;

-- Follower relationships showing who follows whom
SELECT
  CONCAT(followed.name, ' ', followed.surname) AS user_name,
  CONCAT(follower.name, ' ', follower.surname) AS follower_name,
  f.date_followed
FROM Followers f
JOIN Users followed ON f.user_id = followed.user_id
JOIN Users follower ON f.follower_id = follower.user_id
ORDER BY f.date_followed DESC;

-- Ratings with recipe titles and reviewer names
SELECT
  r.title,
  CONCAT(u.name, ' ', u.surname) AS reviewer,
  rat.date_posted,
  rat.comment
FROM Ratings rat
JOIN Recipes r ON rat.recipe_id = r.recipe_id
JOIN Users u ON rat.user_id = u.user_id
ORDER BY rat.date_posted DESC;

-- Ingredient list for each recipe
SELECT
  r.title,
  GROUP_CONCAT(i.ingredient ORDER BY i.ingredient SEPARATOR ', ') AS ingredient_list
FROM Ingredients i
JOIN Recipes r ON i.recipe_id = r.recipe_id
GROUP BY r.recipe_id, r.title
ORDER BY r.title;

-- Tag cloud per recipe with nutrition context
SELECT
  r.title,
  r.category,
  CONCAT(FORMAT(r.calories, 0), ' kcal') AS calories,
  GROUP_CONCAT(t.tag_name ORDER BY t.tag_name SEPARATOR ', ') AS tags
FROM Tags t
JOIN Recipes r ON t.recipe_id = r.recipe_id
GROUP BY r.recipe_id, r.title, r.category, r.calories
ORDER BY r.category, r.title;


select * from Users


ALTER TABLE Users
    MODIFY name VARCHAR(100) NULL,
    MODIFY surname VARCHAR(100) NULL,
    MODIFY about_me TEXT NULL,
    MODIFY profile_img_path VARCHAR(255) NULL,
    MODIFY date_registered DATETIME NULL;