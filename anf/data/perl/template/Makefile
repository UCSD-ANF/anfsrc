
DATADIR= templates
DATA= xpl xpls.header xpls.footer

CLEAN  = xpl xpl.contrib xpl.nocontrib
CLEAN += xpls.header xpls.header.contrib xpls.header.nocontrib

include $(ANFMAKE)

# Override the Include rule so that templates get installed before scripts
# need them
Include :: DATA

% : %.id
	rm -f $@
	getid < $@.id > $@

xpl : xpl.nocontrib xpl.contrib
	case `getid id` in \
		5.4) cp xpl.nocontrib xpl ;; \
		* ) cp xpl.contrib xpl ;; \
		esac

xpls.header : xpls.header.nocontrib xpls.header.contrib
	case `getid id` in \
		5.4) cp xpls.header.nocontrib xpls.header ;; \
		* ) cp xpls.header.contrib xpls.header ;; \
		esac
