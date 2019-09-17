<!DOCTYPE html>
<html lang="it" dir="ltr">
<head>
    <meta charset="utf-8">
    <title></title>
</head>
<body>
    <table border="1">
            <tr>
                <td>windSpeed</td>
                <td>windDirection</td>
                <td>windGust</td>
                <td>temperature</td>
                <td>rain</td>
                <!--<td>humidity</td>-->
                <td>timestamp</td>
            </tr>
    <?php
        require_once "Models.php";

        $ans = WeatherRecord::get(10);

        echo '';

        foreach (array_reverse($ans) as $r) {
            echo "<tr>
            <td>{$r->wind_speed}</td>
            <td>{$r->wind_direction}</td>
            <td>{$r->wind_gust}</td>
            <td>{$r->temperature}</td>
            <td>{$r->rain}</td>
            <!--<td>{$r->humidity}</td>-->
            <td>{$r->timestamp}</td>
            </tr>";
        }
    ?>
    </table>
</body>
</html>