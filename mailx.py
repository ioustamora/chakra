import argparse
import logging
import asyncio

from kademlia.network import Server

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log = logging.getLogger('kademlia')
log.addHandler(handler)
log.setLevel(logging.DEBUG)

server = Server()


async def get_by_key(args):
    await server.listen(args.l)
    bootstrap_node = (args.i, int(args.p))
    await server.bootstrap([bootstrap_node])

    result = await server.get(args.k)
    print("Get result:", result)
    server.stop()


async def set_key_value(args):
    await server.listen(args.l)
    bootstrap_node = (args.i, int(args.p))
    await server.bootstrap([bootstrap_node])
    await server.set(args.k, args.v)
    server.stop()


def connect_to_bootstrap_node(args):
    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    loop.run_until_complete(server.listen(args.l))
    bootstrap_node = (args.i, int(args.p))
    loop.run_until_complete(server.bootstrap([bootstrap_node]))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
        loop.close()


def create_bootstrap_node(args):
    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    loop.run_until_complete(server.listen(args.p))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
        loop.close()


async def main():
    parser = argparse.ArgumentParser(prog='mailx', description="dht encrypted mail")

    parser.add_argument('mode', help='command: node, get or set', choices=['node', 'get', 'set'])
    parser.add_argument('-i', help='set ip of bootstrap node')
    parser.add_argument('-p', help='set port of bootstrap node')
    parser.add_argument('-l', help='set local port')
    parser.add_argument('-k', help='set key')
    parser.add_argument('-v', help='set value')

    args = parser.parse_args()

    if args.i is None:
        args.i = '127.0.0.1'

    if args.p is None:
        args.p = 5000

    if args.k is None:
        args.k = 'messages'

    if args.l is None:
        args.l = 5001

    print(args)

    if args.mode == 'node':
        create_bootstrap_node(args)

    if args.mode == 'set':
        await set_key_value(args)

    if args.mode == 'get':
        await get_by_key(args)


if __name__ == "__main__":
    asyncio.run(main())
