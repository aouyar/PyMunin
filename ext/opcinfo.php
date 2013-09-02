<?php

# Get current date and time.
$date_now = gmdate('D, d M Y H:i:s \G\M\T');

# Send Headers
header('Content-Type: application/json');
header("Expires: " . $date_now);
header('Last-Modified: ' . $date_now);
header('Cache-Control: max-age=0, no-cache, '
        . 'must-revalidate, proxy-revalidate, '
        . 'pre-check=0, post-check=0');

if(function_exists('opcache_get_status')) {
    $opcinfo = opcache_get_status();
    unset($opcinfo['scripts']);
    echo json_encode($opcinfo);
}

?>
