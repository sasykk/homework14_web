import os
import crud
import schemas
from jose import jwt
from database import get_db
from datetime import timedelta
from sqlalchemy.orm import Session
from utils import send_verification_email
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

router = APIRouter()

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """
    The login_for_access_token function is a ReST endpoint that accepts POST requests with the following JSON body:
    {
        &quot;username&quot;: string,
        &quot;password&quot;: string,
    }

    :param db: Session: Get the database session
    :param form_data: OAuth2PasswordRequestForm: Get the username and password from the request body
    :return: A json response with the access token
    :doc-author: Trelent
    """
    user = crud.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=crud.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = crud.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=schemas.User)
async def register_user(user: schemas.UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    The register_user function creates a new user in the database.
    It takes a UserCreate object as input, which is validated by Pydantic.
    If the email address already exists in the database, it raises an HTTPException with status code 409 (Conflict).
    Otherwise, it creates a new user and returns that user's information.

    :param user: schemas.UserCreate: Pass in the user data from the request body
    :param background_tasks: BackgroundTasks: Add a task to the background queue
    :param db: Session: Get a database session
    :return: A user object, which is defined in the schemas
    :doc-author: Trelent
    """
    db_user = crud.get_user(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=409, detail="Email already registered")
    new_user = crud.create_user(db=db, user=user)
    token = crud.create_access_token(data={"sub": new_user.email})
    await send_verification_email(new_user.email, token)
    return new_user


@router.get("/verify")
def verify_email(token: str, db: Session = Depends(get_db)):
    """
    The verify_email function is used to verify a user's email address.
    It takes in the token that was sent to the user's email and decodes it using JWT.
    If the token is valid, then we set the user's account as active.

    :param token: str: Pass the token to the function
    :param db: Session: Get the database session from the dependency
    :return: A message saying that the email has been verified successfully
    :doc-author: Trelent
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[crud.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
    user = crud.get_user(db, email=email)
    if user is None:
        raise credentials_exception
    user.is_active = True
    db.commit()
    return {"msg": "Email verified successfully"}