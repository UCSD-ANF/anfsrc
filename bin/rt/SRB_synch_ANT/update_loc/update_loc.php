#!/usr/bin/php
<?php

$config_file="../config.sample";
$site_files=array(
  array( "net"=>"anza", "file"=>"anza.site", "net_prefix"=>"AZ")
  );

$config=parseConfigFile($config_file);

$sites=parseDSSiteFile($site_files);



print "\n\n--- Connecting SRB ...\n";
system("Sinit -v");
print "\n\n--- Change to ORB stream directory ...\n";
system("Scd '".$config['SRB_COLLECTION_REGISTERED_ORBS']."'");
print "\n\n--- Adding location information ...\n";
echo "trying sitename: ";
foreach ($sites as $site)
{
  echo $site['sta']."\t";
  $datanames=findORBStreamsBySite($site);
  foreach ($datanames as $dataname)
  {
     addLocation($dataname, $site);
  }
  
}
echo "\n";

print "\n\n--- All Done!!!\n";


function parseConfigFile($file)
{
  $config=array();
  $file_content=file_get_contents($file);
  $file_content_line_array=explode("\n", $file_content);
  foreach ($file_content_line_array as $line)
  {
    $line=trim($line);
    if ( (empty($line)) || 0==strncmp($line,"#",1) ) continue;
    
    $param_set=explode(" ", $line);
    if (2>count($param_set))
    {
      die ("parseConfigFile failed!\n");
    }
    else if (2<count($param_set))
    {
      $temp=implode(" ", array_slice($param_set, 1));
      $param_set[1]=$temp;
    }
    else
    {
      //parse successfully  
    }
    $config[$param_set[0]]=$param_set[1];
  }
  return $config;
}

function addLocation($data_name, $site)
{
  $loc=$site['staname'];
  $lat=$site['lat'];
  $lon=$site['lon'];
  $elev=$site['elev'];
  
  if (0!=system("Smeta -u 7 UDSMD1='$lat' $data_name")) die ("Smeta.1 failed in addLocation");
  if (0!=system("Smeta -u 8 UDSMD1='$lon' $data_name")) die ("Smeta.2 failed in addLocation");
  if (0!=system("Smeta -u 9 UDSMD1='$elev' $data_name")) die ("Smeta.3.0 failed in addLocation");
  if (0!=system("Smeta -u 9 UDSMD2='KM' $data_name")) die ("Smeta.3.1 failed in addLocation");
  if (0!=system("Smeta -u 10 UDSMD1='$loc' $data_name")) die ("Smeta.4 failed in addLocation");
}
function findORBStreamsBySite($site)
{
  $temp_file="temp.updata_loc";
  $owner=$site['net'];
  $sta=$site['sta'];
  $net_prefix=$site['net_prefix'];
  $srcname_pattern_to_search=$net_prefix."_".$sta."*";
  $status=0;
  $datanames=array();
  system("/bin/rm -f $temp_file");
  system("Sufmeta -Q ".
         "srcname like '$srcname_pattern_to_search' ".
         "2>/dev/null 1>$temp_file", $status);
  $tmp=file_get_contents($temp_file);
  if (0!=$status) 
  {
    if (strstr($tmp,"No Answer found"))
    {
      //no answer found
      return $datanames;
    }
    else
    {
      die ("FATAL: Sufmeta failed in findORBStreamsBySite\n");
    }
  }
  $tmp2=explode("\n", $tmp);
  foreach ($tmp2 as $tmp_line)
  {
    $tmp_line=trim($tmp_line);
    if ( empty($tmp_line) || strstr($tmp_line, "---") )
      continue;
    $num_match=preg_match("/^data_name: (.*)/i",$tmp_line, $matches); 
    if ($num_match<1)
      continue;
    array_push($datanames,$matches[1]);
  }
  return $datanames;  
}  

function parseDSSiteFile($site_files)
{
  $sites=array();
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
      $site['net_prefix']=$sfile["net_prefix"];
      $site['sta']=trim(substr($line, 0, 8));
      $site['ondate']=trim(substr($line, 8, 9));
      $site['offdate']=trim(substr($line, 17, 7));
      $site['lat']=trim(substr($line, 24, 11));
      $site['lon']=trim(substr($line, 35, 9));
      $site['elev']=trim(substr($line, 44, 11));
      $site['staname']=trim(substr($line, 55, 50));
      
      //over write old entry if already exists
      $match=0;
      foreach($sites as $old_site_key=>$old_site)
      {
        if(( $old_site['net']==$site['net'] )&&( $old_site['sta']==$site['sta'] ))
        {
          $match=1;
          if ($old_site['ondate'] < $site['ondate'])
            $sites[$old_site_key]=$site;
          break;  
        }
      }
      if($match==0)
        array_push($sites, $site);
    }
  }
  return $sites;
}

?>
