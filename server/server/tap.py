from pprint import pformat
import sys, traceback, json, asyncio

class TapMiddleware:
    """
    Prints every ASGI event that reaches the app.  Remove after debugging.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        async def wrapped_receive():
            event = await receive()
            print("[TAP IN ]", pformat(event, compact=True)[:300], file=sys.stdout)
            return event

        async def wrapped_send(message):
            print("[TAP OUT]", pformat(message, compact=True)[:300], file=sys.stdout)
            await send(message)

        try:
            return await self.app(scope, wrapped_receive, wrapped_send)
        except Exception:
            traceback.print_exc(file=sys.stdout)
            raise
