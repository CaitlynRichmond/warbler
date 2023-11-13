"""Message View tests."""

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


class MessageBaseViewTestCase(TestCase):
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


class MessageAddViewTestCase(MessageBaseViewTestCase):
    def test_add_message(self):
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            # Now, that session setting is saved, so we can have
            # the rest of ours test
            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)

            new_message = Message.query.filter_by(text="Hello").one_or_none()

            self.assertIsNotNone(new_message)

    def test_add_message_logged_out(self):
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with app.test_client() as c:
            resp = c.post(
                "/messages/new",
                data={"text": "Hello"},
                follow_redirects=True,
            )
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)


class MessageShowViewTestCase(MessageBaseViewTestCase):
    def test_show_message_good(self):
        """Tests showing a message"""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/messages/{self.m1_id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                "This line for testing routes involving messages/show.html",
                html,
            )

            m1 = Message.query.get(self.m1_id)

            self.assertIn(m1.text, html)

    def test_show_message_bad_message_id_does_not_exist(self):
        """Tests showing a message with id that doesn't exist"""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/messages/0")

            self.assertEqual(resp.status_code, 404)

    def test_show_message_bad_logged_out(self):
        """Messages cannot be seen when logged out"""

        with app.test_client() as c:
            resp = c.get(
                f"/messages/{self.m1_id}",
                follow_redirects=True,
            )
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)


class MessageDeleteViewTestCase(MessageBaseViewTestCase):
    def test_delete_message(self):
        """Test deleting one of users own messages"""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(f"/messages/{self.m1_id}/delete")
            self.assertEqual(resp.status_code, 302)

            check_delete = Message.query.filter_by(
                text="m1-text"
            ).one_or_none()
            self.assertIsNone(check_delete)

    def test_delete_message_bad_message_id_does_not_exist(self):
        """404 if message does not exist"""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
            resp = c.post("/messages/0/delete")
            self.assertEqual(resp.status_code, 404)

    def test_delete_message_bad_other_user_message(self):
        """Cannot delete other user's messages"""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u2_id

            resp = c.post(
                f"/messages/{self.m1_id}/delete",
                follow_redirects=True,
            )
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_delete_message_bad_logged_out(self):
        """Messages cannot be deleted when logged out"""

        with app.test_client() as c:
            resp = c.post(
                f"/messages/{self.m1_id}/delete",
                follow_redirects=True,
            )
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)


class MessageToggleLikeViewTestCase(MessageBaseViewTestCase):
    def test_toggle_likes(self):
        """Add/remove message from likes for logged in user"""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u2_id

            resp = c.post(f"/messages/{self.m1_id}/like")

            self.assertEqual(resp.status_code, 302)

            u2 = User.query.get(self.u2_id)
            m1 = Message.query.get(self.m1_id)

            self.assertIn(m1, u2.likes)
            self.assertIn(u2, m1.likes)

            resp = c.post(f"/messages/{self.m1_id}/like")
            u2 = User.query.get(self.u2_id)
            m1 = Message.query.get(self.m1_id)
            self.assertNotIn(m1, u2.likes)
            self.assertNotIn(u2, m1.likes)

    def test_toggle_likes_bad_users_own_message(self):
        """Tests failure to like your own message"""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(
                f"/messages/{self.m1_id}/like", follow_redirects=True
            )
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_toggle_likes_bad_not_logged_in(self):
        """Tests failure to like message when not logged in"""
        with app.test_client() as c:
            resp = c.post(
                f"/messages/{self.m1_id}/like", follow_redirects=True
            )
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)
