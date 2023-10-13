"""User View tests."""

# run these tests like:
#
#    FLASK_DEBUG=False python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ["DATABASE_URL"] = "postgresql:///warbler_test"

# Now we can import app

from app import app, CURR_USER_KEY

app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False

# This is a bit of hack, but don't use Flask DebugToolbar

app.config["DEBUG_TB_HOSTS"] = ["dont-show-debug-toolbar"]

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config["WTF_CSRF_ENABLED"] = False


class UserBaseViewTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.flush()

        m1 = Message(text="m1-text", user_id=u1.id)
        db.session.add_all([m1])
        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id
        self.m1_id = m1.id


class UserShowHomeTestCase(UserBaseViewTestCase):
    """Show Homepage Test Cases"""

    def test_get_anon_homepage(self):
        """Show anon-homepage if not logged in"""

        with app.test_client() as client:
            resp = client.get("/")
            html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("This comment is for testing the home-anon.html", html)

    def test_get_logged_in_homepage(self):
        """Show homepage with warbles if logged in"""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get("/")
            html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("This comment is for testing the home.html", html)


class UserShowLoginAndSignupForms(UserBaseViewTestCase):
    """Show Signup and Login Pages Tests"""

    def test_logged_in_redirect_to_homepage(self):
        """Redirect to homepage if logged in and access /login"""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get("/login", follow_redirects=True)
            html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("This comment is for testing the home.html", html)

    def test_get_login_page(self):
        """Redirect to homepage if logged in and and try to access /login"""
        with app.test_client() as c:
            resp = c.get("/login")
            html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(
            "This comment is for testing showing /login.html page",
            html,
        )

    def test_get_signup_page(self):
        """display signup page if logged out"""
        with app.test_client() as c:
            resp = c.get("/signup")
            html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(
            "This comment is for testing showing /signup.html page",
            html,
        )

    def test_logged_in_redirect_signup_page(self):
        """redirect from signup page if logged in"""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get("/signup", follow_redirects=True)
            html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(
            "This comment is for testing the home.html",
            html,
        )


class UserLogoutViewTestCase(UserBaseViewTestCase):
    """Logout View Test Cases"""

    def test_logout_route(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
            resp = c.post("/logout", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertIn("Logged out, Going so soon :(", html)


class GeneralUserViewTestCases(UserBaseViewTestCase):
    """General view Test Cases"""

    def test_list_users_all(self):
        """Get page of existing users"""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

        resp = c.get("/users", follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(
            "This comment is for testing showing /index.html page",
            html,
        )
        self.assertIn("@u1", html)
        self.assertIn("@u2", html)

    def test_list_users_filter(self):
        """Get page of filtered existing users"""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

        resp = c.get("/users?q=u2", follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(
            "This comment is for testing showing /index.html page",
            html,
        )
        self.assertNotIn("@u1", html)
        self.assertIn("@u2", html)

    def test_list_users_logged_out(self):
        """Can't see a users if not logged in"""
        with app.test_client() as c:
            resp = c.get("/users", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)

            self.assertIn(
                "Access unauthorized.",
                html,
            )


class UserShowLikeViewTestCase(UserBaseViewTestCase):
    """Show Likes Test Cases"""

    def test_show_likes(self):
        """Show likes of a user when logged in"""
        m2 = Message(text="m2-text", user_id=self.u1_id)
        db.session.add(m2)
        u2 = User.query.get(self.u2_id)
        u2.likes.append(m2)
        db.session.commit()

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u2_id

            resp = c.get(f"/users/{self.u2_id}/likes")

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)

            self.assertIn(m2.text, html)
            self.assertIn(
                "This comment for testing routes involving user/likes.html",
                html,
            )

    def test_show_likes_bad_not_loggedin(self):
        """Can't see a users likes if not logged in"""
        with app.test_client() as c:
            resp = c.get(f"/users/{self.u2_id}/likes", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)

            self.assertIn(
                "Access unauthorized.",
                html,
            )
