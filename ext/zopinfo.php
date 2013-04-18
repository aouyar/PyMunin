<?php

# Get current date and time.
$date_now = gmdate('D, d M Y H:i:s \G\M\T');

# Send Headers
header('Content-type: text/plain');
header("Expires: " . $date_now);
header('Last-Modified: ' . $date_now);
header('Cache-Control: max-age=0, no-cache, '
        . 'must-revalidate, proxy-revalidate, '
        . 'pre-check=0, post-check=0');

if(function_exists('opcache_get_status')) {
    $zopinfo = opcache_get_status();
    unset($zopinfo['scripts']);
    echo json_encode($zopinfo);
}

?>
