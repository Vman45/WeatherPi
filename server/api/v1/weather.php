<?php

    require_once "Models.php";

    if($_SERVER['REQUEST_METHOD'] === 'GET'){
        //GET
        $size = 1;

        if(isset($_GET['size']) && is_numeric($_GET['size']))
            $size = intval($_GET['size']);

        $records = WeatherRecord::get($size);

        http_response_code(200);
        exit(json_encode($records));
    }
    else if ($_SERVER['REQUEST_METHOD'] === 'POST'){
        //POST

        $contentType = isset($_SERVER["CONTENT_TYPE"]) ? trim($_SERVER["CONTENT_TYPE"]) : '';
        //not json
        if(strcasecmp($contentType, 'application/json') !== 0){
            http_response_code(415);
            exit;
        }

        //get body
        $rawData = file_get_contents("php://input");

        //decode body as json
        $json = json_decode($rawData, true);

        //check for json sanity
        if(json_last_error() !== JSON_ERROR_NONE){
            http_response_code(415);
            exit;
        }

        //check for each parameter
        if(isset($json["token"]) and
            isset($json["wind_speed"]) and
            isset($json["wind_direction"]) and
            isset($json["wind_gust"]) and
            isset($json["temperature"]) and
            isset($json["rain"]) and
            isset($json["humidity"]) and
            isset($json["timestamp"])
        ){

            $db = DB::getInstance();

            //check for token existance
            $query = "SELECT `token_id` FROM `token` WHERE `token` = ?";
            $ans = $db->prepared($query, [$json["token"]]);
            if(count($ans) === 0){
                http_response_code(401);
                exit;
            }

            //insert
            $record = WeatherRecord::fill(
                $json["wind_speed"],
                $json["wind_direction"],
                $json["wind_gust"],
                $json["temperature"],
                $json["rain"],
                $json["humidity"],
                $json["timestamp"]
            );
            $ans = $record->save();

            //201 -> Created
            //409 -> Conflict
            http_response_code($ans ? 201 : 409);
            exit;
        }

        http_response_code(415);
        exit;
    }

?>
