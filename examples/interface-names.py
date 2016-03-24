from connect import procurve
import getpass

password = getpass.getpass()
switch = procurve('switch.example.com', 'admin', password)

names = [
        'example1',
        'example2',
        'example3',
        'example4'
        ]

for port, name in enumerate(names):
    with switch.config.interface(port) as iface:
        iface.name(name)

switch.write('memory')
