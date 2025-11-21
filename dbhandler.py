import mysql.connector
from mysql.connector import Error

class DBHandler():
    def __init__(self):
        try:
            self.cnx = mysql.connector.connect(user='root', password='Scripter1211#',
                                host='localhost',
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
        query = f"insert into Users(email, password, name, surname, about_me, profile_img_path, date_registered, role) values('{login}', '{password}', '{name}', NULL, NULL, NULL, DATE_ADD(NOW(), INTERVAL 5 HOUR), 'user')"
        try:
            self.cursor.execute(query)
            self.cnx.commit()
            return True
        except Error as err:
            print(err)
            self.cnx.rollback()
            return False
