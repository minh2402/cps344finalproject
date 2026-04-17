## Reliable Data Transmission

### Getting Started
Follow the same strategy you used to build assignment 2. This assignment also uses the `asio` library for communication between a client and a server.

Since this is another client-server application, running `make` will generate two programs: `client` and `server`. Try starting the server in one terminal `./server` and then running the client in another terminal `./client`. Make sure that you start the server first, as otherwise the client will complain about there not being a server.

You will only need to modify `client.cpp` to get this project running. (no server modification allowed!) 

### Next steps
As menetioned in the write-up, you can pass flags to the server to help in debugging. `./server --no-delay` disables delay and `./server --no-packet-drops` disables packet loss. You can also use both debug options at the same time `./server --no-delay --no-packet-drops`. For the optional extra-credit challenge, use `./server --chaos`. Note that your client must produce the correct output *without* these debug flags enabled for full credit! 
