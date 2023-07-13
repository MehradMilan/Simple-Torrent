# Simple-Torent-Network
## The Computer Networks course homework.
### Spring 2023 - Sharif University of Technology
---


In this exercise, we created networks similar to the torrent network using `TCP` and `UDP` connections.

Only the `tracker` knows which peers have downloaded each file completely, and when a particular file is requested, information such as the file size and a list of peers that completely have the file should be sent to the requester. Then, the requester, according to the tracker's response, randomly selects one of the `peer`s who have the file and sends a download request to it. In the end, the requesting peer, after downloading the file, becomes a `seed`. That is, the program remains open and if needed, other peers can request the file from it.

- Unlike a regular download from a website, when the download is complete, the program doesn't stop; instead, it becomes a `seeder`. This means that nothing is downloaded but only uploads are taking place.

- A `keep-alive` mechanism is used between the tracker and each peer. This mechanism helps the tracker to realize which peers are still on the network.

- The connection between the **tracker and peer** is `UDP`, and the connection **between peers** is `TCP`.

With every request sent from a peer to the tracker, the name of that peer, its request, the peers who have that file, and ultimately the success or failure in obtaining the file are recorded in the tracker, which are displayed by entering the `request logs` command in the tracker command line. Also, every file that is published on the network logs a record for the tracker, and all these logs are displayed by entering the command `file_logs -all` in the tracker command line (which parts of which files are in the hands of which peers). By entering `file_logs <file_name>` in the tracker command line, the logs related to a file are displayed, and if the file doesn't exist, an appropriate error message should be displayed. In the peer program, the log of all responses received from the server to get a part of the file should be recorded, which are displayed by the command `request logs` in the peer command line.

## Commands:

```sh
tracker.py <IP:PORT>
```

Running the program in the above manner causes the tracker to listen to UDP port PORT and respond to requests. (locally)

- We assume that the peer program starts only in one of the two states, share or get.

```sh
peer.py share|get <FILENAME> <TRACKER_ADDRESS> <LISTEN_ADDRESS>
```
For example:
```sh
peer.py share myfile.txt 127.0.0.1:6771 127.0.0.1:52611
```
Shares the file *myfile.txt* on the torrent network with the tracker at address *127.0.0.1:6771*. Also, if someone wants to receive this file, they can connect to this peer at address *127.0.0.1:52611* and request the file.

```sh
peer.py get myfile.txt 127.0.0.1:6771 127.0.0.1:52612
```
With this command, we request from the tracker at address *127.0.0.1:6771* to send us information about the file *myfile.txt*.
