import hashlib    # um das Passwort in der DB unlesbar zu machen
import random
import uuid

from flask import Flask, render_template, request, make_response, redirect, url_for
from models import User

app = Flask(__name__)


@app.route("/", methods=["GET"])        # Controller für index-URL
def index():                            # index-Funktion
    session_token = request.cookies.get("session_token")

    if session_token:                   # Überprüfen, ob User bereits eingeloggt ist
        user = User.fetch_one(query=["session_token", "==", session_token])
    else:
        user = None

    return render_template("index.html", user=user)

@app.route("/login", methods=["POST"])   # Controller für login-URL
def login():                             # Login-Fkt.
    name = request.form.get("user-name")    # Variablen definieren, die man aus Eingaben des Users erhält
    email = request.form.get("user-email")
    password = request.form.get("user-password")    # passwort wird hier festgelegt, daher muss dieser Controller über dem profile-edit-Controller sein

    # hash the password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # create a secret number
    secret_number = random.randint(1, 30)

    # see if user already exists
    user = User.fetch_one(query=["email", "==", email])

    if not user:
        # create a User object
        user = User(name=name, email=email, secret_number=secret_number, password=hashed_password)
        user.create()  # save the object into a database

    # check if password is incorrect
    if hashed_password != user.password:
        return "WRONG PASSWORD! Go back and try again."
    elif hashed_password == user.password:
        session_token = str(uuid.uuid4())
        User.edit(obj_id=user.id, session_token=session_token)

        # save user's session token into a cookie
        response = make_response(redirect(url_for('index')))
        response.set_cookie("session_token", session_token)

        return response


@app.route("/profile", methods=["GET"])
def profile():
    session_token = request.cookies.get("session_token")    # Überprüfen, ob User bereits existiert

    # get user from the database
    user = User.fetch_one(query=["session_token", "==", session_token])

    if user:    # wenn user existiert, zum User-Profil
        return render_template("profile.html", user=user)
    else:       # ansonsten zu index zurück
        return redirect(url_for("index"))

@app.route("/profile/edit", methods=["GET", "POST"])    # Controller zur Profil-Bearbeitung mit GET und POST
def profile_edit():
    session_token = request.cookies.get("session_token")

    # get user from the database
    user = User.fetch_one(query=["session_token", "==", session_token])

    if request.method == "GET":
        if user:  # if user is found
            return render_template("profile_edit.html", user=user)
        else:
            return redirect(url_for("index"))

    elif request.method == "POST":
        name = request.form.get("profile-name")
        email = request.form.get("profile-email")
        old_password = request.form.get("old-password")
        new_password = request.form.get("new-password")

        if old_password and new_password:
            hashed_old_password = hashlib.sha256(old_password.encode()).hexdigest()  # hash the old password
            hashed_new_password = hashlib.sha256(new_password.encode()).hexdigest()  # hash the old password

            # check if old password hash is equal to the password hash in the database
            if hashed_old_password == user.password:
                User.edit(obj_id=user.id, name=name, email=email,
                          password=hashed_new_password)  # if yes, save the new password hash in the database
            else:
                return "Wrong (old) password! Go back and try again."
        else:
            User.edit(obj_id=user.id, name=name, email=email)

        return redirect(url_for("profile"))

@app.route("/profile/delete", methods=["GET", "POST"])
def profile_delete():
    session_token = request.cookies.get("session_token")

    # get user from the database
    user = User.fetch_one(query=["session_token", "==", session_token])

    if request.method == "GET":
        if user:  # if user is found
            return render_template("profile_delete.html", user=user)
        else:
            return redirect(url_for("index"))

    elif request.method == "POST":
        User.delete(obj_id=user.id)

        return redirect(url_for("index"))


@app.route("/users", methods=["GET"])       # Controller für users-URL
def all_users():                            # Funktion all_users
    users = User.fetch()                    # User aus der DB holen

    return render_template("users.html", users=users)

@app.route("/user/<user_id>", methods=["GET"])  # Controller für User Details (alles was in Variable user_id gespeichert wird
def user_details(user_id):
    user = User.get(obj_id=user_id)

    return render_template("user_details.html", user=user)




@app.route("/result", methods=["POST"])
def result():
    # create a secret number
    secret_number = random.randint(1, 30)

    guess = int(request.form.get("guess"))

    session_token = request.cookies.get("session_token")

    # get user from the database
    user = User.fetch_one(query=["session_token", "==", session_token])

    if guess == user.secret_number:
        message = "Correct! The secret number is {0}".format(str(guess))

        # create a new random secret number
        new_secret = random.randint(1, 30)

        # update the user's secret number in the User collection
        User.edit(obj_id=user.id, secret_number=secret_number)
    elif guess > user.secret_number:
        message = "Your guess is not correct... try something smaller."
    elif guess < user.secret_number:
        message = "Your guess is not correct... try something bigger."

    return render_template("result.html", message=message)


if __name__ == '__main__':
    app.run(debug=False)