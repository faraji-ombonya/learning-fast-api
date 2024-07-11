from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# define the app that will contain all of our routing for Fast API
app = FastAPI()

# define the static and templates directories
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse('main.html', {'request': request, 'name':'John Doe', 'number':'1234567' })
