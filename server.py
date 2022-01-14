#!/usr/bin/env python3

import asyncio
import sys


async def copyto(fromsock, tosock):
	while True:
		data = await fromsock.read(1024)
		if not data:
			tosock.close()
			await tosock.wait_closed()
			return

		tosock.write(data)
		await tosock.drain()


async def fake_server():
	fake_server = await asyncio.start_server(
		handle_real_client,
		*FAKE_ADDR,
	)

	async with fake_server:
		await fake_server.serve_forever()


async def get_puppet_client():
	# listen on puppet server, accept a single puppet client and stop listening

	loop = asyncio.get_event_loop()

	async def handle_client(reader, writer):
		puppet_server.close()
		await puppet_server.wait_closed()
		rw.set_result((reader, writer))

	rw = loop.create_future()

	async with PUPPET_LOCK:
		puppet_server = await asyncio.start_server(
			handle_client,
			*PUPPET_ADDR,
		)
		async with puppet_server:
			return (await rw)


async def handle_real_client(real_reader, real_writer):
	loop = asyncio.get_event_loop()

	print("a real client connected")

	puppet_reader, puppet_writer = await get_puppet_client()
	print("both connected")

	loop.create_task(copyto(puppet_reader, real_writer))
	loop.create_task(copyto(real_reader, puppet_writer))


PUPPET_LOCK = asyncio.Lock()

PUPPET_ADDR = sys.argv[1].split(":")
PUPPET_ADDR[1] = int(PUPPET_ADDR[1])

FAKE_ADDR = sys.argv[2].split(":")
FAKE_ADDR[1] = int(FAKE_ADDR[1])


loop = asyncio.get_event_loop()
loop.create_task(fake_server())
loop.run_forever()
