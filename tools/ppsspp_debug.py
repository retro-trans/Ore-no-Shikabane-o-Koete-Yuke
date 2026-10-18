"""Local PPSSPP debugger API client; operates only on the project test instance."""
import asyncio
import base64
import json
import uuid
from pathlib import Path

import websockets

URL = 'ws://127.0.0.1:19417/debugger'


class Session:
    def __enter__(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.ws = self.loop.run_until_complete(websockets.connect(URL, max_size=128 << 20))
        return self

    def __exit__(self, *args):
        self.loop.run_until_complete(self.ws.close())
        self.loop.close()

    def call(self, event, **params):
        async def invoke():
            ticket = str(uuid.uuid4())
            await self.ws.send(json.dumps(dict(params, event=event, ticket=ticket)))
            while True:
                response = json.loads(await asyncio.wait_for(self.ws.recv(), 30))
                if response.get('ticket') == ticket or (event in ('cpu.stepping', 'cpu.resume') and response.get('event') == event):
                    if response.get('event') == 'error':
                        raise RuntimeError(response)
                    return response
        return self.loop.run_until_complete(invoke())


async def request_async(event, **params):
    ticket = str(uuid.uuid4())
    async with websockets.connect(URL, max_size=128 << 20) as ws:
        await ws.send(json.dumps(dict(params, event=event, ticket=ticket)))
        while True:
            response = json.loads(await asyncio.wait_for(ws.recv(), 30))
            if response.get('ticket') == ticket or (event in ('cpu.stepping', 'cpu.resume') and response.get('event') == event):
                if response.get('event') == 'error':
                    raise RuntimeError(response)
                return response


def request(event, **params):
    return asyncio.run(request_async(event, **params))


def read(address, size):
    return base64.b64decode(request('memory.read', address=address, size=size)['base64'])


def screenshot(path):
    with Session() as session:
        old = session.call('cpu.status')['stepping']
        try:
            if not old:
                session.call('cpu.stepping')
            result = session.call('gpu.buffer.screenshot', type='uri')
        finally:
            if not old:
                session.call('cpu.resume')
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(base64.b64decode(result['uri'].split(',', 1)[1]))
    return {k: v for k, v in result.items() if k != 'uri'}


if __name__ == '__main__':
    import sys
    print(json.dumps(request(sys.argv[1] if len(sys.argv) > 1 else 'game.status',
                             **(json.loads(sys.argv[2]) if len(sys.argv) > 2 else {})), indent=2)[:12000])
