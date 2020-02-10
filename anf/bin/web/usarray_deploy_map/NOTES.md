Development Notes for usarray\_deploy\_map
====

Creating a test database
----

The script appears to need the following tables:
* deployment
* site
* sitechan
* sensor

Other semi-frequently used tables for a dbmaster:
* snetsta
* comm

Command to get a fresh working database:

```bash
for table in site deployment sitechan snetsta comm sensor; do \
    dbcp -v /anf/TA/rt/usarray/usarray-web.$table deploymaptest; done
tar zcf deploymaptest.tgz deploymaptest*
```
