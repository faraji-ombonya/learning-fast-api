from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import firestore
import starlette.status as status

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
            'name': 'No name yet',
            'age': 0,
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

# add in a second route to show us a form for updating the name and the age of the user
@app.get("/update-user", response_class=HTMLResponse)
async def updateForm(request: Request):
    # there should be a token here
    id_token = request.cookies.get("token")

    # validate the token. if its not valid, then redirect to / as a basic security measure as a non logged in user
    # should not be accessing this
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse("/")
    
    # get the user document and send it to the template that will show a basic form for changing this data
    user = getUser(user_token)
    return templates.TemplateResponse('update.html', {'request':request, 'user_token': user_token, 'error_message': None, 'user_info':user.get()})

# this is another version of update user but this will accept a post request and will only redirect when finished
@app.post("/update-user", response_class=RedirectResponse)
async def updateFormPost(request: Request):
    # There should be a token. Validate it and if invalid then redirect back to / as basic security measure
    id_token = request.cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse("/")
    
    # pull the user document and then we will modify the name and age and update it
    user = getUser(user_token)
    form = await request.form()
    user.update({"name": form['name'], "age": int(form['age'])})
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)
