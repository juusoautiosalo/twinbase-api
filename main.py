# Run in bash: uvicorn main:app --reload

from datetime import datetime, timedelta
from typing import Union

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

import dtweb
import requests
import uuid

import os
from git import Repo
import shutil
import json


### vvvvvvvvv AUTHENTICATION SETUP vvvvvvvvvv ###
# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    print('Twinbase API WARNING: Secret key not set, everything might not work properly!')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
HASHED_PASSWORD = os.getenv('HASHED_PASSWORD')

if not HASHED_PASSWORD:
    print('Twinbase API WARNING: Password not set, authentication does not work!')


fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Twinbase API administrator",
        "email": "bot@twinbase.org",
        "hashed_password": HASHED_PASSWORD,
        "disabled": False,
    }
}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class User(BaseModel):
    username: str
    email: Union[str, None] = None
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

### ^^^^^^^^ AUTHENTICATION SETUP ^^^^^^^^^ ###



twinbase_repourl = "https://github.com/juusoautiosalo/twinbase-smart-city"
reponame = "juusoautiosalo/twinbase-smart-city"
baseurl = "https://juusoautiosalo.github.io/twinbase-smart-city"

# GitHub setup https://stackoverflow.com/questions/44784828/gitpython-git-authentication-using-user-and-password
username = "juusoautiosalo"
password = os.getenv('GITHUB_TOKEN')
if not password:
    print('Twinbase API WARNING: GitHub token not set. SSH may still work.')
remoteurl_https = f"https://{username}:{password}@github.com/{reponame}.git"
remoteurl_ssh = "git@github.com:" + reponame + ".git"
# print(remoteurl_ssh)


# Metadata for docs

description= f"""
This page describes an HTTP API for: [{reponame}]({baseurl})

You may send requests with the methods below.

"""


app = FastAPI(
    title = "Twinbase API",
    description=description,
    version="0.0.1",
    docs_url=None,
    redoc_url=None,
)

favicon_path = 'favicon.ico'

class Twin(BaseModel):
    dt_id: str = Field(alias='dt-id')
    hosting_iri: str = Field(alias='hosting-iri')
    name: str
    description: Union[str, None] = None
    local_id: str
    # price: float
    # is_offer: Union[bool, None] = None

"""
   Favicon endpoints
"""
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)

@app.get("/docs", include_in_schema=False)
def overridden_swagger():
	return get_swagger_ui_html(openapi_url="/openapi.json", title=app.title, swagger_favicon_url=favicon_path)

@app.get("/redoc", include_in_schema=False)
def overridden_redoc():
	return get_redoc_html(openapi_url="/openapi.json", title=app.title, redoc_favicon_url=favicon_path)


### vvvvvvvvv AUTHENTICATION FUNCTIONS AND ENDPOINTS vvvvvvvvvv ###
# from: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/#update-the-token-path-operation

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

### ^^^^^^^^ AUTHENTICATION FUNCTIONS AND ENDPOINTS ^^^^^^^^^ ###


@app.get("/")
def read_root():
    return {
        "This is a ": "Twinbase API",
        "See documentation in subfolder": "/docs"
    }


# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}

# @app.put("/items/{item_id}")
# def update_item(item_id: int, item: Item):
#     return {"item_name": item.name, "item_id": item_id}

# Twinbase API starts here

@app.get("/twins")
def read_twins():#(local_id: str):#, q: Union[str, None] = None):
    listurl = baseurl + "/" + '/index.json'
    # listurl = baseurl + "/" + local_id + '/index.json'
    # print(listurl)
    r = requests.get(listurl)
    twins = r.json()['twins']
    return twins

@app.get("/twins/{local_id}")
def read_twin(local_id: str):#, q: Union[str, None] = None):
    jsonUrl = baseurl + "/" + local_id + "/index.json"
    twin = requests.get(jsonUrl).json()
    # print(twin)
    return twin

@app.get("/twins/{local_id}/github")
def read_twin_github(local_id: str):#, q: Union[str, None] = None):
    jsonUrl = "https://raw.githubusercontent.com/" + reponame + "/main/docs/" + local_id + "/index.json"
    # print(jsonUrl)
    twin = requests.get(jsonUrl).json()
    # print(twin)
    return twin

@app.get("/twins/{local_id}/global")
def read_twin_global(local_id: str):#, q: Union[str, None] = None):
    dt_id = "https://dtid.org/" + local_id
    # print("DTID is:", dt_id)
    doc = dtweb.client.fetch_dt_doc(dt_id)
    # print(doc)
    return doc

