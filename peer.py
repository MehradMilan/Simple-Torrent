import asyncio
import socket
import json
import sys

class Peer:
    def __init__(self, mode, file_name, tracker_address, listen_address):
        self.mode = mode
        self.file_name = file_name
        self.tracker_ip, self.tracker_port = tracker_address.split(':')
        self.tracker_port = int(self.tracker_port)
        self.peer_ip, self.peer_port = listen_address.split(':')
        self.peer_port = int(self.peer_port)
        self.response_logs = []

    async def run(self):
        if self.mode == "share":
            await self.share_file()
        else:
            await self.get_file()

    async def share_file(self):
        with open(self.file_name, "rb") as f:
            self.file_data = f.read()

        loop = asyncio.get_event_loop()
        server = await asyncio.start_server(self.handle_request, "127.0.0.1", self.peer_port)

        addr = server.sockets[0].getsockname()
        self.peer_port = addr[1]
        print(f"Sending file {self.file_name} to {addr}")

        asyncio.ensure_future(self.send_share_to_tracker())
        asyncio.ensure_future(self.send_keep_alive())

        async with server:
            await server.serve_forever()

    async def get_file(self):
        print(f"Requesting {self.file_name} from tracker")
        peer = await self.send_share_to_tracker()
        if peer:
            data = await self.download_file(peer)
            if data:
                print(f"Downloaded {self.file_name} from {peer}")
                print("Switching to seeder mode")
                await self.share_file()

    async def send_share_to_tracker(self):
        message = {"action": "share", "file_name": self.file_name, "peer": [self.peer_ip, self.peer_port]}
        await self.send_udp_message_to_tracker(message)

    async def send_get_to_tracker(self):
        message = {"action": "get", "file_name": self.file_name}
        response = await self.send_udp_message_to_tracker(message)
        if not response["peers"]:
            print(f"No peers found for {self.file_name}")
            return
        return response["peers"][0]

    async def send_udp_message_to_tracker(self, message):
        loop = asyncio.get_event_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: UDPProtocol(), remote_addr=(self.tracker_ip, self.tracker_port)
        )

        try:
            if message["action"] == "keep_alive":
                protocol.send_message_without_response(json.dumps(message).encode())
            else:
                return await protocol.send_message(json.dumps(message).encode())
        finally:
            transport.close()


    async def handle_request(self, reader, writer):
        peer = writer.get_extra_info('peername')
        print(f"Uploading {self.file_name} to {peer}")
        self.response_logs.append({"action": "upload", "file_name": self.file_name, "peer": peer})
        await asyncio.sleep(5)
        writer.write(self.file_data)
        await writer.drain()
        writer.close()
        await writer.wait_closed()


    async def download_file(self, peer):
        reader, writer = await asyncio.open_connection(*peer)
        data = await reader.read()
        writer.close()
        await writer.wait_closed()

        with open(self.file_name, "wb") as f:
            f.write(data)

        return data

    
    async def send_keep_alive(self):
        while True:
            message = {"action": "keep_alive", "peer": [self.peer_ip, self.peer_port]}
            await self.send_udp_message_to_tracker(message)
            await asyncio.sleep(2)

class UDPProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.transport = None
        self.future = asyncio.Future()

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        self.future.set_result(json.loads(data))

    async def send_message(self, message):
        self.transport.sendto(message)
        return await self.future
    
    def send_message_without_response(self, message):
        self.transport.sendto(message)


async def async_input(prompt: str = "") -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)

async def handle_commands(peer):
    while True:
        command = await async_input()
        if command == "request logs":
            print('Requests Log:')
            for log in peer.response_logs:
                print("Action: ", log['action'], " - File Name: ", log['file_name'], " - Peer: ", log['peer'])
        elif command == "quit":
            break
        else:
            print("Invalid command")

def get_command():
    n = len(sys.argv)
    mode = sys.argv[1]
    file_name = sys.argv[2]
    tracker_address = sys.argv[3]
    listen_address = sys.argv[4]
    params = {
        'n' : n,
        'mode' : mode,
        'file_name' : file_name,
        'tracker_address' : tracker_address,
        'listen_address' : listen_address
    }
    return params

async def main():
    p = get_command()
    if p['n'] != 5:
        print("Invalid Command")
        sys.exit(1)

    peer = Peer(p['mode'], p['file_name'], p['tracker_address'], p['listen_address'])
    await asyncio.gather(peer.run(), handle_commands(peer))

if __name__ == "__main__":
    asyncio.run(main())