import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_registrations")
def get_registrations():
    registrations = list(mongo.db.registrations.find().sort("event_name"))
    return render_template("registrations.html", registrations=registrations)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                        session["user"] = request.form.get("username").lower()
                        flash("Welcome, {}".format(
                            request.form.get("username")))
                        return redirect(url_for(
                            "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_registration", methods=["GET", "POST"])
def add_registration():
    if request.method == "POST":
        registration = {
            "event_name": request.form.get("event_name"),
            "registration_name": request.form.get("registration_name"),
            "email": request.form.get("email"),
            "gender": request.form.get("gender"),
            "birthday": request.form.get("birthday"),
            "registration_comment": request.form.get("registration_comment"),
            "created_by": session["user"]
        }
        mongo.db.registrations.insert_one(registration)
        flash("Registration Successfully Added")
        return redirect(url_for("get_registrations"))

    events = mongo.db.events.find().sort("event_name", 1)
    return render_template("add_registration.html", events=events)


@app.route("/edit_registration/<registration_id>", methods=["GET", "POST"])
def edit_registration(registration_id):
    if request.method == "POST":
        submit = {
            "event_name": request.form.get("event_name"),
            "registration_name": request.form.get("registration_name"),
            "email": request.form.get("email"),
            "gender": request.form.get("gender"),
            "birthday": request.form.get("birthday"),
            "registration_comment": request.form.get("registration_comment"),
            "created_by": session["user"]
        }
        mongo.db.registrations.update({"_id": ObjectId(registration_id)}, submit)
        flash("Registration Successfully Updated")

    registration = mongo.db.registrations.find_one({"_id": ObjectId(registration_id)})
    events = mongo.db.events.find().sort("event_name", 1)
    return render_template("edit_registration.html", registration=registration, events=events)


@app.route("/delete_registration/<registration_id>")
def delete_registration(registration_id):
    mongo.db.registrations.remove({"_id": ObjectId(registration_id)})
    flash("Registration Successfully Deleted")
    return redirect(url_for("get_registrations"))


@app.route("/get_events")
def get_events():
    events = list(mongo.db.events.find().sort("event_name", 1))
    return render_template("events.html", events=events)


@app.route("/add_event", methods=["GET", "POST"])
def add_event():
    if request.method == "POST":
        event = {
            "event_name": request.form.get("event_name")
        }
        mongo.db.events.insert_one(event)
        flash("New Event Added")
        return redirect(url_for("get_events"))

    return render_template("add_event.html")


@app.route("/edit_event/<event_id>", methods=["GET", "POST"])
def edit_event(event_id):
    if request.method == "POST":
        submit = {
            "event_name": request.form.get("event_name")
        }
        mongo.db.events.update({"_id": ObjectId(event_id)}, submit)
        flash("Event Successfully Updated")
        return redirect(url_for("get_events"))

    event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
    return render_template("edit_event.html", event=event)


@app.route("/delete_event/<event_id>")
def delete_event(event_id):
    mongo.db.events.remove({"_id": ObjectId(event_id)})
    flash("Event Successfully Deleted")
    return redirect(url_for("get_events"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)
 
