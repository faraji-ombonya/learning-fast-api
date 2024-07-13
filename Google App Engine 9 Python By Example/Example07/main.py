from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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
            # for now, we will use a place holder name as this is not our focus, but we will start with an empty array for our addresses
            'name': 'John Doe',
            'address_list': [],
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
    # query firebase for the request token. We also declare a bunch of other variables here as we will need them
    # for rendering the template at the end
    id_token = request.cookies.get("token")
    error_message = "No error here"
    user_token = None
    user = None

    # check if we have a valid login, if not, return the template with empty data as we will shoe the login box
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return templates.TemplateResponse('main.html', {'request': request, 'user_token': None, 'error_message': None, 'user': None})
    
    # get the user document and render the template. we will need to pull the address objects as well
    # you can use get_all as well, but it will not guarantee order. If order does not matter then use get_all
    user = getUser(user_token).get()
    addresses = user.get('address_list')
    return templates.TemplateResponse('main.html', {'request': request, 'user_token': user_token, 'error_message':error_message, 'user_info':user, 'address_list': addresses})


# route that will take in an address form and will add it to the firestore and link it to a user
@app.post("/add-address", response_class=RedirectResponse)
async def addAddresses(request: Request):
    # there should be a toke. Validate it and if invalid, redirect back to / as a basic security measure
    id_token = request.cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse("/")
    
    # pull the form containing our data
    form = await request.form()

    # create a dictionary object that will represent our address as a map we will add to the user
    address = {
        'address1': form['address1'],
        'address2': form['address2'],
        'address3': form['address3'],
        'address4': form['address4'],
    }

    # add the address to our current user
    user = getUser(user_token)
    addresses = user.get().get('address_list')
    addresses.append(address)
    user.update({'address_list': addresses})

    # when finished, return a redirect with a 302 to force a GET verb
    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)


@app.post("/delete-address", response_class=RedirectResponse)
async def deleteAddresses(request: Request):
    # there should be a toke. Validate it and if invalid, redirect back to / as a basic security measure
    id_token = request.cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse("/")
    
    # pull the index from our form
    form = await request.form()
    index = int(form['index'])

    # pull the list of address objects from the user, delete the requested index and update the user
    user = getUser(user_token)
    addresses = user.get().get('address_list')
    del addresses[int(index)]
    data = {
        'address_list': addresses,
    }
    user.update(data)

    # when finished return a redirect with a 302 verb to force a get verb
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)
