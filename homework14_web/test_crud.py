import schemas
import unittest
from jose import jwt
from models import User, Contact
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, date
from crud import (create_user, get_user, authenticate_user, create_access_token,
                  get_current_user, get_contact, get_contacts, create_contact,
                  update_contact, delete_contact, search_contacts, get_upcoming_birthdays)

class TestUserManagement(unittest.TestCase):
    def setUp(self):
        """
        The setUp function is called before each test function.
        It creates a mock database object, and a user_data object that will be used to create the user.
        The user is created with an email address and hashed password, which are then stored in the db.

        :param self: Represent the instance of the object that is using the method
        :return: An instance of the user model, with email and hashed_password attributes
        :doc-author: Trelent
        """
        self.db = MagicMock(spec=Session)
        self.user_data = schemas.UserCreate(email="test@example.com", password="password123")
        self.user = User(email=self.user_data.email, hashed_password="hashed_password")
        self.user.is_active = True

    def test_create_user(self):
        """
        The test_create_user function tests the create_user function in the user.py file.
        It does this by mocking out all of the functions that are called within create_user, and then
        checking to see if they were called correctly.

        :param self: Represent the instance of the class
        :return: The user object
        :doc-author: Trelent
        """
        self.db.query(User).filter().first.return_value = None
        self.db.add.return_value = None
        self.db.commit.return_value = None
        self.db.refresh.return_value = None
        result = create_user(self.db, self.user_data)
        self.assertEqual(result.email, self.user_data.email)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

    def test_get_user(self):
        """
        The test_get_user function tests the get_user function.
        It does this by mocking out the database and returning a user object when queried.
        The test then asserts that the result of calling get_user is equal to our mocked user.

        :param self: Refer to the instance of the class
        :return: The user
        :doc-author: Trelent
        """
        self.db.query(User).filter().first.return_value = self.user

        result = get_user(self.db, self.user.email)
        self.assertEqual(result, self.user)

    def test_create_access_token(self):
        """
        The test_create_access_token function tests the create_access_token function in the auth.py file.
        The test creates a user and then uses that user's email to generate an access token using the
        create_access_token function from auth.py, which is imported at the top of this file.

        :param self: Represent the instance of the class
        :return: A token that is a string
        :doc-author: Trelent
        """
        data = {"sub": self.user.email}
        token = create_access_token(data)
        self.assertTrue(isinstance(token, str))

    def test_get_current_user(self):
        """
        The test_get_current_user function tests the get_current_user function.
        It does this by creating a token, setting the return value of self.db.query(User).filter().first to be self.user,
        and then patching jose's decode method to return {&quot;sub&quot;: self.user}.email (which is &quot;test@example&quot;).
        The result should be that get_current_user returns our user.

        :param self: Access the class attributes and methods
        :return: The user
        :doc-author: Trelent
        """
        token = create_access_token({"sub": self.user.email})
        self.db.query(User).filter().first.return_value = self.user
        with patch("jose.jwt.decode", return_value={"sub": self.user.email}):
            result = get_current_user(self.db, token)
            self.assertEqual(result, self.user)

    def test_get_contact(self):
        """
        The test_get_contact function tests the get_contact function.
        It does this by creating a mock database object, and then setting up that mock to return a Contact object when it is queried.
        The test then calls the get_contact function with the mocked database and an id of 1, which should return that Contact object.

        :param self: Access the instance of the class
        :return: The contact object
        :doc-author: Trelent
        """
        contact_id = 1
        contact = Contact(id=contact_id, first_name="John", last_name="Doe", owner_id=1)
        self.db.query(Contact).filter().first.return_value = contact
        result = get_contact(self.db, contact_id)
        self.assertEqual(result, contact)

    def test_get_contacts(self):
        """
        The test_get_contacts function tests the get_contacts function.
        It does this by creating a mock database object, and then setting up that mock to return a list of contacts when it is queried.
        The test then calls the get_contacts function with the mocked database object as an argument, and asserts that it returns what was set up in the mock.

        :param self: Represent the instance of the class
        :return: The contacts
        :doc-author: Trelent
        """
        user_id = 1
        contacts = [Contact(id=1, first_name="John", last_name="Doe", owner_id=user_id)]
        self.db.query(Contact).filter().offset().limit().all.return_value = contacts

        result = get_contacts(self.db, user_id)
        self.assertEqual(result, contacts)

    def test_create_contact(self):
        """
        The test_create_contact function tests the create_contact function in crud.py.
        It creates a contact object with the given data and adds it to the database, then commits it and refreshes it.

        :param self: Represent the instance of the class
        :return: The first_name of the contact_data
        :doc-author: Trelent
        """
        user_id = 1
        contact_data = schemas.ContactCreate(first_name="John", last_name="Doe", email="john.doe@example.com", phone_number='0000000000', birthday='2000-12-01')
        contact = Contact(id=1, **contact_data.dict(), owner_id=user_id)
        self.db.add.return_value = None
        self.db.commit.return_value = None
        self.db.refresh.return_value = contact
        result = create_contact(self.db, contact_data, user_id)
        self.assertEqual(result.first_name, contact_data.first_name)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

    def test_update_contact(self):
        """
        The test_update_contact function tests the update_contact function in crud.py.
        It creates a contact object and assigns it to the variable 'contact'. It then calls
        the update_contact function with the parameters of db, contact_id, and contact data.
        The result is compared to what was expected (in this case, that first name should be Jane).
        If they are equal, then we know that our test passed.

        :param self: Represent the instance of the class
        :return: The contact_data
        :doc-author: Trelent
        """
        contact_id = 1
        contact_data = schemas.ContactUpdate(first_name="Jane", last_name='Doe', email="", phone_number="0000000000", birthday='2023-12-01')
        contact = Contact(id=contact_id, first_name="John", last_name="Doe", owner_id=1)
        self.db.query(Contact).filter().first.return_value = contact
        result = update_contact(self.db, contact_id, contact_data)
        self.assertEqual(result.first_name, contact_data.first_name)
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

    def test_delete_contact(self):
        """
        The test_delete_contact function tests the delete_contact function.
        It does this by creating a mock contact object and setting it as the return value of query().first()
        Then, it calls delete_contact with that mock database and contact id. It asserts that the result is equal to our mocked contact object,
        and then asserts that db.delete() was called once with our mocked contact object.

        :param self: Represent the instance of the class
        :return: The contact that was deleted
        :doc-author: Trelent
        """
        contact_id = 1
        contact = Contact(id=contact_id, first_name="John", last_name="Doe", owner_id=1)
        self.db.query(Contact).filter().first.return_value = contact
        result = delete_contact(self.db, contact_id)
        self.assertEqual(result, contact)
        self.db.delete.assert_called_once_with(contact)
        self.db.commit.assert_called_once()

    def test_search_contacts(self):
        """
        The test_search_contacts function tests the search_contacts function.
        It does this by creating a mock database object, and then setting up that mock to return a list of contacts when it is queried.
        The test then calls the search_contacts function with the query &quot;John&quot; and user id 1, which should return all contacts whose first name is John.

        :param self: Represent the instance of the class
        :return: The contacts list
        :doc-author: Trelent
        """
        user_id = 1
        query = "Dexter"
        contacts = [Contact(id=1, first_name="Dexter", last_name="Morgan", owner_id=user_id)]
        self.db.query(Contact).filter().filter().all.return_value = contacts
        result = search_contacts(self.db, query, user_id)
        self.assertEqual(result, contacts)

    def test_get_upcoming_birthdays(self):
        """
        The test_get_upcoming_birthdays function tests the get_upcoming_birthdays function.
        It does this by creating a mock database object, and then setting up some test data to be returned from that mock database.
        The test data is a list of Contact objects with an id of 1, first name &quot;John&quot;, last name &quot;Doe&quot;, birthday 3 days from today, and owner id 1.
        Then it calls the get_upcoming_birthdays function with the mock db object and user id 1 as arguments. It asserts that result is equal to contacts.

        :param self: Represent the instance of the object that is passed to a method when it is called
        :return: The contacts list
        :doc-author: Trelent
        """
        user_id = 1
        today = date.today()
        next_week = today + timedelta(days=7)
        contacts = [Contact(id=1, first_name="Dexter", last_name="Morgan", birthday=today + timedelta(days=3), owner_id=user_id)]
        self.db.query(Contact).filter().filter().all.return_value = contacts
        result = get_upcoming_birthdays(self.db, user_id)
        self.assertEqual(result, contacts)

if __name__ == '__main__':
    unittest.main()