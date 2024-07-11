from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import firestore
from typing import Union
import starlette.status as status
import datetime


# define the app that will contain all of our routing for fast API
app = FastAPI()

# define a firestore client so we can interact with out database
firestore_db = firestore.Client()

# we need a request object to be able to talk to firebase for verifying user logins
firebase_request_adapter = requests.Request()

# define the static and template directories
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory="templates")


# function that we will use to retrieve and return the document that represents this user
# by using the ID of the firebase credentials. this function assumes that the credentials
# have been checked first
def getUser(user_token):
    # now that we have a user token, we are going to try and retrieve a user object for this user from firestore
    # if there is not a user object for this user, we will create one
    user = firestore_db.collection("users").document(user_token['user_id'])
    if not user.get().exists():
        user_data = {
            # our signup form doesn't have a name field so we will set a default that we will edit later
            'string': 'No name yet',
            'int': 0,
            'float': 3.14159,
            'boolean': True,
            'datetime': datetime.datetime.now(),
            'geo-point': firestore.GeoPoint(54.424, -2.0393),
            'array': [3,4,5,6],
            'map': {"first":"hello", "second":"world"},
        }
        firestore_db.collection("users").document(user_token['user_id']).set(user_data)

    # return the user document
    return user

# function that we will use to validate an id_token, we will return the user_token if valid, None if not
def validateFirebaseToken(id_token):
    # if we dont have a token, then return None
    if not id_token:
        return None
    
    # try to validate the token if this fails with an exception then this will remain as None so just return
    # at the end
    user_token = None
    try:
        user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
    except ValueError as err:
        # dump this message to the console as it will not be displayed on the template. use for debuggin
        # but if you are building for production you should handle this much more gracefully
        print(str(err))

    # return the token to the caller
    return user_token


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # query firebase for the request token. We also declare a bunch of other variables here as we still need them
    # for rendering the templates at the end. we have an error_message
    id_token = request.cookies.get("token")
    error_message = "No error here"
    user_token = None
    user = None
    
    # check if we have a valid firebase login if not, return the template with empty data as we will show the login box
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return templates.TemplateResponse('main.html', {'request': request, 'user_token': None, 'error_message': None, 'user_info': None})
    
    # get the user document and render the template
    user = getUser(user_token)
    return templates.TemplateResponse('main.html', {'request': request, 'user_token': user_token, 'error_message': error_message, 'user_info': user.get()})
