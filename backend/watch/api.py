import json
import logging
import os
import sys
from typing import Optional

import asyncio
import uvicorn
import zmq
from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from starlette.responses import RedirectResponse
from zmq.asyncio import Context

logging.basicConfig(stream=sys.stdout, level='INFO')

zk_root = os.environ.get('ZK_ROOT', '/default')[1:]

req_sock = None
sub_sock = None

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
logger = logging.getLogger('api')


class Component(BaseModel):
    service: str
    color: str
    signal: str
    signal_path: str
    state: Optional[int]
    state_path: str
    version: str
    version_path: str
    expected_state: Optional[int]
    expected_state_path: str

class Global(BaseModel):
    global_type: str
    global_color: str
    global_signal: str
    global_version: str

class Path(BaseModel):
    path: str
    value: str


async def process_request(payload):
    global req_sock
    try:
        await req_sock.send(b'', zmq.SNDMORE)
        await req_sock.send_json(payload)
        message = await asyncio.wait_for(req_sock.recv_multipart(), timeout=2.0)
        resp = json.loads(message[1])
        return resp
    except Exception as e:
        print(e)
        req_sock.close()
        await init_req_sock()
        return {}



@app.get('/stream')
async def message_stream(request: Request):
    async def event_generator():
        while True:
            # If client was closed the connection
            if await request.is_disconnected():
                logger.info('sse connection is closed')
                break

            # Checks for new messages and return them to client if any
            msg = await sub_sock.recv_json()
            logger.info('received new update', msg)
            if msg:
                yield {
                    "data": json.dumps(msg)
                }

    return EventSourceResponse(event_generator())


async def init_req_sock():
    global req_sock
    ctx = Context.instance()
    req_sock = ctx.socket(zmq.DEALER)
    req_sock.bind('tcp://*:6667')


async def init_sub_sock():
    global sub_sock
    ctx = Context.instance()
    sub_sock = ctx.socket(zmq.SUB)
    sub_sock.connect("tcp://localhost:6666")
    sub_sock.setsockopt(zmq.SUBSCRIBE, b'')


@app.on_event('startup')
async def startup_event():
    await init_req_sock()
    await init_sub_sock()


@app.get('/env')
def get_env():
    return {'env': zk_root}


@app.post('/path')
async def read_for_path(path: Path):
    return await process_request({'type': 'get_path', 'path': path.path})


@app.put('/path')
async def update_for_path(path: Path):
    return await process_request({'type': 'set_path', 'path': path.path,
                                  'value': path.value})


@app.get('/components/{component}/{env}')
async def get_component(component: str, env: str):
    return await process_request({'type': 'get_component',
                                  'component': component, 'env': env})


@app.post('/global')
async def update_global(obj: Global):
    await process_request({'type': 'update_global',
                                   'global': vars(obj)})
    return 202

@app.post('/components')
async def update_component(obj: Component):
    return await process_request({'type': 'update_component',
                                  'component': vars(obj)})


@app.get('/components')
async def get_components():
    return await process_request({'type': 'components'})


@app.get("/")
async def redirect():
    response = RedirectResponse(url='/index.html')
    return response


app.mount("/", StaticFiles(directory="build"), name="build")

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=1090)
