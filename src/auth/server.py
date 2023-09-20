import os, jwt, datetime, traceback
from flask import Flask, request
from flask_mysqldb import MySQL
import bcrypt

server = Flask(__name__)
mysql = MySQL(server)

# config
server.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST")
server.config["MYSQL_USER"] = os.environ.get("MYSQL_USER")
server.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD")
server.config["MYSQL_DB"] = os.environ.get("MYSQL_DB")
server.config["MYSQL_PORT"] = int(os.environ.get("MYSQL_PORT"))


@server.route("/signup", methods=["POST"])
def signup():
    creds = request.form

    if not creds:
        return "missing credentials", 401

    email = creds["email"]
    password = creds["password"]
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    # to-do: Implement logging

    try:
        cur = mysql.connection.cursor()

        res = cur.execute(
            "SELECT email, password FROM user WHERE email=%s", (email,)
        )

        if res > 0:
            return "Registration Failed. USER ALREADY EXISTS!", 400

        cur.execute(
            "INSERT INTO user (email, password) VALUES (%s, %s)", (email, hashed_password)
        )
        mysql.connection.commit()

        return createJWT(email, os.environ.get("JWT_SECRET"), True)
    except:
        return "Error while registering User", 500


@server.route("/login", methods=["POST"])
def login():
    auth = request.authorization

    if not auth:
        return "missing credentials", 401
    
    # now we will check in the db for username and password verification
    try:
        cur = mysql.connection.cursor()
    except Exception as err:
        return "SQL CONNECTION ESTABLISHMENT FAILED!", 500
    try:
        res = cur.execute(
            "SELECT email, password FROM user WHERE email=%s", (auth.username,)
        )
    except Exception as err:
        return "error while trying to run sql query", 500

    if res > 0:
        user_row = cur.fetchone()
        hashed_password_db = user_row[1]
        hashed_password_login = bcrypt.hashpw(auth.password.encode("utf-8"), hashed_password_db.encode("utf-8"))
        password_to_check = auth.password

        if not bcrypt.checkpw(password_to_check.encode("utf-8"), hashed_password_db.encode("utf-8")):
            return f"Invalid credentials {hashed_password_login} is not same as {hashed_password_db}", 401
        
        return createJWT(auth.username, os.environ.get("JWT_SECRET"), True)

    else:
        return "Invalid credentials", 401


@server.route("/validate", methods=["POST"])
def validate():
    encoded_jwt = request.headers["Authorization"]

    if not encoded_jwt:
        return "missing credentials", 401

    encoded_jwt = encoded_jwt.split(" ")[1]

    try:
        decoded = jwt.decode(encoded_jwt, os.environ.get("JWT_SECRET"), algorithms=["HS256"])
    except:
        return "Not Authorized", 401

    return decoded, 200


def createJWT(username, secret, authz):
    return jwt.encode(
        {
            "username": username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),
            "iat": datetime.datetime.utcnow(),
            "admin": authz
        },
        secret,
        "HS256"
    )


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=5000)