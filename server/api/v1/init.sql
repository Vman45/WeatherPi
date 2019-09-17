DROP TABLE IF EXISTS `weather`;
DROP TABLE IF EXISTS `token`;

CREATE TABLE `weather` (
    `weather_id` INT AUTO_INCREMENT NOT NULL,
    `wind_speed` NUMERIC(3,1) NOT NULL,
    `wind_direction` INT NOT NULL,
    `wind_gust` NUMERIC(3,1) NOT NULL,
    `temperature` NUMERIC(3,1) NOT NULL,
    `rain` NUMERIC(3,1) NOT NULL,
    `humidity` INT NOT NULL,
    `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    PRIMARY KEY (`weather_id`),
    UNIQUE KEY `unique_timestamp`(`timestamp`)
);

CREATE TABLE `token`(
    `token_id` INT AUTO_INCREMENT NOT NULL,
    `token` CHAR(64) NOT NULL,

    PRIMARY KEY(`token_id`),
    UNIQUE KEY `unique_token`(`token`)
);