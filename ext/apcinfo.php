<?php
# __author__ = "Ali Onur Uyar"
# __copyright__ = "Copyright 2011, Ali Onur Uyar"
# __credits__ = ["Preston Mason (https://github.com/pentie)",]
# __license__ = "GPL"
# __version__ = "0.9.22"
# __maintainer__ = "Ali Onur Uyar"
# __email__ = "aouyar at gmail.com"
# __status__ = "Development"

$date_now = gmdate('D, d M Y H:i:s \G\M\T');

header('Content-type: text/plain');
header("Expires: " . $date_now);
header('Last-Modified: ' . $date_now);
header('Cache-Control: max-age=0, no-cache, '
        . 'must-revalidate, proxy-revalidate, '
        . 'pre-check=0, post-check=0');

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
