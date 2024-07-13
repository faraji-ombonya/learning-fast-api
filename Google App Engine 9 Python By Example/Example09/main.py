from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
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
            # we wont use this, but just to ensure some data in our user document
            'name': 'John Doe',
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
    dummy_data = firestore_db.collection("dummy-data").stream()
    return templates.TemplateResponse('main.html', {'request': request, 'user_token': user_token, 'error_message':error_message, 'user_info':user, 'dummy_data': dummy_data})

# route that will add four objects to the firestore by using a batch request. the idea is to add the in a single
# rather than for individual objects
@app.post("/initialise", response_class=RedirectResponse)
async def batchAdd(request: Request):
    # there should be a toke. Validate it and if invalid, redirect back to / as a basic security measure
    id_token = request.cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse("/")
    
    
    # create dictionaries for four objects to add into the firestore
    batch1 = {"number": 1, "name":"first"}
    batch2 = {"number": 2, "name":"second"}
    batch3 = {"number": 3, "name":"third"}
    batch4 = {"number": 4, "name":"fourth"}
    batch5 = {"number": 5, "name":"first"}
    batch6 = {"number": 6, "name":"second"}
    batch7 = {"number": 7, "name":"third"}
    batch8 = {"number": 8, "name":"fourth"}
    batch9 = {"number": 9, "name":"first"}
    batch10 = {"number": 10, "name":"second"}
    batch11 = {"number": 11, "name":"third"}
    batch12 = {"number": 12, "name":"fourth"}

    # get a batch object and add the objects
    batch = firestore_db.batch()
    batch.set(firestore_db.collection('dummy-data').document('1'), batch1)
    batch.set(firestore_db.collection('dummy-data').document('2'), batch2)
    batch.set(firestore_db.collection('dummy-data').document('3'), batch3)
    batch.set(firestore_db.collection('dummy-data').document('4'), batch4)
    batch.set(firestore_db.collection('dummy-data').document('1'), batch5)
    batch.set(firestore_db.collection('dummy-data').document('2'), batch6)
    batch.set(firestore_db.collection('dummy-data').document('3'), batch7)
    batch.set(firestore_db.collection('dummy-data').document('4'), batch8)
    batch.set(firestore_db.collection('dummy-data').document('1'), batch9)
    batch.set(firestore_db.collection('dummy-data').document('2'), batch10)
    batch.set(firestore_db.collection('dummy-data').document('3'), batch11)
    batch.set(firestore_db.collection('dummy-data').document('4'), batch12)

    # commit the batch and it should be added to the firestore
    batch.commit()

    # when finished, redirect with a 302 to force a GET request back to /
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)


# route that will filter by a number and return display the list of objects that satisfy
@app.post('/filter-by-number', response_class=HTMLResponse)
async def filterByNumber(request: Request):
    # there should be a toke. Validate it and if invalid, redirect back to / as a basic security measure
    id_token = request.cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse("/")
    
    # pull the number from the form
    form = await request.token()
    num = int(form['num'])

    # get a reference to the collection and then make a query
    dummy_data_ref = firestore_db.collection('dummy-data')
    query = dummy_data_ref.where(filter=FieldFilter('number', '>=', int(num)))

    # return the template with the filtered data
    user = getUser(user_token).get()
    return templates.TemplateResponse('main.html', {'request':request, 'user_token':user_token, 'error_message':'no error here', 'user_info':user, 'dummy_data':query.stream()})


# route that will filter by two numbers and return display the list of objects that satisfy
@app.post('/filter-by-ranger', response_class=HTMLResponse)
async def filterByRange(request: Request):
    # there should be a toke. Validate it and if invalid, redirect back to / as a basic security measure
    id_token = request.cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse("/")
    
    # pull the number from the form
    form = await request.token()
    low = int(form['low'])
    high = int(form['high'])


    # get a reference to the collection and then make a query
    dummy_data_ref = firestore_db.collection('dummy-data')
    query = dummy_data_ref.where(filter=FieldFilter('number', '>=', int(low))).where(filter=FieldFilter('number', '<=', int(high)))

    # return the template with the filtered data
    user = getUser(user_token).get()
    return templates.TemplateResponse('main.html', {'request':request, 'user_token':user_token, 'error_message':'no error here', 'user_info':user, 'dummy_data':query.stream()})



# route that will filter by two strings and return display the list of objects that satisfy
# this will pick out all the objects with a name starting with the letter f
@app.post('/filter-by-string', response_class=HTMLResponse)
async def filterByString(request: Request):
    # there should be a toke. Validate it and if invalid, redirect back to / as a basic security measure
    id_token = request.cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse("/")
    
    # get a reference to the collection and then make a query
    dummy_data_ref = firestore_db.collection('dummy-data')
    query = dummy_data_ref.where(filter=FieldFilter('number', '>=', 'f')).where(filter=FieldFilter('number', '<', 'g'))

    # return the template with the filtered data
    user = getUser(user_token).get()
    return templates.TemplateResponse('main.html', {'request':request, 'user_token':user_token, 'error_message':'no error here', 'user_info':user, 'dummy_data':query.stream()})



# route that will filter by a name and a number and return display the list of objects that satisfy
# note, this will return an index to be built
@app.post('/filter-by-both', response_class=HTMLResponse)
async def filterByString(request: Request):
    # there should be a toke. Validate it and if invalid, redirect back to / as a basic security measure
    id_token = request.cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse("/")
    
    # pull the number from the form
    form = await request.token()
    num = int(form['num'])
    textinput = form['textinput']
    
    # get a reference to the collection and then make a query
    dummy_data_ref = firestore_db.collection('dummy-data')
    query = dummy_data_ref.where(filter=FieldFilter('number', '>=', int(num))).where(filter=FieldFilter('number', '==', textinput))

    # return the template with the filtered data
    user = getUser(user_token).get()
    return templates.TemplateResponse('main.html', {'request':request, 'user_token':user_token, 'error_message':'no error here', 'user_info':user, 'dummy_data':query.stream()})
