#!/bin/bash

# generateCertificates.sh
#
# generation of certificates for a list of geocachers
#

generate() {
    test -f Certificats/Geocaching__Bretagne__$1_white.png && return 0
    date
    for color in white black
    do
	echo Generating $1 $2 $color
	time /cygdrive/c/My\ Program\ Files/Python/python.exe generateAnimation.py \
	     -f Cote_Bretagne.gpx -f Cote_Atlantique.gpx -f Cote_Manche.gpx -f Cote_Mediterrannee.gpx -f Frontiere_Sud.gpx -f Frontiere_Est.gpx \
	     -l Geocaching_all_logs_$1.htm -c $color -g "$2" \
	     -z _Bretagne_ -x GC_Bretagne_errors.txt -p GC_Bretagne.csv \
	     2>&1 > resu_$1_$color.txt
	cp Images/Geocaching__Bretagne__$1.png Certificats/Geocaching__Bretagne__$1_$color.png
    done
    return 1
}

generate TeamCasimirdl "(TeamCasimirdl|Casimirdelyon)"
generate C2iC "(C2iC|Breizh Geocacheurs)"
generate Pepe29 "Pepe29"
generate Philfat29 "Philfat29"
generate Arlok78 "Arlok78"
generate Garenkreiz "Garenkreiz"
generate Kavadell "Kavadell"
generate Cukcelte "Cukcelte"


