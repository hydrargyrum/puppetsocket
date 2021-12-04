import socket
import asyncio
import time
import sys

async def copyto(fromsock, tosock):
	while True:
		data = await fromsock.read(1024)
		print(data)
		if not data:
			# tosock.write_eof()
			tosock.close()
			await tosock.wait_closed()
			break

		tosock.write(data)
		await tosock.drain()


async def main():
	while True:
		try:
			fake_reader, fake_writer = await asyncio.open_connection(*FAKE_SERVER)
		except OSError:
			print("fake server is not listening")
			time.sleep(1)
			continue

		real_reader, real_writer = await asyncio.open_connection(*REAL_SERVER)
		print("connected both!")
		await asyncio.gather(
			copyto(fake_reader, real_writer),
			copyto(real_reader, fake_writer),
		)


async def main():
	tasks = set()
	done = ()
	while True:
		# try to connect to fake server
		fake_conn = asyncio.create_task(asyncio.open_connection(*FAKE_SERVER))
		tasks.add(fake_conn)
		while fake_conn not in done:
			done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
		done = ()

		assert fake_conn.done()
		try:
			fake_reader, fake_writer = fake_conn.result()
		except OSError:
			print("fake server is not listening")
			await asyncio.sleep(10)
			print("end waiting")
			continue

		# when fake server accepts, we can connect to real server
		real_conn = asyncio.create_task(asyncio.open_connection(*REAL_SERVER))
		tasks.add(real_conn)
		while real_conn not in done:
			done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
		done = ()

		assert real_conn.done()
		try:
			real_reader, real_writer = real_conn.result()
		except OSError as exc:
			print("failed connecting to real server: %s" % exc)
			fake_writer.close()
			tasks.add(asyncio.create_task(fake_writer.wait_closed()))
			continue

		print("connected to fake and real! linking them")
		tasks.add(asyncio.create_task(copyto(fake_reader, real_writer)))
		tasks.add(asyncio.create_task(copyto(real_reader, fake_writer)))


REAL_SERVER = sys.argv[1].split(":")
REAL_SERVER[1] = int(REAL_SERVER[1])

FAKE_SERVER = sys.argv[2].split(":")
FAKE_SERVER[1] = int(FAKE_SERVER[1])

asyncio.run(main())
