import os
from dotenv import load_dotenv

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import (
    UserAddForm,
    LoginForm,
    MessageForm,
    CSRFProtectForm,
    UserEditForm,
)
from models import db, connect_db, User, Message

load_dotenv()

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SQLALCHEMY_ECHO"] = False
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = True
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


@app.before_request
def add_csrf_form_to_g():
    """Add a csrf form to Flask global"""

    g.csrf_form = CSRFProtectForm()


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Log out user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    if g.user:
        return redirect("/")

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", "danger")
            return render_template("users/signup.html", form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template("users/signup.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login and redirect to homepage on success."""

    if g.user:
        return redirect("/")

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(
            form.username.data,
            form.password.data,
        )

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", "danger")

    return render_template("users/login.html", form=form)


@app.post("/logout")
def logout():
    """Handle logout of user and redirect to homepage."""

    form = g.csrf_form

    if form.validate_on_submit():
        do_logout()
        flash("Logged out, Going so soon :(", "success")
        return redirect("/login")

    else:
        flash("Access unauthorized.", "danger")
        return redirect("/")


##############################################################################
# General user routes:


@app.get("/users")
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    search = request.args.get("q")

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template("users/index.html", users=users)


@app.get("/users/<int:user_id>")
def show_user(user_id):
    """Show user profile."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)

    return render_template("users/show.html", user=user)


@app.get("/users/<int:user_id>/following")
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template("users/following.html", user=user)


@app.get("/users/<int:user_id>/followers")
def show_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template("users/followers.html", user=user)


@app.post("/users/follow/<int:follow_id>")
def start_following(follow_id):
    """Add a follow for the currently-logged-in user.

    Redirect to following page for the current for the current user.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = g.csrf_form

    if form.validate_on_submit():
        followed_user = User.query.get_or_404(follow_id)
        g.user.following.append(followed_user)
        db.session.commit()

        return redirect(f"/users/{g.user.id}/following")

    else:
        flash("Access unauthorized.", "danger")
        return redirect("/")


@app.post("/users/stop-following/<int:follow_id>")
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user.

    Redirect to following page for the current for the current user.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = g.csrf_form

    if form.validate_on_submit():
        followed_user = User.query.get_or_404(follow_id)
        g.user.following.remove(followed_user)
        db.session.commit()

        return redirect(f"/users/{g.user.id}/following")
    else:
        flash("Access unauthorized.", "danger")
        return redirect("/")


@app.route("/users/profile", methods=["GET", "POST"])
def profile():
    """Update profile for current user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = UserEditForm(obj=g.user)

    if form.validate_on_submit():
        valid_pass = User.authenticate(
            g.user.username,
            form.password.data,
        )

        if valid_pass:
            try:
                data = {
                    k: v
                    for k, v in form.data.items()
                    if k != "csrf_token" and k != "password"
                }
                g.user.edit_user(**data)
                db.session.commit()
            except IntegrityError:
                flash("Username already taken", "danger")
                return render_template("users/edit.html", form=form)

        return redirect(f"/users/{g.user.id}")
    else:
        return render_template("users/edit.html", form=form)


@app.post("/users/delete")
def delete_user():
    """Delete user.

    Redirect to signup page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = g.csrf_form

    if form.validate_on_submit():
        do_logout()
        User.query.filter_by(id=g.user.id).delete()
        db.session.commit()

        return redirect("/signup")
    else:
        flash("Access unauthorized.", "danger")
        return redirect("/")


##############################################################################
# Messages routes:


@app.route("/messages/new", methods=["GET", "POST"])
def add_message():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template("messages/create.html", form=form)


@app.get("/messages/<int:message_id>")
def show_message(message_id):
    """Show a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get_or_404(message_id)
    return render_template("messages/show.html", message=msg)


@app.post("/messages/<int:message_id>/delete")
def delete_message(message_id):
    """Delete a message.

    Check that this message was written by the current user.
    Redirect to user page on success.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = g.csrf_form

    if form.validate_on_submit():
        msg = Message.query.get_or_404(message_id)
        db.session.delete(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")
    else:
        flash("Access unauthorized.", "danger")
        return redirect("/")


##############################################################################
# Homepage and error pages


@app.get("/")
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of self & followed_users
    """
    if g.user:
        # If we're logged in as user
        # we want messages to be the users messages and the user they are following
        # messages
        show_tweets_from_users_ids = [
            followed_user.id for followed_user in g.user.following
        ]
        show_tweets_from_users_ids.append(g.user.id)
        messages = (
            Message.query.order_by(Message.timestamp.desc())
            .filter(Message.user_id.in_(show_tweets_from_users_ids))
            .limit(100)
            .all()
        )

        return render_template("home.html", messages=messages)

    else:
        return render_template("home-anon.html")


@app.after_request
def add_header(response):
    """Add non-caching headers on every request."""

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    response.cache_control.no_store = True
    return response