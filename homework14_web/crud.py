import schemas
from typing import Optional
from database import get_db
from jose import JWTError, jwt
from models import User, Contact
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status, Depends
from utils import get_password_hash, verify_password
from schemas import UserCreate, ContactCreate, ContactUpdate

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def create_user(db: Session, user: UserCreate):
    """
    The create_user function creates a new user in the database.
        Args:
            db (Session): The database session to use for this operation.
            user (UserCreate): The UserCreate object to create in the database.

    :param db: Session: Pass the database session to the function
    :param user: UserCreate: Create a new user in the database
    :return: A user object
    :doc-author: Trelent
    """
    db_user = User(email=user.email, hashed_password=get_password_hash(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, email: str):
    """
    The get_user function takes in a database session and an email address.
    It then queries the database for a user with that email address, and returns it.

    :param db: Session: Pass the database session to the function
    :param email: str: Specify the type of the parameter
    :return: A user object
    :doc-author: Trelent
    """
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    """
    The authenticate_user function takes in a database session, an email address and a password.
    It then checks to see if the user exists in the database by calling get_user with the email address.
    If no user is found, it returns False. If a user is found, it verifies that their password matches what's stored in the database using verify_password from passlib.

    :param db: Session: Pass in the database session to the function
    :param email: str: Pass the email address of the user to be authenticated
    :param password: str: Pass in the password that the user enters when they try to log in
    :return: A user object if the password is correct
    :doc-author: Trelent
    """
    user = get_user(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    The create_access_token function creates a JWT token with the given payload.
    The expiry time is set to 30 minutes by default, but can be overridden by passing an expires_delta parameter.


    :param data: dict: Store the data that will be encoded in the jwt
    :param expires_delta: Optional[timedelta]: Set the expiration time of the token
    :return: The encoded jwt
    :doc-author: Trelent
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """
    The get_current_user function is a dependency that will be used in the
        protected endpoints. It uses the OAuth2 authorization scheme to validate
        a user's credentials and return their information from our database.

    :param db: Session: Get access to the database
    :param token: str: Pass the token that is sent in the authorization header
    :return: The user that is currently logged in
    :doc-author: Trelent
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = get_user(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: schemas.User = Depends(get_current_user)):
    """
    The get_current_active_user function is a dependency that returns the current user,
    if they are active. If not, it raises an HTTPException with status code 400 and detail &quot;Inactive user&quot;.


    :param current_user: schemas.User: Get the current user from the database
    :return: The current user, but only if the user is active
    :doc-author: Trelent
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_contact(db: Session, contact_id: int):
    """
    The get_contact function takes in a database session and contact_id,
    and returns the first contact found with that id.


    :param db: Session: Pass in the database session
    :param contact_id: int: Specify the id of the contact to be retrieved
    :return: A contact object
    :doc-author: Trelent
    """
    return db.query(Contact).filter(Contact.id == contact_id).first()

def get_contacts(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    """
    The get_contacts function returns a list of contacts for the user with the given id.
    The skip and limit parameters are used to paginate through results.

    :param db: Session: Pass the database session to the function
    :param user_id: int: Filter the contacts by owner_id
    :param skip: int: Skip a number of records
    :param limit: int: Limit the number of contacts that are returned
    :return: A list of contacts
    :doc-author: Trelent
    """
    return db.query(Contact).filter(Contact.owner_id == user_id).offset(skip).limit(limit).all()

def create_contact(db: Session, contact: ContactCreate, user_id: int):
    """
    The create_contact function creates a new contact in the database.
        Args:
            db (Session): The database session to use for creating the contact.
            contact (ContactCreate): The data of the new contact to create.

    :param db: Session: Pass in the database session
    :param contact: ContactCreate: Create a contact object
    :param user_id: int: Identify the user that is creating the contact
    :return: The newly created contact
    :doc-author: Trelent
    """
    db_contact = Contact(**contact.dict(), owner_id=user_id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def update_contact(db: Session, contact_id: int, contact: ContactUpdate):
    """
    The update_contact function updates a contact in the database.
        Args:
            db (Session): The database session object.
            contact_id (int): The id of the contact to update.
            contact (ContactUpdate): A ContactUpdate object containing updated information for the specified user.

    :param db: Session: Pass the database session to the function
    :param contact_id: int: Identify the contact to update
    :param contact: ContactUpdate: Pass in the updated contact information
    :return: The updated contact
    :doc-author: Trelent
    """
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not db_contact:
        return None
    for key, value in contact.dict().items():
        setattr(db_contact, key, value)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def delete_contact(db: Session, contact_id: int):
    """
    The delete_contact function deletes a contact from the database.
        Args:
            db (Session): The database session to use for querying.
            contact_id (int): The id of the contact to delete.

    :param db: Session: Pass the database session to the function
    :param contact_id: int: Specify the id of the contact to be deleted
    :return: The contact that was deleted
    :doc-author: Trelent
    """
    db_contact = db.query(Contact)\
        .filter(Contact.id == contact_id).first()
    if db_contact:
        db.delete(db_contact)
        db.commit()
    return db_contact

def search_contacts(db: Session, query: str, user_id: int):
    """
    The search_contacts function searches the database for contacts that match a given query.
    The function takes in a database session, the search query, and an owner_id to filter by.
    It returns all contacts that match the search criteria.

    :param db: Session: Pass the database session to the function
    :param query: str: Filter the contacts by a search query
    :param user_id: int: Filter the contacts by owner_id
    :return: A list of contact objects
    :doc-author: Trelent
    """
    return db.query(Contact).filter(Contact.owner_id == user_id).filter(
        (Contact.first_name.contains(query)) |
        (Contact.last_name.contains(query)) |
        (Contact.email.contains(query))
    ).all()

def get_upcoming_birthdays(db: Session, user_id: int):
    """
    The get_upcoming_birthdays function returns a list of contacts whose birthdays are within the next week.

    :param db: Session: Pass the database session to the function
    :param user_id: int: Filter the contacts by owner_id
    :return: A list of contacts whose birthdays are in the next week
    :doc-author: Trelent
    """
    today = date.today()
    next_week = today + timedelta(days=7)
    return db.query(Contact).filter(Contact.owner_id == user_id).\
        filter(Contact.birthday.between(today, next_week)).all()