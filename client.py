import asyncio
import sys

async def copyto(fromsock, tosock):
	while True:
		data = await fromsock.read(1024)
		if not data:
			tosock.close()
			await tosock.wait_closed()
			break

		tosock.write(data)
		await tosock.drain()


async def connect_loop():
	loop = asyncio.get_event_loop()
	
	while True:
		# try to connect to puppet server
		try:
			puppet_reader, puppet_writer = await asyncio.open_connection(*PUPPET_SERVER)
		except OSError:
			print("puppet server is not listening")
			await asyncio.sleep(1)
			print("end waiting")
			continue

		# when puppet server accepts, we can connect to real server
		try:
			real_reader, real_writer = await asyncio.open_connection(*REAL_SERVER)
		except OSError as exc:
			print("failed connecting to real server: %s" % exc)
			puppet_writer.close()
			tasks.add(asyncio.create_task(puppet_writer.wait_closed()))
			continue

		print("connected to puppet and real! linking them")
		loop.create_task(copyto(puppet_reader, real_writer))
		loop.create_task(copyto(real_reader, puppet_writer))


REAL_SERVER = sys.argv[1].split(":")
REAL_SERVER[1] = int(REAL_SERVER[1])

PUPPET_SERVER = sys.argv[2].split(":")
PUPPET_SERVER[1] = int(PUPPET_SERVER[1])

loop = asyncio.get_event_loop()
loop.create_task(connect_loop())
loop.run_forever()
