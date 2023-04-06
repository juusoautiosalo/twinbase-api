# Run in bash: uvicorn main:app --reload
# Run in localhost: uvicorn main:app --reload --host localhost

from typing import Union

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from pydantic import BaseModel, Field

import dtweb
import requests
import uuid
import pprint

import os
from git import Repo
import shutil
import json
import iaa

twinbase_repourl = "https://github.com/juusoautiosalo/twinbase-smart-city"
reponame = "juusoautiosalo/twinbase-smart-city"
baseurl = "https://juusoautiosalo.github.io/twinbase-smart-city"

# GitHub setup https://stackoverflow.com/questions/44784828/gitpython-git-authentication-using-user-and-password
username = "juusoautiosalo"
password = os.getenv("GITHUB_TOKEN")
if not password:
    print("Twinbase API WARNING: GitHub token not set. SSH may still work.")
remoteurl_https = f"https://{username}:{password}@github.com/{reponame}.git"
remoteurl_ssh = "git@github.com:" + reponame + ".git"


# Metadata for docs

description = f"""
This page describes an HTTP API for: [{reponame}]({baseurl})

You may send requests with the methods below.

"""


app = FastAPI(
    title="Twinbase API with SSI auth",
    description=description,
    version="0.0.1",
    docs_url=None,
    redoc_url=None,
)


class Twin(BaseModel):
    dt_id: str = Field(alias="dt-id")
    hosting_iri: str = Field(alias="hosting-iri")
    name: str
    description: str | None = None
    local_id: str


# Helper functions

# def check_location_filters(doc, restr)

# Favicon endpoints

favicon_path = "favicon.ico"


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)


@app.get("/docs", include_in_schema=False)
def overridden_swagger():
    return get_swagger_ui_html(
        openapi_url="/openapi.json", title=app.title, swagger_favicon_url=favicon_path
    )


@app.get("/redoc", include_in_schema=False)
def overridden_redoc():
    return get_redoc_html(
        openapi_url="/openapi.json", title=app.title, redoc_favicon_url=favicon_path
    )


# Twinbase API starts here


@app.get("/")
def read_root():
    return {"This is a ": "Twinbase API", "See documentation in subfolder": "/docs"}


@app.get("/update")
def update():
    listurl = baseurl + "/" + "/index.json"
    r = requests.get(listurl)
    twins = r.json()["twins"]
    for twin in twins:
        print("\nChecking " + twin["name"])
        # pprint.pprint(twin)
        try:
            doc = dtweb.client.fetch_dt_doc(twin["dt-id"])
        except:
            print(
                "This twin is not working properly. Probably the DTID is not working."
            )
            pass
        filters = iaa.get_location_filters_for(doc)
        iaa.configure(twin, filters)

    return {"detail": "Update is not working yet :)"}


@app.get("/twins")
def read_twins():
    listurl = baseurl + "/" + "/index.json"
    r = requests.get(listurl)
    twins = r.json()["twins"]
    return twins


@app.get("/twins/{local_id}")
def read_twin(local_id: str):
    jsonUrl = baseurl + "/" + local_id + "/index.json"
    r = requests.get(jsonUrl)
    if r.status_code == 200:
        twin = r.json()
    else:
        return {"detail": "error", "status-code": r.status_code}
    return twin


@app.get("/twins/{local_id}/github")
def read_twin_github(local_id: str):
    jsonUrl = (
        "https://raw.githubusercontent.com/"
        + reponame
        + "/main/docs/"
        + local_id
        + "/index.json"
    )
    twin = requests.get(jsonUrl).json()
    return twin


@app.get("/twins/{local_id}/global")
def read_twin_global(local_id: str):
    dt_id = "https://dtid.org/" + local_id
    doc = dtweb.client.fetch_dt_doc(dt_id)
    return doc


@app.patch("/twins/{local_id}")
def update_twin(local_id: str, patch: dict):
    jsonUrl = baseurl + "/" + local_id + "/index.json"
    r = requests.get(jsonUrl)
    if r.status_code == 200:
        twin = r.json()
    else:
        return {"detail": "twin not found", "status-code": r.status_code}
    twin.update(patch)

    tempdir = "temporary_directory_for_twinbase_api"
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
    assert not repo.bare

    repo.config_writer().set_value("user", "name", "Juuso Autiosalo").release()
    repo.config_writer().set_value("user", "email", "juuso.autiosalo@iki.fi").release()

    twindoc_filepath = gitdir + "/docs/" + local_id + "/index.json"
    with open(twindoc_filepath, "w") as jsonfilew:
        json.dump(twin, jsonfilew, indent=4)

    with open(twindoc_filepath, "r") as jsonfiler:
        print(json.load(jsonfiler))

    repo.index.add([twindoc_filepath])

    repo.index.commit("Update " + twin["name"])

    origin = repo.remote(name="origin")
    origin.push()

    shutil.rmtree(gitdir)
    return twin


@app.post("/twins/")
def create_twin(twin: Twin):
    twin.local_id = str(uuid.uuid4())
    twin.dt_id = "https://dtid.org/" + twin.local_id
    twin.hosting_iri = baseurl + "/" + twin.local_id
    tempdir = "temporary_directory_for_twinbase_api"
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
    assert not repo.bare

    # https://stackoverflow.com/questions/50104496/gitpython-unable-to-set-the-git-config-username-and-email
    repo.config_writer().set_value("user", "name", "twinbase-bot").release()
    repo.config_writer().set_value("user", "email", "bot@twinbase.org").release()

    twindoc_filepath = gitdir + "/docs/" + twin.local_id + "/index.json"
    os.mkdir(gitdir + "/docs/" + twin.local_id)
    twindict = dict(twin)
    twindict["dt-id"] = twindict.pop("dt_id")
    twindict["hosting-iri"] = twindict.pop("hosting_iri")
    with open(twindoc_filepath, "w+") as jsonfilew:
        json.dump(twindict, jsonfilew, indent=4)

    with open(twindoc_filepath, "r") as jsonfiler:
        print(json.load(jsonfiler))

    repo.index.add([twindoc_filepath])
    repo.index.commit("Initialize " + twin.name)
    origin = repo.remote(name="origin")
    origin.push()

    shutil.rmtree(gitdir)
    return twin


@app.delete("/twins/{local_id}")
def delete_twin(local_id: str):
    jsonUrl = baseurl + "/" + local_id + "/index.json"
    r = requests.get(jsonUrl)
    if r.status_code == 200:
        twin = r.json()
    else:
        return {"detail": "twin not found", "status-code": r.status_code}

    tempdir = "temporary_directory_for_twinbase_api"
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
    assert not repo.bare

    repo.config_writer().set_value("user", "name", "twinbase-bot").release()
    repo.config_writer().set_value("user", "email", "bot@twinbase.org").release()

    twindir = gitdir + "/docs/" + local_id
    try:
        shutil.rmtree(twindir)
    except FileNotFoundError:
        return {"detail": "twin not found, probably recently deleted"}

    repo.git.add(all=True)

    repo.index.commit("Delete " + twin["name"])

    origin = repo.remote(name="origin")
    origin.push()

    shutil.rmtree(gitdir)
    return "Removed " + twin["name"]


# Update conf file at startup
update()
