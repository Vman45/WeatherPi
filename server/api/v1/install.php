<?php

    //Get init.sql content and split the various query
    $sql = file_get_contents("init.sql");
    $sql = trim($sql);
    $queries = explode(";", $sql);

    //Get DB connection via singleton
    require_once "DB.php";
    $db = DB::getInstance();

    //Execute each DDL query
    foreach($queries as $q)
        if (!empty($q)){
            $result = $db->exec($q . ";");
            if (is_array($result) && isset($result['error']))
                echo "Error with {$q} => {$result['error']} <br />";
        }

?>