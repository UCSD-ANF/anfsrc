<HTML>
<HEAD>
<TITLE>ROADNet Network Status</Title>
</HEAD>
<BODY>


<table border="0" cellpadding="0" cellspacing="0" width="800"><TR><TD colspan="7"><IMG SRC="http://roadnet.ucsd.edu/images/raodnet_r1_c1.jpg" WIDTH="800"></TD></TR><TR><TD height="18"><img src="header.jpg" width="503" height="29" border="0"></td><td colspan="-1" height="18"><img name="roadnetma_r5_c5" src="roadnet-ma_r5_c5.jpg" width="248" height="29" border="0"><A HREF="http://roadnet.ucsd.edu"><IMG SRC="roadnet-ma_r5_c7.jpg" WIDTH="49" HEIGHT="29" BORDER="0"></A></td><td height="18">&nbsp;</td></tr> <tr> <td colspan="4" height="2">&nbsp;</td></tr> </table>

<BR>
<BR>
<BR>

<?php 
	/* our constants in the program:
	 * STATUS_FILE - the Nagios host status file
 	 * OBJECTS_FILE - the Nagios objects file (Our host information file)
	 * SERVICE - The service we are looking for in the status file
 	 * UP_IMG - The image that means an up status for a host
	 * DN_IMG - The image that means a down status for a host
	 */
	define( STATUS_FILE, "/export/nagios2/var/status.dat");
	define( OBJECTS_FILE, "/export/nagios2/var/objects.cache" );
	define( SERVICE, "PING stats");
	define( UP_IMG, "http://stat.hpwren.ucsd.edu/green.gif" );
	define( DN_IMG, "http://stat.hpwren.ucsd.edu/red.gif" );

	$hostGroup = $_GET['host'];

	echo "Current time: ".strftime( "%A, %B %d %Y at %T %Z", time() )."<BR><BR>"; 

	if( $hostGroup == "" ){

		$hosts = read_Hosts( OBJECTS_FILE, &$output, $hostGroup);

		usage( $hosts );
		
	}
	else{
	

		$hosts = read_Hosts( OBJECTS_FILE, &$output, $hostGroup );

		$status = read_Status( STATUS_FILE, &$output, $hosts );

		make_Table( $output, $status );	

	}
?>

<?php 
	/* 
	 * Function Name: read_Hosts
	 * Description: Opens the File designated by $File, and reads in the
	 * 		host names of the group specified by $hostGroup into
	 * 		a hash. The descriptions of each host is also entered
	 * 		into the output hash for later display. Note: $output
	 * 	  	is passed by reference from the calling function
 	 * 
	 * Parameters: $File - the File to open to read from 
	 *		       (i.e. objects.cache)
	 *	       $output - the array to store the host information in
	 * 	       $hostGroup - the host group to look for in objects.cache
 	 *
	 * Return Value: A hash of names of hosts in the specified group
	 */
	function read_Hosts( $File, $output, $hostGroup ){

		$hosts_FH = fopen($File,"r");

		while( !feof( $hosts_FH ) ){

			$line = fgets( $hosts_FH );
	
			if( $hostGroup == "" ){

				if( $line == "define hostgroup {\n" ){

					$line = fgets( $hosts_FH );

					$hosts = substr( trim( $line, "\n" ), 16 );

					$hostAsoc[$hosts] = "<A HREF=\"status.php?host=$hosts\"> $hosts - " ;

					$line = fgets( $hosts_FH );

					$descrip = substr( trim( $line, "\n" ), 7 );

					$hostAsoc[$hosts] .= "$descrip</A><BR>";
		
				}

			}

			else if( $line == "\thostgroup_name\t$hostGroup\n" ){
			
				$line = fgets( $hosts_FH );

				$line = fgets( $hosts_FH );

				$hosts = substr( trim( $line, "\n" ), 9 );
					
				$hostArr = explode( "," , $hosts );

				foreach ( $hostArr as $host ){

					$hostAsoc[$host] = 0;

					$output[$host] = "<B>Host Name</B>: $host<BR>";

				}	

				$descriptions = 1;
			}

			if( $descriptions ){

				if( $line == "define host {\n" ){

					$line = fgets( $hosts_FH );
			
					$name = substr( trim( $line, "\n" ), 11 );
			
					if( array_key_exists( $name, $hostAsoc ) ){

						$line = fgets( $hosts_FH );

						$descrip = substr( trim( $line, "\n" ), 7 );

						$output[$name] .= "<B>Description</B>: $descrip<BR>";

					}
				}

			} 

			

		}

		fclose( $hosts_FH );
		
		return $hostAsoc;

	}

