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
header("Cache-Control: no-store, no-cache, must-revalidate");  // HTTP/1.1
header("Cache-Control: post-check=0, pre-check=0", false);
header("Pragma: no-cache");                                    // HTTP/1.0

$cache_sys = apc_cache_info('', true);
$cache_user = apc_cache_info('user', true);  
$mem_limited = apc_sma_info(true);
$mem = apc_sma_info();

foreach ($cache_sys as $key => $val) {
  printf("%s:%s:%s\n",'cache_sys', $key, $val); 
}
foreach ($cache_user as $key => $val) {
  printf("%s:%s:%s\n",'cache_user', $key, $val); 
}
foreach ($mem_limited as $key => $val) {
  printf("%s:%s:%s\n",'memory', $key, $val); 
}

// Fragementation: (freeseg - 1) / total_seg
$nseg = $freeseg = $fragsize = $freetotal = 0;
for($i=0; $i<$mem['num_seg']; $i++) {
        $ptr = 0;
        foreach($mem['block_lists'][$i] as $block) {
                if ($block['offset'] != $ptr) {
                        ++$nseg;
                }
                $ptr = $block['offset'] + $block['size'];
                /* Only consider blocks <5M for the fragmentation % */
                if($block['size']<(5*1024*1024)) $fragsize+=$block['size'];
                $freetotal+=$block['size'];
        }
        $freeseg += count($mem['block_lists'][$i]);
}

$frag = $freeseg > 1 ? $fragsize/$freetotal : 0;

printf("%s:%s:%s\n",'memory', 'fragmented', $fragsize); 
printf("%s:%s:%f\n",'memory', 'fragment_percentage', $frag * 100); 


?>
