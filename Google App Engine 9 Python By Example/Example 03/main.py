from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token
from google.auth.transport import requests

# define the app that will contain all of our routing for FastAPI
app = FastAPI()

# we need a request object to be able to talk to firebase for verifying user logins
firebase_request_adapter = requests.Request()

# define the static and template directories
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # Query firebase for the request token. We also declare a bunch of other variables here as we will need them
    # for rendering the templates at the end. We have an error_message there incase you want to output an error to
    # the user in the template
    id_token = request.cookies.get("token")
    error_message = "No error here"
    user_token = None

    # if we have an id_token, we will verify it against firebase. If it does not checkout then log the error message that is returned
    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        except ValueError as err:
            # dump this message to console as it will not be displayed on the template. use for debugging, if you are building for
            # production you should handle this much more gracefully
            print(str(err))
    return templates.TemplateResponse("main.html", {"request": request, "user_token":user_token, "error_message":error_message })