?>

<?php

	function read_Status( $File, $output, $hosts ){

		$status_FH = fopen($File, "r" );

		while( !feof( $status_FH ) ){

			

			$line = fgets( $status_FH );

			if( $line == "service {\n" ){

				$line = fgets( $status_FH );		
			
				$host = explode( "=", trim( $line, "\n" ) );

				if( array_key_exists( $host[1], $hosts ) ){
				
					$line = fgets( $status_FH );

					$type = explode( "=", trim( $line, "\n" ) );

					if( $type[1] == "PING stats"){

						while( $i < 9 ){

							$line = fgets( $status_FH );

							$i++;
						
						}

						$lastHard = explode( "=", trim( $line, "\n" ) );

						$i = 0;
									
						while( $i < 5 ){

							$line = fgets( $status_FH );

							$i++;

						}

						$i = 0;

						$lastTime = explode( "=", trim( $line, "\n") );
	
	
						if( $lastHard[1] == "0" ){

							$status[$host[1]] = UP_IMG;
							$time = strftime( "%A, %B %d %Y at %T", $lastTime[1] );
							$output[$host[1]] .= "<B>Status</B>: $host[1] is <B><I>online</I></B> <BR><B>since</B>: $time\n";
						}

						else{

							$status[$host[1]] = DN_IMG;
							$time = strftime( "%A, %B %d %Y at %T", $lastTime[1] );
							$output[$host[1]] .= "<B>Status</B>: $host[1] is <B><I>offline</I></B><BR><B>since</B>: $time\n";
						}
					}
				}
			}
		}




		fclose( $status_FH );

		return $status;		

	}

?>		

								
<?php 

	/*
	 * Function Name: make_Table
	 * Description: Creates an HTML table outputting the the two strings 
	 * 		at each key in the array to adject cells in the table.
 	 * 		Note: the $status array holds just a string that is the 
 	 *		URL for the proper up/image for the host, and not the 
	 * 		actual image.
	 * 
 	 * Parameters: $output: array of strings that describes the host, its 
	 *			status, and time the host has been in that 
	 *			state.
	 *  	       $status: array of strings that URL's pointing to the 
	 * 			proper image for each host.
	 * 
 	 * Return Value: None.
	 */
	function make_Table( $output, $status )
	{

		$i = 0;

		// 3 Here is arbitrary
		$num_Cols = 3;
		
		echo "<Table border=\"1\" cellspacing=\"4\">\n";

		echo "<TR>\n";

		foreach ( $output as $key => $value){

			echo "<TD>\n<IMG SRC=\"".
					$status[$key].
					"\"></IMG>\n</TD>\n";

			echo "<TD>\n<P>".
					$output[$key]
					."</P>\n</TD>\n";
	
			if( $i % $num_Cols == $num_Cols-1 ){	
				
				echo "</TR>\n";
			
				echo "<TR>\n";
			}	

			$i++;
		}

		echo "</table>\n";

	}
	

?>

<?php 

	function usage( $hosts )
	{
	
		echo "<P>Usage: status.php?host=&lt hostgroup &gt<BR>
			where hostgroup is the name of the Nagios
			host group you would like to display.<BR>
			This script will display the statues for 
			every host in the hostgroup.</P>";
		echo "<P>Each of the following hostgroups are valid and
			available for display:</P>";

		echo "<BR><P>";

		foreach( $hosts as $v ){

			echo $v;
			echo "<BR>";

		}

		echo "</P>\n";


	}

?>


<BR>
<BR>
<BR>
<BR>

<table border="0" cellpadding="0" cellspacing="0" width"728" height"4%">
<TR> <TD><img name="subhead_r14_c1" src="http://roadnet.ucsd.edu/images/subhead_r14_c1.jpg" width="800" height="27" border="0" alt=""></TD></TR></table>


</BODY>
</HTML>
