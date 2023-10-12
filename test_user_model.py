"""User model tests."""

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


class UserModelTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id

    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        u1 = User.query.get(self.u1_id)

        # User should have no messages & no followers
        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 0)

    #####################################################################
    # Following/Followers Tests

    def test_is_following_true(self):
        """Test case where u1 is following u2"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u1_id)
        u1.following.append(u2)

        self.assertTrue(u1.is_following(u2))
        self.assertIn(u2, u1.following)

    def test_is_following_false(self):
        """Test case where u1 isn't following u2"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u1_id)

        self.assertFalse(u1.is_following(u2))
        self.assertNotIn(u2, u1.following)

    def test_is_followed_by_true(self):
        """Test case where u1 is followed by u2"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u1_id)
        u1.followers.append(u2)

        self.assertTrue(u1.is_followed_by(u2))
        self.assertIn(u2, u1.followers)

    def test_is_followed_by_false(self):
        """Test case where u1 isn't followed by u2"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u1_id)

        self.assertFalse(u1.is_followed_by(u2))
        self.assertNotIn(u2, u1.followers)

    #################################################################
    # Signup Tests

    def test_good_user_signup(self):
        """Test good signup submission"""
        u3 = User.signup("u3", "u3@email.com", "password", None)
        db.session.add(u3)
        db.session.commit()

        users = User.query.all()

        self.assertIn(u3, users)
        self.assertEqual(u3.image_url, DEFAULT_IMAGE_URL)
        self.assertEqual(u3.header_image_url, DEFAULT_HEADER_IMAGE_URL)
        self.assertEqual(u3.location, DEFAULT_LOCATION)

    #############################
    # Signup Uniqueness Tests

    def test_user_signup_unique_fields(self):
        """Test bad signup for non unique submissions"""
        with self.assertRaises(IntegrityError):
            User.signup("u1", "bad_user@email.com", "password", None)
            db.session.commit()

    def test_user_signup_unique_email(self):
        with self.assertRaises(IntegrityError):
            User.signup("unique_user", "u1@email.com", "password", None)
            db.session.commit()

    #############################
    # Signup Lengths Tests

    def test_user_signup_too_username_input(self):
        """Test bad username length submission"""
        with self.assertRaises(DataError):
            User.signup(
                "1234567890123456789012345678901",
                "u5@email.com",
                "password",
                None,
            )
            db.session.commit()

    def test_user_signup_too_long_email_input(self):
        """Test bad email length submission"""
        with self.assertRaises(DataError):
            User.signup(
                "u5",
                "1234567890123456789012345678901234567890123456789031231",
                "password",
                None,
            )
            db.session.commit()

    def test_user_signup_no_password_input(self):
        """Test no password submission"""
        with self.assertRaises(ValueError):
            User.signup(
                "u5",
                "u5@email.com",
                "",
                None,
            )
            db.session.commit()

    ###########################################################
    # Authentication Tests
    def test_valid_user_authentication(self):
        """Test valid username and password authentication"""
        u1 = User.query.get(self.u1_id)
        self.assertEqual(User.authenticate("u1", "password"), u1)

    def test_invalid_username_authentication(self):
        """Test invalidvalid username authentication"""
        self.assertFalse(User.authenticate("u4", "password"))

    def test_invalid_password_authentication(self):
        """Test invalidvalid password authentication"""
        self.assertFalse(User.authenticate("u4", "badpassword"))
