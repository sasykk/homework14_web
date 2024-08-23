import crud
import pytest
from main import app
from database import Base, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    """
    The client function is a fixture that creates the database and returns a test client.
    The test client can be used to make requests to the API, which will be run against an in-memory SQLite database.
    After all tests have been run, the database is dropped.

    :return: A testclient instance
    :doc-author: Trelent
    """
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as client:
        yield client
    Base.metadata.drop_all(bind=engine)

def test_register_user(client):
    """
    The test_register_user function tests the /auth/register endpoint.
    It does so by making a POST request to that endpoint with an email and password,
    and then asserts that the response has status code 200 (OK) and contains an email key in its JSON body.

    :param client: Make requests to the flask application
    :return: A 200 response and a json object with the email address
    :doc-author: Trelent
    """
    response = client.post("/auth/register", json={"email": "test@example.com", "password": "password"})
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

def test_login(client):
    """
    The test_login function tests the login endpoint.
    It does so by sending a POST request to /auth/token with the username and password of our test user.
    If this is successful, we should get back an access token in JSON format.

    :param client: Make requests to the flask application
    :return: A token that can be used to authenticate with the api
    :doc-author: Trelent
    """
    response = client.post("auth/token", data={"username": "test@example.com", "password": "password"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_verify_email(client):
    """
    The test_verify_email function tests the /auth/verify endpoint.
    It does so by creating a user, generating an access token for that user, and then calling the /auth/verify endpoint with that token.
    The test asserts that the response status code is 200 (OK), and also checks to make sure that the JSON response contains a msg key with value &quot;Email verified successfully&quot;.
    Finally, it refreshes our database session to ensure we have up-to-date data about our User object in memory.

    :param client: Make requests to the api
    :return: A status code of 200, a message saying &quot;email verified successfully&quot;, and asserts that the user is active
    :doc-author: Trelent
    """
    db = TestingSessionLocal()
    user = crud.get_user(db, email="test@example.com")
    token = crud.create_access_token(data={"sub": user.email})
    response = client.get(f"/auth/verify?token={token}")
    assert response.status_code == 200
    assert response.json()["msg"] == "Email verified successfully"
    db.refresh(user)
    assert user.is_active

def test_create_contact(client):
    """
    The test_create_contact function tests the creation of a contact.
    It does so by first logging in as the test user, then creating a new contact with valid data.
    The response is checked to ensure that it has an HTTP status code of 200 and that the returned JSON contains
    the correct first name.

    :param client: Make requests to the flask application
    :return: A response object
    :doc-author: Trelent
    """
    login_response = client.post("/auth/token", data={"username": "test@example.com", "password": "password"})
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    contact_data = {
        "first_name": "Dexter",
        "last_name": "Morgan",
        "email": "dexter@example.com",
        "phone_number": "123456789",
        "birthday": "2000-01-01"
    }

    response = client.post("/contacts/", json=contact_data, headers=headers)
    assert response.status_code == 200
    print(response.json())
    assert response.json()["first_name"] == "Dexter"