flickrdownload
====

Internal ANF Tool to download flickr images for use in the TA/CEUSN web sites

Authors
-------

Staff of UC San Diego/Array Network Facility:
* Geoffrey A. Davis
* Jon C. Meyer
* Robert L. Newman
* Juan C. Reyes-Colon
* Malcolm C. White

Support
--------

This software is provided with no support or warranty.

Requirements
------------

* BRTT Antelope 5.5 through 5.8 (for the PF reading library)
* Python 2.7 (as distributed with Antelope)
* Access to the ANF station API (to retrieve a list of stations)

Non-standard Python Modules:
* pyflickr < 2.0.0

Usage
-----

Usage summary can be retrieved by running `flickrdownload -h`:

```
Usage: flickrdownload [options]

Options:
  -h, --help  show this help message and exit
  -a          get all
  -n SNET     network subset
  -v          verbose output
  -s STA      station subset
  -p PF       parameter file path
```

For example:

```sh
flickrdownload -n TA -p pf/flickrdownload_TA.pf
```

Although this program uses multiprocessing to download in parallel, it's best to wrap
the code in a `timeout` command to prevent it from running too long.

Example above with `timeout` then becomes:
```sh
timeout 6h flickrdownload -n TA -p pf/flickrdownload_TA.pf
```

You will need to configure the parameter file with real values for the following:
* `api_key`
* `api_secret`
* `token`
* `myid`
* `json_api`

See `flickrdownloads.pf` for details on these values.

Retrieving a user Token
-----------------------

Flickr started requiring a user token for downloading with the API.  The token
can be retrieved by using the command `flickrgettoken`, included with the
script.

The `myid` key
--------------

`myid` is the User ID number for the account that contains the station photos.
It can be viewed by visting:
 https://www.flickr.com/services/api/explore/?method=flickr.people.getInfo

A value of `me` will search using the ID of the user account associated with
the `api_key` and `api_secret`.
