-- Use InnoDB + utf8mb4 for FK support and proper text handling
SET NAMES utf8mb4;
SET sql_notes = 0;


create database recipedb

-- USERS
CREATE TABLE IF NOT EXISTS Users (
  user_id           INT AUTO_INCREMENT PRIMARY KEY,
  email             VARCHAR(255) NOT NULL UNIQUE,
  password          VARCHAR(255) NOT NULL,               -- store hash here
  name              VARCHAR(100) NOT NULL,
  surname           VARCHAR(100) NOT NULL,
  about_me          TEXT,
  profile_img_path  VARCHAR(255),
  date_registered   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  role              VARCHAR(20) NOT NULL DEFAULT 'user',
  CONSTRAINT chk_users_role CHECK (role IN ('user','admin'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- FOLLOWERS
CREATE TABLE IF NOT EXISTS Followers (
  relation_id   INT AUTO_INCREMENT PRIMARY KEY,
  user_id       INT NOT NULL,
  follower_id   INT NOT NULL,
  date_followed DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_follow_user    FOREIGN KEY (user_id)     REFERENCES Users(user_id) ON DELETE CASCADE,
  CONSTRAINT fk_follow_follower FOREIGN KEY (follower_id) REFERENCES Users(user_id) ON DELETE CASCADE,
  CONSTRAINT uq_follow UNIQUE (user_id, follower_id),
  CONSTRAINT chk_no_self_follow CHECK (user_id <> follower_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- RECIPES
CREATE TABLE IF NOT EXISTS Recipes (
  recipe_id             INT AUTO_INCREMENT PRIMARY KEY,
  title                 VARCHAR(200) NOT NULL,
  author_id             INT NOT NULL,
  category              VARCHAR(100),
  rating                DECIMAL(3,2),                    -- aggregate/denorm if you use it
  difficulty            VARCHAR(20),
  cover_img_path        VARCHAR(255),
  prepare_time          INT,                             -- minutes
  calories              DECIMAL(10,2),
  protein               DECIMAL(10,2),
  carbs                 DECIMAL(10,2),
  fats                  DECIMAL(10,2),
  sugar                 DECIMAL(10,2),
  fiber                 DECIMAL(10,2),
  procedure_description TEXT,
  date_posted           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_recipe_author FOREIGN KEY (author_id) REFERENCES Users(user_id) ON DELETE CASCADE,
  CONSTRAINT chk_prepare_time_nonneg CHECK (prepare_time IS NULL OR prepare_time >= 0),
  CONSTRAINT chk_nutrition_nonneg CHECK (
    (calories IS NULL OR calories >= 0) AND
    (protein  IS NULL OR protein  >= 0) AND
    (carbs    IS NULL OR carbs    >= 0) AND
    (fats     IS NULL OR fats     >= 0) AND
    (sugar    IS NULL OR sugar    >= 0) AND
    (fiber    IS NULL OR fiber    >= 0)
  )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Helpful search indexes
CREATE INDEX ix_recipes_author      ON Recipes(author_id);
CREATE INDEX ix_recipes_category    ON Recipes(category);
CREATE INDEX ix_recipes_dateposted  ON Recipes(date_posted);
-- Full-text for catalogue search (title + procedure)
CREATE FULLTEXT INDEX ft_recipes_title_procedure ON Recipes (title, procedure_description);

-- RATINGS
CREATE TABLE IF NOT EXISTS Ratings (
  rate_id      INT AUTO_INCREMENT PRIMARY KEY,
  recipe_id    INT NOT NULL,
  user_id      INT NOT NULL,
  date_posted  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  comment      TEXT,
  CONSTRAINT fk_rating_recipe FOREIGN KEY (recipe_id) REFERENCES Recipes(recipe_id) ON DELETE CASCADE,
  CONSTRAINT fk_rating_user   FOREIGN KEY (user_id)   REFERENCES Users(user_id)   ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX ix_ratings_recipe ON Ratings(recipe_id);
CREATE INDEX ix_ratings_user   ON Ratings(user_id);

-- LIKES
CREATE TABLE IF NOT EXISTS Likes (
  like_id     INT AUTO_INCREMENT PRIMARY KEY,
  recipe_id   INT NOT NULL,
  user_id     INT NOT NULL,
  date_liked  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_like_recipe FOREIGN KEY (recipe_id) REFERENCES Recipes(recipe_id) ON DELETE CASCADE,
  CONSTRAINT fk_like_user   FOREIGN KEY (user_id)   REFERENCES Users(user_id)   ON DELETE CASCADE,
  CONSTRAINT uq_like_once UNIQUE (recipe_id, user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- INGREDIENTS
CREATE TABLE IF NOT EXISTS Ingredients (
  ingredient_id INT AUTO_INCREMENT PRIMARY KEY,
  recipe_id     INT NOT NULL,
  ingredient    VARCHAR(255) NOT NULL,
  CONSTRAINT fk_ing_recipe FOREIGN KEY (recipe_id) REFERENCES Recipes(recipe_id) ON DELETE CASCADE,
  CONSTRAINT uq_ing_per_recipe UNIQUE (recipe_id, ingredient)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX ix_ing_recipe ON Ingredients(recipe_id);
CREATE FULLTEXT INDEX ft_ing_ingredient ON Ingredients (ingredient);

-- TAGS
CREATE TABLE IF NOT EXISTS Tags (
  tag_id    INT AUTO_INCREMENT PRIMARY KEY,
  recipe_id INT NOT NULL,
  tag_name  VARCHAR(100) NOT NULL,
  CONSTRAINT fk_tag_recipe FOREIGN KEY (recipe_id) REFERENCES Recipes(recipe_id) ON DELETE CASCADE,
  CONSTRAINT uq_tag_per_recipe UNIQUE (recipe_id, tag_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX ix_tag_recipe ON Tags(recipe_id);
CREATE INDEX ix_tag_name   ON Tags(tag_name);

SET sql_notes = 1;