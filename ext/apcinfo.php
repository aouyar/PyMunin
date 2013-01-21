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
		
if ($_GET['detail']) {
	$detail = TRUE;
}
else {
	$detail = FALSE;
}

$cache_sys = apc_cache_info('', true);
$cache_user = apc_cache_info('user', true);  
$mem = apc_sma_info(true);
$mem_detail = apc_sma_info();

foreach ($cache_sys as $key => $val) {
  printf("%s:%s:%s\n",'cache_sys', $key, $val); 
}
foreach ($cache_user as $key => $val) {
  printf("%s:%s:%s\n",'cache_user', $key, $val); 
}

$num_seg = $mem['num_seg'];
$seg_size = $mem['seg_size'];
$avail_mem = $mem['avail_mem'];
$total_mem = $num_seg * $seg_size;
$util_ratio = (float) $avail_mem / $total_mem;
$mem['total_mem'] = $total_mem;
$mem['utilization_ratio'] = 1 - $util_ratio;

if ($detail) {
	// Fragmentation: 1 - (Largest Block of Free Memory / Total Free Memory)
	$total_num_frag = 0;
	$total_frag = 0;
	$total_free = 0;
	for($i=0; $i < $num_seg; $i++) {
		$seg_free_max = 0; $seg_free_total = 0; $seg_num_frag = 0;
		foreach($mem_detail['block_lists'][$i] as $block) {
			$seg_num_frag += 1;
        	if ($block['size'] > $seg_free_max) {
				$seg_free_max = $block['size'];
			}
			$seg_free_total += $block['size'];
		}
		if ($seg_num_frag > 1) {
        	$total_num_frag += $seg_num_frag - 1;
			$total_frag += $seg_free_total - $seg_free_max;
		}
		$total_free += $seg_free_total;
	}
	$frag_ratio = ($total_free > 0) ? (float) $total_frag / $total_free : 0;
	$frag_count = $total_num_frag;
	$frag_avg_size = ($frag_count > 0) ? (float )$total_frag / $frag_count: 0;
	$mem['fragmentation_ratio'] = $frag_ratio;
	$mem['fragment_count'] = $frag_count;
	$mem['fragment_avg_size'] = $frag_avg_size;
}

foreach ($mem as $key => $val) {
  printf("%s:%s:%s\n",'memory', $key, $val); 
}


?>
