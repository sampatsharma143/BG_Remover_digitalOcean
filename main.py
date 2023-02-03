import imp
from fastapi import FastAPI, Depends, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from asyncer import asyncify
from starlette.responses import Response
import pathlib
import sys
import time
from enum import Enum
from typing import IO, cast
import filetype
import aiohttp

from rembg import remove

from rembg.session_base import BaseSession
from rembg.session_factory import new_session

app = FastAPI()
sessions: dict[str, BaseSession] = {}

origins = [
    "http://localhost",
    "http://localhost:8080",
    "157.245.96.101",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class ModelType(str, Enum):
    u2net = "u2net"
    u2netp = "u2netp"
    u2net_human_seg = "u2net_human_seg"
    u2net_cloth_seg = "u2net_cloth_seg"
    
class CommonQueryPostParams:
    def __init__(
        self,
        model: ModelType = Form(
            default=ModelType.u2net,
            description="Model to use when processing image",
        ),
        a: bool = Form(default=False, description="Enable Alpha Matting"),
        af: int = Form(
            default=240,
            ge=0,
            le=255,
            description="Alpha Matting (Foreground Threshold)",
        ),
        ab: int = Form(
            default=10,
            ge=0,
            le=255,
            description="Alpha Matting (Background Threshold)",
        ),
        ae: int = Form(
            default=10, ge=0, description="Alpha Matting (Erode Structure Size)"
        ),
        om: bool = Form(default=False, description="Only Mask"),
        ppm: bool = Form(default=False, description="Post Process Mask"),
    ):
        self.model = model
        self.a = a
        self.af = af
        self.ab = ab
        self.ae = ae
        self.om = om
        self.ppm = ppm


class CommonQueryParams:
    def __init__(
        self,
        model: ModelType = Query(
            default=ModelType.u2net,
            description="Model to use when processing image",
        ),
        a: bool = Query(default=False, description="Enable Alpha Matting"),
        af: int = Query(
            default=240,
            ge=0,
            le=255,
            description="Alpha Matting (Foreground Threshold)",
        ),
        ab: int = Query(
            default=10,
            ge=0,
            le=255,
            description="Alpha Matting (Background Threshold)",
        ),
        ae: int = Query(
            default=10, ge=0, description="Alpha Matting (Erode Structure Size)"
        ),
        om: bool = Query(default=False, description="Only Mask"),
        ppm: bool = Query(default=False, description="Post Process Mask"),
    ):
        self.model = model
        self.a = a
        self.af = af
        self.ab = ab
        self.ae = ae
        self.om = om
        self.ppm = ppm


def im_without_bg(content: bytes, commons: CommonQueryParams) -> Response:
    return Response(
        remove(
            content,
            session=sessions.setdefault(
                commons.model.value, new_session(commons.model.value)
            ),
            alpha_matting=commons.a,
            alpha_matting_foreground_threshold=commons.af,
            alpha_matting_background_threshold=commons.ab,
            alpha_matting_erode_size=commons.ae,
            only_mask=commons.om,
            post_process_mask=commons.ppm,
        ),
        media_type="image/png",
    )


@app.get('/')
def  index():
    return {"Error":"Not Authorized"}

@app.get(
    path="/api/remove",
    tags=["Background Removal"],
    summary="Remove from URL",
    description="Removes the background from an image obtained by retrieving an URL.",
)
async def get_index(
    url: str = Query(
        default=..., description="URL of the image that has to be processed."
    ),
    commons: CommonQueryParams = Depends(),
):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            file = await response.read()
            return await asyncify(im_without_bg)(file, commons)



@app.post('/api/remove')
async def post_index(
    file: bytes = File(
        default=...,
        description="Image file (byte stream) that has to be processed.",
    ),
    commons: CommonQueryPostParams = Depends(),
):
    return await asyncify(im_without_bg)(file, commons)
