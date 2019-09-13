import sqlite3

class AuriolStorage:

    def __init__(self, filename):
        self.filename = filename
        self.queryCreate = """CREATE TABLE IF NOT EXISTS queue (
                id integer primary key AUTOINCREMENT,
                wind_speed decimal(3,1) NOT NULL,
                wind_direction int(3) NOT NULL,
                wind_gust decimal(3,1) NOT NULL,
                temperature decimal(3,1) NOT NULL,
                rain decimal(3,1) NOT NULL,
                humidity int(2) NOT NULL,
                timestamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        self.queryInsert = 'INSERT INTO queue (wind_speed, wind_direction, wind_gust, temperature, rain, humidity, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)'
        self.format = ('wind_speed', 'wind_direction', 'wind_gust', 'temperature', 'rain', 'humidity', 'timestamp')
        self.querySelectOne = 'SELECT * FROM queue LIMIT 1'
        self.queryDelete = 'DELETE FROM queue WHERE id = ?'
        self.query_count = 'SELECT count(*) FROM queue'

        try:
            self.db = sqlite3.connect(self.filename)
            self.cursor = self.db.cursor()

            self.cursor.execute(self.queryCreate)

            self.db.commit()
        except sqlite3.Error as e:
            raise


    def push(self, data):
        self.cursor.execute(self.queryInsert, tuple(data[f] for f in self.format))
        self.db.commit()


    def _front(self):
        #Get first row
        self.cursor.execute(self.querySelectOne)
        r = self.cursor.fetchone()
        return r


    def front(self):
        return self.jsonize(self._front())


    def pop(self):
        #Get first row
        r = self._front()
        #Delete row added
        self.cursor.execute(self.queryDelete, (r[0],))
        #Commit changes
        self.db.commit()
        return self.jsonize(r)


    def size(self):
        self.cursor.execute(self.query_count)
        return self.cursor.fetchone()[0]


    def close(self):
        self.db.close()


    def jsonize(self, row):
        data = {f : v for f, v in zip(self.format, row[1:])}
        return data

