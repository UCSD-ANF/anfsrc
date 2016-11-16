# K. Lindquist
# Geophysical Institute
# University of Alaska, Fairbanks
# 1998

sub compass_from_azimuth {
	my( $azimuth ) = @_;

	while( $azimuth < 0. ) { $azimuth += 360.; };
	while( $azimuth > 360. ) { $azimuth -= 360.; };

	if( $azimuth >= 348.75 || $azimuth < 11.25 ) {

		return "N";		# 0.00

	} elsif( $azimuth >= 11.25 && $azimuth < 33.75 ) {

		return "NNE";		# 22.50

	} elsif( $azimuth >= 33.75 && $azimuth < 56.25 ) {

		return "NE";		# 45.00	

	} elsif( $azimuth >= 56.25 && $azimuth < 78.75 ) {

		return "ENE";		# 67.50	

	} elsif( $azimuth >= 78.75 && $azimuth < 101.25 ) {

		return "E";		# 90.00	

	} elsif( $azimuth >= 101.25 && $azimuth < 123.75 ) {

		return "ESE";		# 112.50	

	} elsif( $azimuth >= 123.75 && $azimuth < 146.25 ) {

		return "SE";		# 135.00	

	} elsif( $azimuth >= 146.25 && $azimuth < 168.75 ) {

		return "SSE";		# 157.50	

	} elsif( $azimuth >= 168.75 && $azimuth < 191.25 ) {

		return "S";		# 180.00	

	} elsif( $azimuth >= 191.25 && $azimuth < 213.75 ) {

		return "SSW";		# 202.50	

	} elsif( $azimuth >= 213.75 && $azimuth < 236.25 ) {

		return "SW";		# 225.00 	

	} elsif( $azimuth >= 236.25 && $azimuth < 258.75 ) {

		return "WSW";		# 247.50	

	} elsif( $azimuth >= 258.75 && $azimuth < 281.25 ) {

		return "W";		# 270.00	

	} elsif( $azimuth >= 281.25 && $azimuth < 303.75 ) {

		return "WNW";		# 292.50	

	} elsif( $azimuth >= 303.75 && $azimuth < 326.25 ) {

		return "NW";		# 315.00	

	} elsif( $azimuth >= 326.25 && $azimuth < 348.75 ) {

		return "NNW";		# 337.50	
	} else {

		return ""; # Faulty logic if we hit this
	}
}

1;
