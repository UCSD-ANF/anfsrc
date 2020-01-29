"""Main function wrapper for poc2mongo"""
import sys

from poc2mongo.main import main

if __name__ == '__main__':
    sys.exit(main(sys.argv))
