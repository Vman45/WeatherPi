<?php

    if (strcasecmp(str_replace('\\', '/', __FILE__), $_SERVER['SCRIPT_FILENAME']) == 0) {
        http_response_code(404);
        exit;
    }

    class DB{

        private static $instance = null;
        private $dbUser = "";
        private $dbPasswd = "";
        private $dbName = "";
        private $dbHost = "";
        private $connection = null;

        //Singleton getter
        public static function getInstance() {
            if (static::$instance === null) {
                static::$instance = new DB();
            }
            return static::$instance;
        }

        //Executes query without parameters and without return
        public function exec(string $query){
            static::getInstance();
            if($this->connection === null) return null;

            try{
                return $this->connection->exec($query);
            }
            catch(PDOException $e){
                return ["error" => $e->getMessage()];
            }
        }

        //Executes query with parameter and no return values
        public function preparedExec(string $query, array $args) :array{
            static::getInstance();
            if($this->connection === null){
                return ["error" => "Error with DB connection"];
            }
            try{
                $stmt = $this->connection->prepare($query);
                $stmt->execute($args);
                return [];
            }
            catch(PDOException $e){
                return ["error" => $e->getMessage()];
            }
        }

        //Executes query with parameter and return values
        public function prepared(string $query, array $args) : array{
            static::getInstance();
            if($this->connection === null){
                return ["error" => "Error with DB connection"];
            }
            try{
                $stmt = $this->connection->prepare($query);
                $stmt->execute($args);
                return $stmt->fetchAll(PDO::FETCH_ASSOC);
            }
            catch(PDOException $e){
                return ["error" => $e->getMessage()];
            }
        }

        private function __construct(){
            try{
                $this->connection = new PDO("mysql:host=$this->dbHost;dbname=$this->dbName",$this->dbUser, $this->dbPasswd);
                $this->connection->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
                $this->connection->setAttribute(PDO::ATTR_EMULATE_PREPARES, FALSE);
            }
            catch(PDOException $e){
                $this->connection = null;
            }
        }

        public function __destruct(){
            $this->connection = null;
            static::$instance = null;
        }

        private function __clone(){
        }

    }

?>
