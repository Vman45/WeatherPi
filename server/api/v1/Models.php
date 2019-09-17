<?php

    if (strcasecmp(str_replace('\\', '/', __FILE__), $_SERVER['SCRIPT_FILENAME']) == 0) {
        http_response_code(404);
        exit;
    }

    require "DB.php";

    class WeatherRecord{

        /*Static variables*/
        private static $db = null;

        /*Static methods*/
        private static function getDB(){ static::$db = DB::getInstance(); }

        /*Void constructor*/
        private function __construct() {}

        /*Filler constructor*/
        public static function fill($wind_speed, $wind_direction, $wind_gust, $temperature, $rain, $humidity, $timestamp){

            $obj = new self();

            $obj->wind_speed = $wind_speed;
            $obj->wind_direction = $wind_direction;
            $obj->wind_gust = $wind_gust;
            $obj->temperature = $temperature;
            $obj->rain = $rain;
            $obj->humidity = $humidity;
            $obj->timestamp = $timestamp;

            return $obj;
        }

        /*Gets last $size element*/
        public static function get(int $size) : array{
            static::getDB();

            $query = 'SELECT * FROM `weather` ORDER BY `timestamp` DESC LIMIT ?;';
            $ans = static::$db->prepared($query, [$size]);

            if(isset($ans["error"])){
                return $ans;
            }

            $record = [];
            foreach($ans as $r){
                array_push($record, WeatherRecord::fill(
                    $r['wind_speed'],
                    $r['wind_direction'],
                    $r['wind_gust'],
                    $r['temperature'],
                    $r['rain'],
                    $r['humidity'],
                    $r['timestamp']
                ));
            }
            return $record;
        }

        /*Insert this instance into the database*/
        public function save(){
            static::getDB();

            $query = 'INSERT INTO weather VALUES(default, ?, ?, ?, ?, ?, ?, ?)';
            $params = [$this->wind_speed,
                        $this->wind_direction,
                        $this->wind_gust,
                        $this->temperature,
                        $this->rain,
                        $this->humidity,
                        $this->timestamp,
            ];

            $ans = static::$db->preparedExec($query, $params);

            return !isset($ans["error"]);
        }

        //Remove this instance from the database
        public function remove(){
          static::getDB();

          $query = "DELETE FROM weather WHERE timestamp = ?";
          $params = [$this->timestamp];

          return static::$db->exec($query, $params);
        }
    }

?>
