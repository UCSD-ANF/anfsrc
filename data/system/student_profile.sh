#
# Automatic configuration of environment for the students.
#

function mkerr() {
    echo 1>&2
    echo "ERROR: $1" 1>&2
    echo "See your local admins or email anf-admins@ucsd.edu for further assistance."
    echo 1>&2
}
function helpMsg() {
    echo 1>&2
    echo "  Switch user environments between ANF projects." 1>&2
    echo "EXAMPLES:" 1>&2
    echo "  anfwork ANZA" 1>&2
    echo "  anfwork chile" 1>&2
    echo "  anfwork TA" 1>&2
    echo 1>&2

}
function anfworkUsage() {
    echo 1>&2
    echo "anfwork" 1>&2
    helpMsg
}
function anfwork() {
    nfshost='plinian.ucsd.edu'
    proj="$1"
    antelope=5.3


    #
    # Some needed aliases and env setup
    #
    umask 002

    alias ssh='ssh -X'
    alias ll='ls -lah'
    alias cp='cp -i'
    alias mv='mv -i'
    alias rsync="rsync -P"
    alias now='epoch now'
    alias vi='vim'
    alias du="du -kh"
    alias df="df -kTh"



    # Confirm valid input, normalize captitalization of work titles.
    case $proj in
    [Aa][Nn][Zz][Aa])
        proj='ANZA'
        #antelope=5.3  # You can overwrite the version here...
        antelopeconfig=/opt/antelope/${antelope}/setup.sh
        anfconfig=/opt/anf/${antelope}/setup.sh
    ;;
    [Cc][Hh][Ii][Ll][Ee])
        proj='chile'
        antelopeconfig=/opt/antelope/${antelope}/setup.sh
        anfconfig=/opt/anf/${antelope}/setup.sh
    ;;
    [Tt][Aa])
        proj='TA'
        antelopeconfig=/opt/antelope/${antelope}/setup.sh
        anfconfig=/opt/anf/${antelope}/setup.sh
    ;;
    *)
        mkerr "Not a valid project, ${proj}."
        anfworkUsage
        return 1
    ;;
    esac

    workdir=''
    workdirs=( /anf/${proj} /Volumes/${proj} /net/${nfshost}/export/${proj} )

    for d in ${workdirs[*]}; do
        case $d in 
        /Volumes/${proj}) 
            # check for already-mounted NFS volume, and mount if need be.
            if [ -d $d ]; then 
                workdir=$d
                break
            else
                mkdir $d && mount_nfs ${nfshost}:/export/${proj} ${d} && \
                    workdir=$d && break
            fi  
            ;;
        *)
            # ls the directory to force any automounter logic to mount it.
            ls $d >/dev/null 2>&1 
            sleep 1
            [ -d ${d} ] && workdir="$d" && break
            ;;
        esac
    done
    if [ ! -d "$workdir" ]; then
        mkerr "Cannot find valid working directory for project, '${proj}'." 
        anfworkUsage
        return 2
    fi

    # Confirm a bunch of settings once we know we can work...

    # Set our PFPATH env
    export PFPATH=${workdir}/student_pf:./pf:./

    # SET ANTELOPE ENV
    if [ -f "$anfconfig" ]; then
        # Source ANF folder. This will source Antelope internally
        #echo "Looking for Antelope version $antelope" 
        source "$anfconfig"
    elif [ -f "$antelopeconfig" ]; then
        # Source ANTELOPE directly
        #echo "Looking for Antelope version $antelope" 
        source "$antelopeconfig"
    else
        mkerr "No ANTELOPE version set on this project, '${proj}'." 
        anfworkUsage
        return 3
    fi

    if [ $ANTELOPE == "" ]; then
        mkerr "NO WORKING COPY OF ANTELOPE ON THIS COMPUTER!!!" 
        return 4
    fi

    # Print Antelope version and verify that it works
    echo
    echo "ANTELOPE: $ANTELOPE"
    if check_license; then
        echo
    else
        mkerr "NO WORKING COPY OF ANTELOPE ON THIS COMPUTER!!!" 
        return 5
    fi

    # Modify/expand work folder variable.
    workdir="${workdir}/work/${USER}"
    [ -d $workdir ] || mkdir -p $workdir

    echo -n "Changing to directory $workdir ... " 
    cd $workdir 
    if [ `pwd` == $workdir ]; then
        echo 'Success!!!'
        echo
        echo
    else
        mkerr "Cannot change to directory $workdir. for project '${proj}'." 
        return 6
    fi

    # Print little help msg...
    helpMsg
    echo

    return 0
}
function update_self() {
    #
    # Verify that we have the latest copy of the script.
    #

    # NOTE:  For now we are getting it from github.
    source="https://raw.github.com/UCSD-ANF/anfsrc/master/data/system/student_profile.sh"
    tempfile="${HOME}/student_profile.sh"
    profile="${HOME}/.profile"

    cd $HOME

    echo "Get $source"

    if curl -fSs -o $tempfile $source; then
        # With the -sSf combination curl with download
        # the file only if it is found on the server. 
        # For all other error codes it will exit and 
        # return a code > 0. The status bar will 
        # also be avoided.

        if diff $tempfile $profile; then
            echo "Using latest copy of $profile"
        else
            echo "Need to update ${profile}"

            echo "rm -f ${profile}"
            rm -f $profile

            echo "cp ${tempfile} ${profile}"
            cp $tempfile $profile

            echo "source ${profile}"
            source $profile

            # Exit now and let the new code run
            return 7

        fi

    else
        # The curl command failed. Maybe the internet is 
        # not responding. We can continue loading with 
        # the old copy. 
        echo "curl -fSs -o $tempfile $source => $?"
        echo
        mkerr "Cannot update local copy of $tempfile from ${source}. USING OLD COPY!" 
    fi

    return 0

}

# Ensure ~/.profile is up-to-date
if update_self; then
    # Migrate to ANZA workdir by default.
    anfwork ANZA
    return $?
fi

#We should never get here.
return 99
