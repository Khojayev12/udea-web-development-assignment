CREATE TABLE Followers (
  `relation_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `follower_id` int NOT NULL,
  `date_followed` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`relation_id`),
  UNIQUE KEY `uq_follow` (`user_id`,`follower_id`),
  KEY `fk_follow_follower` (`follower_id`),
  CONSTRAINT `fk_follow_follower` FOREIGN KEY (`follower_id`) REFERENCES `Users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_follow_user` FOREIGN KEY (`user_id`) REFERENCES `Users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `chk_no_self_follow` CHECK ((`user_id` <> `follower_id`))
) ENGINE=InnoDB AUTO_INCREMENT=57 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE Ingredients (
  `ingredient_id` int NOT NULL AUTO_INCREMENT,
  `recipe_id` int NOT NULL,
  `ingredient` varchar(255) NOT NULL,
  PRIMARY KEY (`ingredient_id`),
  UNIQUE KEY `uq_ing_per_recipe` (`recipe_id`,`ingredient`),
  KEY `ix_ing_recipe` (`recipe_id`),
  FULLTEXT KEY `ft_ing_ingredient` (`ingredient`),
  CONSTRAINT `fk_ing_recipe` FOREIGN KEY (`recipe_id`) REFERENCES `Recipes` (`recipe_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=129 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE Likes (
  `like_id` int NOT NULL AUTO_INCREMENT,
  `recipe_id` int NOT NULL,
  `user_id` int NOT NULL,
  `date_liked` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`like_id`),
  UNIQUE KEY `uq_like_once` (`recipe_id`,`user_id`),
  KEY `fk_like_user` (`user_id`),
  CONSTRAINT `fk_like_recipe` FOREIGN KEY (`recipe_id`) REFERENCES `Recipes` (`recipe_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_like_user` FOREIGN KEY (`user_id`) REFERENCES `Users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=61 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE Notifications (
  `notification_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `actor_id` int DEFAULT NULL,
  `recipe_id` int DEFAULT NULL,
  `type` enum('rating','follow','recipe_status') NOT NULL,
  `message` varchar(255) DEFAULT NULL,
  `is_read` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`notification_id`),
  KEY `fk_notif_actor` (`actor_id`),
  KEY `fk_notif_recipe` (`recipe_id`),
  KEY `ix_notif_user_read` (`user_id`,`is_read`,`created_at`),
  CONSTRAINT `fk_notif_actor` FOREIGN KEY (`actor_id`) REFERENCES `Users` (`user_id`) ON DELETE SET NULL,
  CONSTRAINT `fk_notif_recipe` FOREIGN KEY (`recipe_id`) REFERENCES `Recipes` (`recipe_id`) ON DELETE SET NULL,
  CONSTRAINT `fk_notif_user` FOREIGN KEY (`user_id`) REFERENCES `Users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE Ratings (
  `rate_id` int NOT NULL AUTO_INCREMENT,
  `recipe_id` int NOT NULL,
  `user_id` int NOT NULL,
  `date_posted` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `comment` text,
  `rating` decimal(2,1) NOT NULL DEFAULT '0.0',
  PRIMARY KEY (`rate_id`),
  KEY `ix_ratings_recipe` (`recipe_id`),
  KEY `ix_ratings_user` (`user_id`),
  CONSTRAINT `fk_rating_recipe` FOREIGN KEY (`recipe_id`) REFERENCES `Recipes` (`recipe_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_rating_user` FOREIGN KEY (`user_id`) REFERENCES `Users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `ratings_chk_1` CHECK (((`rating` >= 0) and (`rating` <= 5)))
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE Recipes (
  `recipe_id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(200) NOT NULL,
  `author_id` int NOT NULL,
  `category` varchar(100) DEFAULT NULL,
  `rating` decimal(3,2) DEFAULT NULL,
  `difficulty` varchar(20) DEFAULT NULL,
  `cover_img_path` varchar(255) DEFAULT NULL,
  `prepare_time` int DEFAULT NULL,
  `calories` decimal(10,2) DEFAULT NULL,
  `protein` decimal(10,2) DEFAULT NULL,
  `carbs` decimal(10,2) DEFAULT NULL,
  `fats` decimal(10,2) DEFAULT NULL,
  `sugar` decimal(10,2) DEFAULT NULL,
  `fiber` decimal(10,2) DEFAULT NULL,
  `procedure_description` text,
  `date_posted` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(50) NOT NULL DEFAULT 'unactive',
  PRIMARY KEY (`recipe_id`),
  KEY `ix_recipes_author` (`author_id`),
  KEY `ix_recipes_category` (`category`),
  KEY `ix_recipes_dateposted` (`date_posted`),
  FULLTEXT KEY `ft_recipes_title_procedure` (`title`,`procedure_description`),
  CONSTRAINT `fk_recipe_author` FOREIGN KEY (`author_id`) REFERENCES `Users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `chk_nutrition_nonneg` CHECK ((((`calories` is null) or (`calories` >= 0)) and ((`protein` is null) or (`protein` >= 0)) and ((`carbs` is null) or (`carbs` >= 0)) and ((`fats` is null) or (`fats` >= 0)) and ((`sugar` is null) or (`sugar` >= 0)) and ((`fiber` is null) or (`fiber` >= 0)))),
  CONSTRAINT `chk_prepare_time_nonneg` CHECK (((`prepare_time` is null) or (`prepare_time` >= 0)))
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE Tags (
  `tag_id` int NOT NULL AUTO_INCREMENT,
  `recipe_id` int NOT NULL,
  `tag_name` varchar(100) NOT NULL,
  PRIMARY KEY (`tag_id`),
  UNIQUE KEY `uq_tag_per_recipe` (`recipe_id`,`tag_name`),
  KEY `ix_tag_recipe` (`recipe_id`),
  KEY `ix_tag_name` (`tag_name`),
  CONSTRAINT `fk_tag_recipe` FOREIGN KEY (`recipe_id`) REFERENCES `Recipes` (`recipe_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=76 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE Users (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `surname` varchar(100) DEFAULT NULL,
  `about_me` text,
  `profile_img_path` varchar(255) DEFAULT NULL,
  `date_registered` datetime DEFAULT NULL,
  `role` varchar(20) NOT NULL DEFAULT 'user',
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`),
  CONSTRAINT `chk_users_role` CHECK ((`role` in (_utf8mb4'user',_utf8mb4'admin')))
) ENGINE=InnoDB AUTO_INCREMENT=77 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;