@app.patch("/twins/{local_id}")
async def update_twin(local_id: str, patch: dict, current_user: User = Depends(get_current_active_user)):
    jsonUrl = baseurl + '/' + local_id + '/index.json'
    # print(jsonUrl)
    twin = requests.get(jsonUrl).json()
    twin.update(patch)
    # print(twin)

    tempdir = 'temporary_directory_for_twinbase_api'
    curdir = os.getcwd()
    parentdir = os.path.dirname(curdir)
    gitdir = os.path.join(parentdir, tempdir)

    try:
        repo = Repo.clone_from(url=remoteurl_https, to_path=gitdir)
    except:
        try:
            repo = Repo.clone_from(url=remoteurl_ssh, to_path=gitdir)
        except:
            repo = Repo(gitdir)
    # try:
    assert not repo.bare

    repo.config_writer().set_value("user", "name", current_user.full_name).release()
    repo.config_writer().set_value("user", "email", current_user.email).release()


    twindoc_filepath = gitdir + '/docs/' + local_id + '/index.json'
    with open(twindoc_filepath, 'w') as jsonfilew:
        json.dump(twin, jsonfilew, indent=4)

    with open(twindoc_filepath, 'r') as jsonfiler:
        print(json.load(jsonfiler))

    repo.index.add([twindoc_filepath])
    
    repo.index.commit("Update " + twin['name'])

    origin = repo.remote(name="origin")
    origin.push()

    shutil.rmtree(gitdir)
    return twin

@app.post("/twins/")
async def create_twin(twin: Twin, current_user: User = Depends(get_current_active_user)):
    twin.local_id = str(uuid.uuid4())
    # print(twin.local_id)
    twin.dt_id = "https://dtid.org/" + twin.local_id
    twin.hosting_iri = baseurl + "/" + twin.local_id

    # print('Changing to temporary directory')
    # print(os.getcwd())
    # os.chdir('..')
    tempdir = 'temporary_directory_for_twinbase_api'
    curdir = os.getcwd()
    parentdir = os.path.dirname(curdir)
    gitdir = os.path.join(parentdir, tempdir)
    # gitdir = '../' + tempdir
    # os.mkdir(tempdir)
    # os.chdir(tempdir)
    # print(os.getcwd())

    # repo = Repo(os.getcwd())
    # repo = Repo.base.Repo.clone_from(url=twinbase_repourl + '.git')
    # repo = Repo.clone_from(url=twinbase_repourl + '.git', to_path='.')

    try:
        repo = Repo.clone_from(url=remoteurl_https, to_path=gitdir)
    except:
        try:
            repo = Repo.clone_from(url=remoteurl_ssh, to_path=gitdir)
        except:
            repo = Repo(gitdir)
    # try:
    assert not repo.bare

    # https://stackoverflow.com/questions/50104496/gitpython-unable-to-set-the-git-config-username-and-email
    # repo.config_writer().set_value("user", "name", "twinbase-bot").release()
    # repo.config_writer().set_value("user", "email", "bot@twinbase.org").release()
    repo.config_writer().set_value("user", "name", current_user.full_name).release()
    repo.config_writer().set_value("user", "email", current_user.email).release()
    # reader = repo.config_reader()
    # field = reader.get_value("user","email")

    twindoc_filepath = gitdir + '/docs/' + twin.local_id + '/index.json'
    os.mkdir(gitdir + '/docs/' + twin.local_id)
    twindict = dict(twin)
    twindict['dt-id'] = twindict.pop('dt_id')
    twindict['hosting-iri'] = twindict.pop('hosting_iri')
    with open(twindoc_filepath, 'w+') as jsonfilew:
        json.dump(twindict, jsonfilew, indent=4)

    with open(twindoc_filepath, 'r') as jsonfiler:
        print(json.load(jsonfiler))

    # print(repo.git.status())
    repo.index.add([twindoc_filepath])
    # print(repo.git.status())
    
    repo.index.commit("Initialize " + twin.name)
    # print(repo.git.status())
    origin = repo.remote(name="origin")
    origin.push()
    # print('\n\nLast status:')
    # print(repo.git.status())
    # except:
    #     shutil.rmtree(gitdir)
    #     return



    # print('Changing back to normal directory')
    # print(os.getcwd())
    # os.chdir('..')
    # os.chdir('twinbase-api')
    # print(os.getcwd())


    shutil.rmtree(gitdir)
    return twin


@app.delete("/twins/{local_id}")
async def delete_twin(local_id: str, current_user: User = Depends(get_current_active_user)):
    jsonUrl = baseurl + '/' + local_id + '/index.json'
    # print(jsonUrl)
    twin = requests.get(jsonUrl).json()

    tempdir = 'temporary_directory_for_twinbase_api'
    curdir = os.getcwd()
    parentdir = os.path.dirname(curdir)
    gitdir = os.path.join(parentdir, tempdir)

    try:
        repo = Repo.clone_from(url=remoteurl_https, to_path=gitdir)
    except:
        try:
            repo = Repo.clone_from(url=remoteurl_ssh, to_path=gitdir)
        except:
            repo = Repo(gitdir)
    # try:
    assert not repo.bare

    repo.config_writer().set_value("user", "name", current_user.full_name).release()
    repo.config_writer().set_value("user", "email", current_user.email).release()


    twindir = gitdir + '/docs/' + local_id
    shutil.rmtree(twindir)

    repo.git.add(all=True)

    repo.index.commit("Delete " + twin['name'])


    origin = repo.remote(name="origin")
    origin.push()

    shutil.rmtree(gitdir)
    return "Removed " + twin['name']
