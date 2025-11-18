import mysql.connector

class DBHandler():
    def __init__(self):
        self.cnx = mysql.connector.connect(user='root', password='Scripter1211#',
                              host='localhost',
                              database='recipedb')
        self.cursor = self.cnx.cursor()
        print("DBhandler initiated")
    def closer_connection(self):
        self.cnx.close()
        print("Database connection closed!")
    def check_user_login(self, login, password):
        query = f"select user_id from Users where email='{login}' and password='{password}'"
        self.cursor.execute(query)
        result = self.cursor.fetchall()[0][0]
        print("result: ", result)
        return result
