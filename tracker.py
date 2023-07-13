import asyncio
import json
import sys

class Request:
    def __init__(self, peer, file_name, req) -> None:
        self.peer = peer
        self.file_name = file_name
        self.req = req
        self.success = True
        self.peers_contain_file = []

    def not_succeed(self):
        self.success = False

    def find_peers_contain_file(self, tracker):
        self.peers_contain_file = tracker.files.get(self.file_name, [])

class Tracker:
    def __init__(self, host="127.0.0.1", port=6771):
        self.host = host
        self.port = port
        self.files = {}
        self.logs = []
        self.peer_timeouts = {}

    def log_request(self, request):
        self.logs.append(request)

    async def run(self):
        loop = asyncio.get_event_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: TrackerProtocol(self), local_addr=(self.host, self.port)
        )

        print(f"Tracker Listening on {self.host}:{self.port}...")

        try:
            await asyncio.sleep(1000)
        finally:
            transport.close()

    def handle_message(self, message, addr):
        action = message.get("action")
        file_name = message.get("file_name")

        if action == "share":
            peer = message.get("peer")
            self.add_peer(file_name, peer)
            print(f"Registered {file_name} from {peer}")
            request = Request(peer, file_name, action)
            request.find_peers_contain_file(self)
            self.log_request(request)

        elif action == "get":
            peers = self.files.get(file_name, [])
            response = json.dumps({"peers": peers}).encode()
            self.protocol.transport.sendto(response, addr)
            print(f"Sent info of {file_name} to {addr}")
            request = Request(addr, file_name, action)
            request.find_peers_contain_file(self)
            self.log_request(request)

        elif action == "keep_alive":
            peer = message.get("peer")
            self.peer_timeouts[tuple(peer)] = asyncio.get_event_loop().time()

        else:
            request = Request(peer, file_name, action)
            request.not_succeed()
            self.log_request(request)

    async def check_timeouts(self):
        while True:
            current_time = asyncio.get_event_loop().time()
            timeout_threshold = 10  # Adjust the timeout threshold as needed

            for peer, last_seen in list(self.peer_timeouts.items()):
                if current_time - last_seen > timeout_threshold:
                    print(f"Peer {peer} timed out")
                    self.remove_peer(peer)
                    del self.peer_timeouts[peer]

            await asyncio.sleep(5)

    def add_peer(self, file_name, peer):
        if file_name not in self.files:
            self.files[file_name] = []

        if peer not in self.files[file_name]:
            self.files[file_name].append(peer)

    def remove_peer(self, peer):
        for file_name, peers in self.files.items():
            if peer in peers:
                peers.remove(peer)
                if not peers:
                    del self.files[file_name]

    def file_logs(self, file_name):
        if file_name == "all":
            return self.files
        else:
            return {file_name: self.files.get(file_name, [])}

class TrackerProtocol(asyncio.DatagramProtocol):
    def __init__(self, tracker):
        self.tracker = tracker

    def connection_made(self, transport):
        self.transport = transport
        self.tracker.protocol = self

    def datagram_received(self, data, addr):
        message = json.loads(data.decode())
        self.tracker.handle_message(message, addr)

async def async_input(prompt: str = "") -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)

async def handle_commands(tracker):
    while True:
        command = await async_input()
        if command == "request logs":
            print('Requests Log:')
            for log in tracker.logs:
                print("Peer: ", log.peer, " - Successful: ", log.success, " - Peers containing the file: ", log.peers_contain_file)
        elif command == "file_logs -all":
            print('File Logs:')
            logs = tracker.file_logs("all")
            for file_name, peers in logs.items():
                print(f"{file_name}: {peers}")
        elif command.startswith(">file_logs>"):
            file_name = command.split(">")[2]
            print(f'File Logs for {file_name}:')
            logs = tracker.file_logs(file_name)
            if not logs[file_name]:
                print("Error: File not found.")
            else:
                print(logs)
        elif command == "quit":
            break
        else:
            print("Invalid command")

def get_command():
    n = len(sys.argv)
    ip = sys.argv[1].split(':')[0]
    port = sys.argv[1].split(':')[1]
    params = {
        'ip' : ip,
        'port' : port
    }
    return params

async def main():
    p = get_command()
    tracker = Tracker(p['ip'], p['port'])
    await asyncio.gather(tracker.run(), handle_commands(tracker), tracker.check_timeouts())

if __name__ == "__main__":
    asyncio.run(main())
