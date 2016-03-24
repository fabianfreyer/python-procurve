from connect import procurve
import getpass

password = getpass.getpass()
switch = procurve('switch.example.com', 'admin', password)

def mac(addr):
    'Weird format for mac addresses that the procurves use'
    onlyhex = ''.join([c for c in addr.lower() if c in '0123456789abcdef'])
    assert len(onlyhex) == 12
    return '%s-%s' % (onlyhex[0:6], onlyhex[6:12])

with switch.config as conf:
    print conf.port_security(1,
            learn_mode='static',
            mac_address=mac('00:1e:37:F0:00:0D')
            )
