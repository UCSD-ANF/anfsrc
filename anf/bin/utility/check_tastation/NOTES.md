RavenX populates a different version OID than RV50

should be able to query RV50 OID first. If positive, poll RV50 style
else try RavenX
if positive, poll ravenx style
else, fail

Could switch to multiple OIDs in a single get PDU - V3 and V2C both support,
would cut down on the back and forth.

RavenX modem SNMPv3 implementation is NOT RFC-compliant. The net-snmp `snmpget` command uses a non-RFC "Discovery" stage and thus sidesteps the issue. However, nothing else seems to work with SNMPv3 and the RavenX.

| SNMPv3 Agent Type      | RavenX    | RV-50 |
| :---                   | ---:      | ---   |
| InterMapper            | *CRASHES* | Works |
| Perl Net::SNMP library | no result | Works |
| Python pysnmp library  | no result | Works |
| net-snmp `snmpget`     | Works     | Works |

NOTE: No relation between perl Net::SNMP and net-snmp (formerly ucd-snmp) -
Net::SNMP is a pure-Perl implementation

---

SNMPWALK examples:

    snmpwalk -m ALL -r 1 -v 3 -l authPriv -a MD5 \
      -u user -A 53805380 -x DES -X 53805380 \
      IP_ADDR


RavenX on public IP (verizon):
N4\_237B  166.161.113.31

   SNMPv2-MIB::sysDescr.0 = STRING: Raven X EV-DO


RV50 on VPN IP (verizon):
N4\_N35B  10.200.200.94

    SNMPv2-MIB::sysDescr.0 = STRING: RV50
