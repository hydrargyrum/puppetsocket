
import asyncio
import functools
import sys


async def copyto(fromsock, tosock):
	while True:
		data = await fromsock.read(1024)
		if not data:
			tosock.write_eof()
			await tosock.wait_closed()
			return

		tosock.write(data)
		await tosock.drain()


async def handle_connection(prot_reader, prot_writer, real_reader, real_writer, prot_server_l):
	print("both connected")
	prot_server_l[0].close()
	await asyncio.gather(
		copyto(prot_reader, real_writer),
		copyto(real_reader, prot_writer),
	)


async def handle_real_client(reader, writer):
	print("a real client connected")
	prot_server_l = []
	cb = functools.partial(
		handle_connection,
		real_reader=reader,
		real_writer=writer,
		prot_server_l=prot_server_l,
	)
	prot_server = await asyncio.start_server(
		cb,
		*PROT_ADDR,
		reuse_port=True,
	)
	prot_server_l.append(prot_server)
	async with prot_server:
		await prot_server.serve_forever()


async def main():
	fake_server = await asyncio.start_server(
		handle_real_client,
		*FAKE_ADDR,
		reuse_port=True,
	)

	async with fake_server:
		await fake_server.serve_forever()


PROT_ADDR = sys.argv[1].split(":")
PROT_ADDR[1] = int(PROT_ADDR[1])

FAKE_ADDR = sys.argv[2].split(":")
FAKE_ADDR[1] = int(FAKE_ADDR[1])

asyncio.run(main())
