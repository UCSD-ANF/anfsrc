#!/usr/bin/php
<?php

$site_files=array(
  array( "net"=>"anza", "file"=>"anza.site")
  );

parseDSSiteFile($site_files);

function parseDSSiteFile($site_files)
{
  foreach ($site_files as $sfile)
  {
    $site_content=file_get_contents($sfile["file"]);
    $site_content_line_array=explode("\n", $site_content);
    foreach ($site_content_line_array as $line)
    //$line=$site_content_line_array[0];
    {
      $temp=trim($line);
      if (empty($temp)) continue;
      
      $site=array();
      $site['net']=$sfile["net"];
      $site['sta']=trim(substr($line, 0, 8));
      $site['ondate']=trim(substr($line, 8, 9));
      $site['offdate']=trim(substr($line, 17, 7));
      $site['lat']=trim(substr($line, 24, 11));
      $site['lon']=trim(substr($line, 35, 9));
      $site['elev']=trim(substr($line, 44, 11));
      $site['staname']=trim(substr($line, 55, 50));
      var_dump($site);
    }
  }
}

?>
