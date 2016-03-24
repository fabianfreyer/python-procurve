from connect import procurve
import getpass

password = getpass.getpass()
switch = procurve('switch.example.com', 'admin', password)

with switch.config.vlan(42) as vlan:
    vlan.untagged('1-10')
    vlan.name('wowsuchvlan')

