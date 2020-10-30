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
@app.route("/get_tasks")
def get_tasks():
    tasks = list(mongo.db.tasks.find())
    return render_template("tasks.html", tasks=tasks)


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


@app.route("/add_task", methods=["GET", "POST"])
def add_task():
    if request.method == "POST":
        task = {
            "event_name": request.form.get("event_name"),
            "task_name": request.form.get("task_name"),
            "task_description": request.form.get("task_description"),
            "due_date": request.form.get("due_date"),
            "created_by": session["user"]
        }
        mongo.db.tasks.insert_one(task)
        flash("Task Successfully Added")
        return redirect(url_for("get_tasks"))

    events = mongo.db.events.find().sort("event_name", 1)
    return render_template("add_task.html", events=events)


@app.route("/edit_task/<task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    if request.method == "POST":
        submit = {
            "event_name": request.form.get("event_name"),
            "task_name": request.form.get("task_name"),
            "task_description": request.form.get("task_description"),
            "due_date": request.form.get("due_date"),
            "created_by": session["user"]
        }
        mongo.db.tasks.update({"_id": ObjectId(task_id)}, submit)
        flash("Task Successfully Updated")

    task = mongo.db.tasks.find_one({"_id": ObjectId(task_id)})
    events = mongo.db.events.find().sort("event_name", 1)
    return render_template("edit_task.html", task=task, events=events)


@app.route("/delete_task/<task_id>")
def delete_task(task_id):
    mongo.db.tasks.remove({"_id": ObjectId(task_id)})
    flash("Task Successfully Deleted")
    return redirect(url_for("get_tasks"))


@app.route("/get_events")
def get_events():
    events = list(mongo.db.categories.find().sort("event_name", 1))
    return render_template("event.html", events=events)


@app.route("/add_event", methods=["GET", "POST"])
def add_event():
    if request.method == "POST":
        event = {
            "event_name": request.form.get("event_name")
        }
        mongo.db.events.insert_one(event)
        flash("New Event Added")
        return redirect(url_for("get_events"))

    return render_template("add_events.html")


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
            debug=True)