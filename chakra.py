import sys
import asyncio
from kademlia.network import Server
from kademlia.node import Node, NodeHeap
from ecies.utils import generate_eth_key
from ecies import encrypt, decrypt


class ChatNode:
    def __init__(self, port):
        self.server = Server()
        self.port = port

    async def listen(self):
        await self.server.listen(self.port)

    async def bootstrap(self, bootstrap_node):
        await self.server.bootstrap([bootstrap_node])

    async def send_message(self, key, message):
        await self.server.set(key, message)

    async def get_messages(self, key):
        return await self.server.get(key)

    async def find_close_nodes(self, key):
        return await self.server.protocol.router.find_neighbors(key)

    async def listen_for_messages(self, chat_key):
        last_message = None
        while True:
            messages = await self.get_messages(chat_key)
            if messages and messages != last_message:
                print("\nNew message:")
                print(messages)
                last_message = messages
            await asyncio.sleep(1)  # Check every second

    async def listen_for_peers(self, chat_key):
        last_peer = None
        while True:
            peers = self.get_peers_from_routing_table()
            if peers and peers != last_peer:
                print("\nNew peer:")
                print(peers)
                last_peer = peers
            await asyncio.sleep(1)  # Check every second

    def get_peers_from_routing_table(self):
        peers = []
        for bucket in self.server.protocol.router.buckets:
            peers.extend(bucket.get_nodes())
        return peers

    async def crawl_network(self):
        seen_nodes = set()

        async def recursive_find(node_id):
            neighbors = await self.find_close_nodes(node_id)
            for neighbor in neighbors:
                if neighbor.id not in seen_nodes:
                    seen_nodes.add(neighbor.id)
                    await recursive_find(neighbor.id)

        # Start with our own node ID
        await recursive_find(self.server.node.id)
        return seen_nodes

    async def get_all_known_keys(self):
        known_keys = set()
        for bucket in self.server.protocol.router.buckets:
            for node in bucket.get_nodes():
                try:
                    keys = await self.server.protocol.get_keys(node)
                    known_keys.update(keys)
                except:
                    print("some thing")
        return known_keys

    async def get_all_key_value_pairs(self):
        keys = await self.get_all_known_keys()
        key_value_pairs = {}
        for key in keys:
            value = await self.server.get(key)
            if value is not None:
                key_value_pairs[key] = value
        return key_value_pairs


async def run():
    if len(sys.argv) != 4:
        print("Usage: python chat.py <port> <bootstrap_ip> <bootstrap_port>")
        return
    port = int(sys.argv[1])
    bootstrap_ip = sys.argv[2]
    bootstrap_port = int(sys.argv[3])

    chat_node = ChatNode(port)
    await chat_node.listen()
    print("Bootstrapping, please wait...")
    await chat_node.bootstrap((bootstrap_ip, bootstrap_port))
    await asyncio.sleep(5)

    #username = input("Enter your username: ")
    chat_key = "messages"

    eth_k = generate_eth_key()
    sk_hex = eth_k.to_hex()  # hex string
    pk_hex = eth_k.public_key.to_hex()  # hex string
    data = b'this is a crypto test'
    full_message = decrypt(sk_hex, encrypt(pk_hex, data))

    # Start the message listening task
    #listen_task1 = asyncio.create_task(chat_node.listen_for_messages(chat_key))
    #listen_task2 = asyncio.create_task(chat_node.listen_for_peers(chat_key))

    await chat_node.send_message(chat_key, full_message.decode('utf-8'))
    print(await chat_node.get_messages(chat_key))

    chat_node.server.stop()


asyncio.run(run())
