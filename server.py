import obspython as obs
import asyncio
import threading
import websockets

clients = set()

async def socket_handler(websocket):
    clients.add(websocket)
    print(f"FXWizard: Client Connected. Total: {len(clients)}")
    try:
        async for message in websocket:
            # BROADCAST LOGIC
            if clients:
                print(f"FXWizard: Broadcasting to {len(clients)} clients...")
                # We create a list from the set to prevent 'size changed' errors
                for client in list(clients):
                    try:
                        # Direct send; if the client is dead, it will trigger the except
                        await client.send(message)
                    except Exception:
                        # Clean up dead clients on the fly
                        clients.discard(client)
    except Exception as e:
        print(f"FXWizard Socket Error: {e}")
    finally:
        clients.discard(websocket)
        print(f"FXWizard: Client Disconnected. Total: {len(clients)}")

async def main_async_entry(host, port):
    async with websockets.serve(socket_handler, host, port):
        await asyncio.Future()  # Keep server alive

def start_server_thread(loop):
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main_async_entry("0.0.0.0", 8080))
    except Exception as e:
        print(f"FXWizard Thread Error: {e}")

def script_description():
    return "FXWizard WebSocket Server"

def script_load(settings):
    new_loop = asyncio.new_event_loop()
    t = threading.Thread(target=start_server_thread, args=(new_loop,), daemon=True)
    t.start()