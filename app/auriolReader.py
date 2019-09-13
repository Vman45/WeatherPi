from VentusDecoder import VentusDecoder
from Uploader import Uploader
from time import sleep, time, localtime
from datetime import datetime
import sys
import logging
import signal
import json

HTTP_ENDPOINT = ""

def main():
	logger.info('Starting')

	every = 1

	#Map of used pins
	pins = {
		'data' : 15,
		'enable' : 18
	}

	try:

		state = {}
		try:
			tmp = json.loads(open('status.txt', 'r').read())

			#if is not passed midnight or aren't elapsed 10 mins, restore the state
			now = localtime()
			if tmp['timestamp'][2] == now.tm_mday and (now.tm_hour*60 + now.tm_min) - (tmp['timestamp'][3]*60 + tmp['timestamp'][4]) <= 10:
				logger.info('Restored previous state')
				state = tmp

		except Exception: pass

		#Create threads
		v = VentusDecoder(pins['data'], pins['enable'], logger, state)
		uploader = Uploader(
			HTTP_ENDPOINT,
		 	'weather.db',
			logger
		)

		#Create thread exit handler
		def close(signum = None, frame = None, exitcode = 0):
			v.stop()

			#Save current state
			state = v.serialize()
			state['timestamp'] = localtime()
			with open('status.txt', 'w') as f:
				f.write(json.dumps(state))

			uploader.stop()
			logger.info('Quitted safely')
			sys.exit(exitcode)

		#for systemd exit
		signal.signal(signal.SIGINT, close)
		signal.signal(signal.SIGTERM, close)

		#Start threads
		v.start()
		uploader.start()

		start = time()

		#Wait until is ready
		while not v.isReady() and v.is_alive() and uploader.is_alive(): sleep(1)

		if v.isReady():
			logger.info('Checking completed!')

		lastUpdateMin = 60 #impossible minute

		#Upload every x minutes
		while v.is_alive() and uploader.is_alive():
			nowMin = localtime().tm_min
			if lastUpdateMin != nowMin and nowMin % every == 0:
				data = v.getData()
				data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:00')

				uploader.push(data)

				lastUpdateMin = nowMin

			sleep(1)

		logger.info('Quitting for thread death!')
		close(exitcode = 1)

	except (KeyboardInterrupt, SystemExit) as e:
		sys.exit()

	except Exception as e:
		logger.info('Exception : ' + str(e))
		raise



#Set up logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)

if __name__ == '__main__':
	main()
