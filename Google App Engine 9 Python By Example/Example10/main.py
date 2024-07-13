from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import firestore, storage
from google.cloud.firestore_v1.base_query import FieldFilter
from typing import Union
import starlette.status as status
import datetime
import local_constants

# define the app that will contain all of our routing for fast API
app = FastAPI()

# define a firestore client so we can interact with out database
firestore_db = firestore.Client()

# we need a request object to be able to talk to firebase for verifying user logins
firebase_request_adapter = requests.Request()

# define the static and template directories
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory="templates")


# function tha will add an empty directory to our storage  bucket. Note that the passed in directory name must have
# a trailing slash attached to it otherwise this will store as a file
def addDirectory(directory_name):
    # get access to a storage client then list the bucket we need to use using the project and the bucket name
    # from the local constants
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)

    # make an empty blob out the directory name and upload it to the bucket. this is the conventio GCS uses
    # to distinguish between file and directories
    blob = bucket.blob(directory_name)
    blob.upload_from_string('', content_type='application/x-www-form-urlencoded;charset=UTF-8')


# function that will add a file to the storage bucket
def addFile(file):
    # get access to a storage client then list the bucket we need to use using the project and the bucket name
    # from the local constants
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)

    # create the blob to be stored then upload the content from the source file
    blob = storage.Blob(file.filename, bucket)
    blob.upload_from_file(file.file)


# function that will return the list of blobs in the bucket
def blobList(prefix):
    # get access to a storage client then list the bucket we need to use using the project and the bucket name
    # from the local constants
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)

    # get the list of blobs and return it
    return storage_client.list_blobs(local_constants.PROJECT_STORAGE_BUCKET, prefix=prefix)

# function that will get the contents of a blob and will return it to the caller for downloading
def downloadBlob(filename):
    # get access to a storage client then list the bucket we need to use using the project and the bucket name
    # from the local constants
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)

    # get access to the blob name and then download it to disk
    blob = bucket.get_blob(filename)
    return blob.download_as_bytes()


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
    
    # the list of files and directories that we have in storage
    file_list = []
    directory_list = []

    # get the list of blobs and sort them based on directory and files
    blobs = blobList(None)
    for blob in blobs:
        if blob.name[-1] == '/':
            directory_list.append(blob)
        else:
            file_list.append(blob)

    # get the user document and render the template. we will need to pull the address objects as well
    # you can use get_all as well, but it will not guarantee order. If order does not matter then use get_all
    user = getUser(user_token).get()
    return templates.TemplateResponse('main.html', {'request': request, 'user_token': user_token, 'error_message':error_message, 'user_info':user, 'file_list': file_list, 'directory_list':directory_list})

# handler that will take in a string representing a directory and will create it in the bucket
@app.post("/add-directory", response_class=RedirectResponse)
async def addDirectoryHandler(request: Request):
    # there should be a toke. Validate it and if invalid, redirect back to / as a basic security measure
    id_token = request.cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse("/")
    
    # do a couple of basic checks. if the string is zero length or does not end in a / then reject it
    form = await request.form()
    dir_name = form['dir_name']
    if dir_name == '' or dir_name[-1] != '/':
        return RedirectResponse("/")
    
    # create the directory in the bucket and then redirect
    addDirectory(dir_name)
    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

# handler that will take in a filename to dowload and will serve it to the user
@app.post("/download-file", response_class=Response)
async def downloadFileHandler(request: Request):
    # there should be a toke. Validate it and if invalid, redirect back to / as a basic security measure
    id_token = request.cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse("/")
    
    # pull the file name and see what filename we have for download
    form = await request.form()
    filename = form['filename']
    return Response(downloadBlob(filename))

# handler that will upload a file to the bucket. this will store it in the root of the bucket
@app.post("/upload-file", response_class=RedirectResponse)
async def uploadFileHandler(request: Request):
    # there should be a toke. Validate it and if invalid, redirect back to / as a basic security measure
    id_token = request.cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse("/")
    
    # if the file name is empty, the redirect to / and do nothing
    form = await request.form()
    if form['file_name'].filename == "":
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    
    # redirect back after the directory is added
    addFile(form['file_name'])
    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)