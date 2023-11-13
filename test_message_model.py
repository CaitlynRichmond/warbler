"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from models import (
    db,
    User,
    Message,
    Follow,
    DEFAULT_HEADER_IMAGE_URL,
    DEFAULT_LOCATION,
    DEFAULT_IMAGE_URL,
)
from sqlalchemy.exc import IntegrityError, DataError

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ["DATABASE_URL"] = "postgresql:///warbler_test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class MessageModelTestCase(TestCase):
    def setUp(self):
        # Only deleting user because messages for them are deleted by cascade
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id

        m1 = Message(text="test", user_id=u1.id)
        db.session.add(m1)
        db.session.commit()

        self.m1_id = m1.id

    def tearDown(self):
        db.session.rollback()

    def test_message_model(self):
        """Tests that messages don't have any likes on start and m1 is tied to u1"""
        m1 = Message.query.get(self.m1_id)
        u1 = User.query.get(self.u1_id)
        # Message should have no likes
        self.assertEqual(m1.user, u1)
        self.assertEqual(len(m1.likes), 0)

    def test_create_message_bad_user_id(self):
        "Tests non-existent user id fail case"
        with self.assertRaises(IntegrityError):
            m2 = Message(text="test", user_id=0)
            db.session.add(m2)
            db.session.commit()

    def test_create_message_bad_text_is_none(self):
        """Tets bad case text is none"""
        with self.assertRaises(IntegrityError):
            m2 = Message(text=None, user_id=0)
            db.session.add(m2)
            db.session.commit()

    def test_create_message_bad_text_is_too_long(self):
        """Tests bad case for making a message text is too long"""
        with self.assertRaises(DataError):
            m2 = Message(
                text=(
                    "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
                    + "Duis eget condimentum eros, eu elementum dui. Maecenas"
                    + "erat enim, mollis sit mauris tis et."
                ),
                user_id=self.u1_id,
            )
            db.session.add(m2)
            db.session.commit()

    ################################################################
    # Likes Tests
    def test_message_likes(self):
        """Tests the relationships for likes"""

        m1 = Message.query.get(self.m1_id)
        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u1_id)

        u1.likes.append(m1)
        m1.likes.append(u2)

        self.assertIn(m1, u1.likes)
        self.assertIn(u1, m1.likes)
        self.assertIn(u2, m1.likes)
