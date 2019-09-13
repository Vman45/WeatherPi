import pigpio as pi
from time import sleep, time, localtime
from threading import Thread

class VentusDecoder(Thread):

    def __init__(self, data, enable, logger, init = {}):
        #Inherit from Thread
        Thread.__init__(self, name = 'decoder')
        self.name = 'decoder'

        self.logger = logger

        #Initialization of internal state
        self.reverseBitsLookup = [
            0x0, 0x8, 0x4, 0xC, 0x2, 0xA, 0x6, 0xE,
            0x1, 0x9, 0x5, 0xD, 0x3, 0xB, 0x7, 0xF
        ]
        self.enum = {
            'UNKNOWN' : 0,
            'T0' : 1,
            'OK' : 2,
            'DONE' : 3
        }
        self.resetDecoder()
        self.flag = 0

        #Initialization of intervals variables
        self.lastHit = 0
        self.hits = []

        #Gpio setup
        self.g = pi.pi()
        self.enablePin = enable
        self.dataPin = data

        self.g.set_mode(self.enablePin, pi.OUTPUT)
        self.g.set_mode(self.dataPin, pi.INPUT)

        #Initialization of weather data
        #rain
        self.rainID = self.currentRainTick = self.rain = 0
        #wind
        self.windID = self.currentWindDir = self.currentWindGust = self.currentWindAvg = 0
        #temperature
        self.temperature = 0

        if init.get('flag', 0) != 0:
            self.flag = init['flag']

            if self.flag & 0x01:
                self.rainID = init['rainID']
                self.currentRainTick = init['currentRainTick']
                self.rain = init['rain']

            if self.flag & 0x02:
                self.windID = init['windID']
                self.currentWindDir = init['currentWindDir']
                self.currentWindGust = init['currentWindGust']

            if self.flag & 0x04:
                self.windID = init['windID']
                self.currentWindAvg = init['currentWindAvg']

            if self.flag & 0x08:
                self.temperature = init['temperature']


    #Thread methods
    def run(self):

        self.logger.info('Starting console handler')

        #Turn on the console
        self.g.write(self.enablePin, pi.LOW)
        sleep(1)
        self.g.write(self.enablePin, pi.HIGH)

        #Initialization of interrupt
        self.g.callback(self.dataPin, pi.EITHER_EDGE, self.hit)

        #Set stop flag
        self.stopped = False

        self.lastPacket = time()
        self.lastReset = localtime().tm_mday

        #Check for packet if thread hasn't been stopped or connection is alive
        while not self.stopped:

            now = localtime()
            if self.lastReset != now.tm_mday and now.tm_hour == 0 and now.tm_min == 0:
                self.lastReset = now.tm_mday
                self.rain = 0
                self.logger.info('Resetted rain count')

            if time() - self.lastPacket > 60*4:
                self.logger.info('Connection lost, quit')
                break

            if len(self.hits) == 0: sleep(1)
            elif self.nextPulse():
                if self.checkSum():
                    self.lastPacket = time()
                self.resetDecoder()

        self.g.stop()
        self.logger.info('Stopping console handler')


    def stop(self):
        self.stopped = True
        self.join()


    def isReady(self):
        return self.flag == 0xF


    def resetDecoder(self):
        self.totalBits = self.pos = 0
        self.state = self.enum['UNKNOWN']
        self.data = [0 for _ in range(25)]


    def hit(self, gpio, level, timestamp):
        elapsed = timestamp - self.lastHit
        if elapsed < 0:
            #Build full timestamp with 33 bits number
            fullTimestamp = 1 << 32 + timestamp
            #Calculate real elapsed time
            elapsed = fullTimestamp - self.lastHit

        if elapsed > 200:
            #Manual overflow
            self.lastHit = (self.lastHit + elapsed) & 0xFFFFFFFF
            self.hits.append(elapsed)


    def gotBit(self, value):
        self.data[self.pos] = ((self.data[self.pos] << 1) | value )
        self.totalBits += 1
        self.pos = self.totalBits >> 3
        if self.pos >= len(self.data): self.resetDecoder()
        self.state = self.enum['OK']


    def nextPulse(self):
        if self.state != self.enum['DONE']:
            decoded = self.decode(self.hits[0])
            if decoded == -1: self.resetDecoder()
            elif decoded == 1: self.state = self.enum['DONE']

        del self.hits[0]

        return self.state == self.enum['DONE']


    def decode(self, width):
        if self.state == self.enum['UNKNOWN']:
            if 425 <= width and width < 575:
                self.state = self.enum['T0']
            else: return -1

        elif self.state == self.enum['T0']:
            if 1700 < width and width < 4600:
                if width < 2300:
                    self.gotBit(0)
                elif width > 3400:
                    self.gotBit(1)
                else: return -1
                self.state = self.enum['UNKNOWN']

            elif self.totalBits > 35 and 7650 < width and width < 10350:
                self.data[self.pos] = self.data[self.pos] << 4
                self.pos+=1
                return 1

            else: return -1

        else: return -1

        return 0


    def checkSum(self):
        rain = ((self.data[1] & 0x7F ) == 0x6C)
        s = 0x7 if rain else 0xF
        for i in range(8):
            if i%2: t = self.reverseBitsLookup[self.data[i//2] & 0xF]
            else: t = self.reverseBitsLookup[self.data[i//2] >> 4]
            s += t if rain else -t

        if (( s & 0x0F ) == self.reverseBitsLookup[self.data[4] >> 4]):
            self.update()
            return True
        return False


    def reverseShort(self, toReverse):
        out = toReverse
        for _ in range(15):
            out <<= 1
            toReverse >>= 1
            out |= toReverse & 1
        return out


    def update(self):
        #rain packet
        if (self.data[1] & 0x7F) == 0x6C :
            self.logger.debug('Rain packet')
            tmp = self.reverseShort((self.data[2] << 8) | self.data[3]) & 0xFFFF
            if self.flag & 0x01:
                if tmp > self.currentRainTick:
                    self.rain += (tmp - self.currentRainTick) * .25
                    self.currentRainTick = tmp
            else:
                self.flag |= 0x01
                self.rainID = self.data[0]
                self.currentRainTick = tmp

        #wind direction/gust packet
        elif (self.data[1] & 0x6E) == 0x6E:
            self.logger.debug('Gust packet')
            if not (self.flag & 0x02):
                self.flag |= 0x02
                self.windID = self.data[0]

            self.currentWindDir = self.reverseShort((self.data[1] & 0x01 << 8) | self.data[2]) >> 7  & 0x1FF
            self.currentWindGust = (self.reverseShort(self.data[3]) >> 8 & 0xFF) * .2

        #wind average packet
        elif (self.data[1] & 0x6F) == 0x68 and self.data[2] == 0x00:
            self.logger.debug('Wind packet')
            if not self.flag & 0x04:
                self.flag |= 0x04
                self.windID = self.data[0]

            self.currentWindAvg = (self.reverseShort(self.data[3]) >> 8 & 0xFF) * .2

        #temperature packet
        elif (self.data[1] & 0x60) == 0x00 or (self.data[1] & 0x60) == 0x20 or (self.data[1] & 0x60) == 0x40:
            self.logger.debug('Temperature packet')
            if not (self.flag & 0x08):
                self.flag |= 0x08
                self.windID = self.data[0]
            self.temperature = ((self.reverseShort((self.data[1]&0x0F << 8) | self.data[2]) >> 4) & 0xFFF) * .1


    def getData(self):
        if not self.isReady: return {}
        return {
            'rain' : str(self.rain)[:str(self.rain).find('.')+3],
            'wind_direction' : str(self.currentWindDir),
            'wind_gust' : str(self.currentWindGust)[:str(self.currentWindGust).find('.')+2],
            'wind_speed' : str(self.currentWindAvg)[:str(self.currentWindAvg).find('.')+2],
            'temperature' : str(self.temperature)[:str(self.temperature).find('.')+2],
        }


    def serialize(self):
        rainSection =  {
            'rainID' : self.rainID,
            'currentRainTick' : self.currentRainTick,
            'rain' : self.rain
        } if self.flag & 0x01 else {}

        directionSection = {
            'windID' : self.windID,
            'currentWindDir' : self.currentWindDir,
            'currentWindGust' : self.currentWindGust
        } if self.flag & 0x02 else {}

        windSection = {
            'windID' : self.windID,
            'currentWindAvg' : self.currentWindAvg
        } if self.flag & 0x04 else {}

        temperatureSection = {
            'temperature' : self.temperature
        } if self.flag & 0x08 else {}

        return {**rainSection, **directionSection, **windSection, **temperatureSection, 'flag' : self.flag}