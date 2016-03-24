from connect import procurve

password = getpass.getpass()
bottomup = procurve('switch.example.com', 'admin', password)

with bottomup.context('config'):
    with bottomup.context('vlan 42'):
        bottomup.cmd('untagged 1-10')
