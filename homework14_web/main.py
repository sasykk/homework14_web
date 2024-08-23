import crud
import schemas
import cloudinary
from config import config
import cloudinary.uploader
from slowapi import Limiter
from sqlalchemy.orm import Session
from auth import router as auth_router
from database import engine, Base, get_db
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, status

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()

app.add_middleware(SlowAPIMiddleware)

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cloudinary.config(
  cloud_name=config.CLOUDINARY_CLOUD_NAME,
  api_key=config.CLOUDINARY_API_KEY,
  api_secret=config.CLOUDINARY_API_SECRET
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

app.include_router(auth_router, prefix="/auth", tags=["auth"])

@app.post("/upload-avatar/", response_model=schemas.User)
def upload_avatar(file: UploadFile, db: Session = Depends(get_db),
                  current_user: schemas.User = Depends(crud.get_current_active_user)):
    """
    The upload_avatar function uploads a user's avatar to the cloudinary server.
    It takes in an UploadFile object, which is a file that has been uploaded by the client.
    The function then uses Cloudinary's Python SDK to upload the image and return its URL.
    Finally, it updates the current_user with their new avatar URL.

    :param file: UploadFile: Get the file from the request
    :param db: Session: Access the database
    :param current_user: schemas.User: Get the current user from the database
    :return: The current user
    :doc-author: Trelent
    """
    result = cloudinary.uploader.upload(file.file, folder="avatars/")
    current_user.avatar_url = result["secure_url"]
    db.commit()
    return current_user

@app.post("/contacts/", response_model=schemas.Contact)
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db),
                   current_user: schemas.User = Depends(crud.get_current_active_user)):
    """
    The create_contact function creates a new contact in the database.

    :param contact: schemas.ContactCreate: Pass the contact data to the create_contact function
    :param db: Session: Pass the database session to the function
    :param current_user: schemas.User: Get the current user's id
    :return: A contact object
    :doc-author: Trelent
    """
    return crud.create_contact(db=db, contact=contact, user_id=current_user.id)

@app.get("/contacts/", response_model=list[schemas.Contact])
def read_contacts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db),
                  current_user: schemas.User = Depends(crud.get_current_active_user)):

    """
    The read_contacts function returns a list of contacts.

    :param skip: int: Skip the first n contacts
    :param limit: int: Limit the number of contacts returned
    :param db: Session: Pass the database session to the function
    :param current_user: schemas.User: Get the current user's id
    :return: A list of contacts (schemas
    :doc-author: Trelent
    """
    return crud.get_contacts(db, skip=skip, limit=limit, user_id=current_user.id)

@app.get("/contacts/{contact_id}", response_model=schemas.Contact)
def read_contact(contact_id: int, db: Session = Depends(get_db),
                 current_user: schemas.User = Depends(crud.get_current_active_user)):
    """
    The read_contact function is a helper function that will be used by the read_contact endpoint.
    It takes in an integer contact_id and returns the corresponding Contact object from the database.
    If no such contact exists, it raises a 404 error.

    :param contact_id: int: Specify the contact id
    :param db: Session: Pass the database session to the function
    :param current_user: schemas.User: Get the current user
    :return: A contact object, which is a pydantic model
    :doc-author: Trelent
    """
    db_contact = crud.get_contact(db, contact_id=contact_id)
    if db_contact is None or db_contact.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@app.put("/contacts/{contact_id}", response_model=schemas.Contact)
def update_contact(contact_id: int, contact: schemas.ContactUpdate,
                   db: Session = Depends(get_db), current_user: schemas.User = Depends(crud.get_current_active_user)):
    """
    The update_contact function takes in a contact_id and a ContactUpdate object,
    and returns the updated contact. The function first checks if the user is authorized to update this contact,
    by checking if they are the owner of it. If not, an HTTPException is raised with status code 404 (Not Found).
    If so, then crud.update_contact() is called.

    :param contact_id: int: Specify the contact to update
    :param contact: schemas.ContactUpdate: Pass the contact data to be updated
    :param db: Session: Pass the database session to the function
    :param current_user: schemas.User: Get the current user
    :return: The updated contact
    :doc-author: Trelent
    """
    db_contact = crud.get_contact(db, contact_id=contact_id)
    if db_contact is None or db_contact.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return crud.update_contact(db=db, contact_id=contact_id, contact=contact)

@app.delete("/contacts/{contact_id}", response_model=schemas.Contact)
def delete_contact(contact_id: int, db: Session = Depends(get_db),
                   current_user: schemas.User = Depends(crud.get_current_active_user)):
    """
    The delete_contact function deletes a contact from the database.
        It takes in an integer representing the id of the contact to be deleted,
        and returns a Contact object that was just deleted.

    :param contact_id: int: Specify the contact to be deleted
    :param db: Session: Pass in the database session
    :param current_user: schemas.User: Get the current user
    :return: A contact object
    :doc-author: Trelent
    """
    db_contact = crud.delete_contact(db, contact_id=contact_id)
    if db_contact is None or db_contact.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@app.get("/contacts/search/", response_model=list[schemas.Contact])
def search_contacts(query: str, db: Session = Depends(get_db),
                    current_user: schemas.User = Depends(crud.get_current_active_user)):
    """
    The search_contacts function searches for contacts in the database.
        It takes a query string and returns all contacts that match the query.
        The search is case insensitive.

    :param query: str: Specify the query string
    :param db: Session: Pass the database session to the function
    :param current_user: schemas.User: Get the current user's id
    :return: A list of contacts
    :doc-author: Trelent
    """
    return crud.search_contacts(db, query=query, user_id=current_user.id)

@app.get("/contacts/upcoming_birthdays/", response_model=list[schemas.Contact])
def get_upcoming_birthdays(db: Session = Depends(get_db),
                           current_user: schemas.User = Depends(crud.get_current_active_user)):
    """
    The get_upcoming_birthdays function returns a list of all the birthdays that are coming up in the next 30 days.
    The function takes two parameters: db and current_user. The db parameter is used to connect to the database, while
    the current_user parameter is used to get information about who's currently logged in.

    :param db: Session: Access the database
    :param current_user: schemas.User: Get the current user's id
    :return: A list of the upcoming birthdays for a user
    :doc-author: Trelent
    """
    return crud.get_upcoming_birthdays(db, user_id=current_user.id)