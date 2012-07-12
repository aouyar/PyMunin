<?php
# __author__ = "Ali Onur Uyar"
# __copyright__ = "Copyright 2011, Ali Onur Uyar"
# __credits__ = []
# __license__ = "GPL"
# __version__ = "0.9"
# __maintainer__ = "Ali Onur Uyar"
# __email__ = "aouyar at gmail.com"
# __status__ = "Development"

header("Content-type: text/plain");

$cache_sys = apc_cache_info('', true);
$cache_user = apc_cache_info('user', true);  
$memory = apc_sma_info(true);

foreach ($cache_sys as $key => $val) {
  printf("%s:%s:%s\n",'cache_sys', $key, $val); 
}
foreach ($cache_user as $key => $val) {
  printf("%s:%s:%s\n",'cache_user', $key, $val); 
}
foreach ($memory as $key => $val) {
  printf("%s:%s:%s\n",'memory', $key, $val); 
}

?>
