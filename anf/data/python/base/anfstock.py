#
# Some generic Python function
# to make database operations easy
# to implement and speed up the
# development process.
#
# Juan Reye
# reyes@ucsd.edu
#

if __name__ == "__main__":
    raise ImportError( "\n\n\tANF Python library. Not to run directly!!!! \n" )

import sys
import logging_helper
import inspect

try:
    import antelope.stock as stock
    import antelope.datascope as datascope
except Exception,e:
    raise ImportError("[%s] Do you have Antelope installed?" % e)

def find_executables( execs ):
    '''
    Let's find some execs on the system and
    keep the full path on a variable.
    This is to avoid problems with some of
    the scripts that we need to run with
    Dreger's original code.
    '''

    if not len(execs): return

    executables = {}

    for ex in execs:
        logging.debug("Find executable for (%s)" % ex)

        newex = spawn.find_executable(ex)

        if not newex:
            logging.error("Cannot locate executable for [%s] in $PATH = \n%s" % \
                    (ex,os.environ["PATH"].split(os.pathsep)) )

        executables[ex] = os.path.abspath( newex )

        logging.debug("(%s) => [%s]" % (ex, newex) )

    return executables

def run(cmd,directory='.'):
    logging.debug("run()  -  Running: %s" % cmd)
    p = subprocess.Popen([cmd], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         cwd=directory, shell=True)
    stdout, stderr = p.communicate()

    if stdout:
        for line in iter(stdout.split('\n')):
            logging.debug('stdout:\t%s'  % line)
    if stderr:
        for line in iter(stderr.split('\n')):
            logging.debug('stderr:\t%s'  % line)

    if p.returncode != 0:
        logging.error('Exitcode (%s) on [%s]' % (p.returncode,cmd))

    if stdout:
        return iter(stdout.split('\n'))
    if stderr:
        return iter(stderr.split('\n'))
    return iter()


def eval_null( value, null_value):
    '''
    Evaluate if our value matches the NULL representation of that field.


    '''
    # Try int value
    try:
        if int(float(value)) == int(float(null_value)):
            return True
    except:
        pass

    # Now test string representation
    try:
        if str(value) == str(null_value):
            return True
    except:
        pass

    return False
