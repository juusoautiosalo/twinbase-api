# Run in bash: uvicorn main:app --reload

from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel, Field

import dtweb
import requests
import uuid

import os
from git import Repo
import shutil
import json


twinbase_repourl = "https://github.com/juusoautiosalo/twinbase-smart-city"
reponame = "juusoautiosalo/twinbase-smart-city"
baseurl = "https://juusoautiosalo.github.io/twinbase-smart-city"

# GitHub setup https://stackoverflow.com/questions/44784828/gitpython-git-authentication-using-user-and-password
username = "juusoautiosalo"
password = os.getenv('GITHUB_TOKEN')
remoteurl = f"https://{username}:{password}@github.com/{reponame}.git"
# print(remoteurl)

app = FastAPI()

class Twin(BaseModel):
    dt_id: str = Field(alias='dt-id')
    hosting_iri: str = Field(alias='hosting-iri')
    name: str
    description: str | None = None
    local_id: str
    # price: float
    # is_offer: Union[bool, None] = None

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
def update_twin(local_id: str, patch: dict):
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
        repo = Repo.clone_from(url=remoteurl, to_path=gitdir)
    except:
        repo = Repo(gitdir)
    # try:
    assert not repo.bare

    repo.config_writer().set_value("user", "name", "Juuso Autiosalo").release()
    repo.config_writer().set_value("user", "email", "juuso.autiosalo@iki.fi").release()


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
def create_twin(twin: Twin):
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
        repo = Repo.clone_from(url=remoteurl, to_path=gitdir)
    except:
        repo = Repo(gitdir)
    # try:
    assert not repo.bare

    # https://stackoverflow.com/questions/50104496/gitpython-unable-to-set-the-git-config-username-and-email
    # repo.config_writer().set_value("user", "name", "twinbase-bot").release()
    # repo.config_writer().set_value("user", "email", "bot@twinbase.org").release()
    repo.config_writer().set_value("user", "name", "Juuso Autiosalo").release()
    repo.config_writer().set_value("user", "email", "juuso.autiosalo@iki.fi").release()
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
def delete_twin(local_id: str):
    jsonUrl = baseurl + '/' + local_id + '/index.json'
    # print(jsonUrl)
    twin = requests.get(jsonUrl).json()

    tempdir = 'temporary_directory_for_twinbase_api'
    curdir = os.getcwd()
    parentdir = os.path.dirname(curdir)
    gitdir = os.path.join(parentdir, tempdir)

    try:
        repo = Repo.clone_from(url=remoteurl, to_path=gitdir)
    except:
        repo = Repo(gitdir)
    # try:
    assert not repo.bare

    repo.config_writer().set_value("user", "name", "Juuso Autiosalo").release()
    repo.config_writer().set_value("user", "email", "juuso.autiosalo@iki.fi").release()


    twindir = gitdir + '/docs/' + local_id
    shutil.rmtree(twindir)

    repo.git.add(all=True)

    repo.index.commit("Delete " + twin['name'])


    origin = repo.remote(name="origin")
    origin.push()

    shutil.rmtree(gitdir)
    return "Removed " + twin['name']
