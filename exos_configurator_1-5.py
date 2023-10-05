#!/usr/bin/env python
# 
# Created by Alex Roland
# For support, email alex.roland@peacefulnetworks.com
# or open an issue on GitHub at https://github.com/Alex-Roland/exos_configurator/issues
# 
# This script is meant to be ran directly on an EXOS switch and will build the configuration directly to memory based on answers provided in the script prompt.
# 
# Version: 1.5
# Built: 10/05/2023

import os
import sys
from exsh import clicmd

def get_ports(x):
    '''
    This function returns a formatted port string depending on the number of switches in the stack
    '''
    return {
        1: '1:1-48',
        2: '1:1-48,2:1-48',
        3: '1:1-48,2:1-48,3:1-48',
        4: '1:1-48,2:1-48,3:1-48,4:1-48',
        5: '1:1-48,2:1-48,3:1-48,4:1-48,5:1-48',
        6: '1:1-48,2:1-48,3:1-48,4:1-48,5:1-48,6:1-48',
        7: '1:1-48,2:1-48,3:1-48,4:1-48,5:1-48,6:1-48,7:1-48',
        8: '1:1-48,2:1-48,3:1-48,4:1-48,5:1-48,6:1-48,7:1-48,8:1-48',
    }.get(x, None)

def menu():
    '''
    This function provides the menu context to ask for information before building the configuration. The entered values will be displayed here in green.
    '''
    print('\n' + '-'*20 + ' MENU ' + '-'*20)
    print('1. Switch IP: \033[92m{}\033[0m'.format(switch_ip if switch_ip else ''))
    print('2. Switch Name: \033[92m{}\033[0m'.format(snmp_name if snmp_name else ''))
    print('3. Switches: \033[92m{}\033[0m'.format(str(stack_amount) if stack_amount else ''))
    print('4. Build the configuration')
    print('5. Exit')
    print(46 * "-")

switch_ip = None
snmp_name = None
stack_amount = None
done = False

# This is a dictionary of VLAN name to ID mappings
vlans = {
    'Staff': '10',
    'Student': '5',
    'AV': '15',
    'VoIP': '99',
}

while True:
    os.system('clear')
    menu()
    try:
        choice = int(raw_input('Enter your selection [1-5]: '))
    except ValueError:
        raw_input('\nPlease enter a number for selection')
        continue
    except TypeError:
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(0)
    if choice == 1:
        switch_ip = raw_input('IP: ')
        gateway_ip = '254'.join(switch_ip.rsplit(switch_ip.split('.')[3], 1))
    elif choice == 2:
        snmp_name = raw_input('Hostname: ')
    elif choice == 3:
        stack_amount = int(raw_input('Switch Quantity [1-8]: '))
        if stack_amount in range(1,9):
            edge_ports = get_ports(stack_amount)
        else:
            raw_input('\nInvalid selection...')
    elif choice == 4:
        if switch_ip and gateway_ip and snmp_name and stack_amount and edge_ports:
            print('Building configuration...this may take a couple minutes...')
            commands = [
                'configure ports 1:57,{}:57 partition 4x10G'.format(stack_amount),
                'configure ports 1:57-60,{}:57-60 auto off speed 10000 duplex full'.format(stack_amount),
                'enable sharing 1:57 grouping 1:57,{}:57 lacp'.format(stack_amount),
                'enable sharing 1:58 grouping 1:58,{}:58 lacp'.format(stack_amount),
                'enable sharing 1:59 grouping 1:59,{}:59 lacp'.format(stack_amount),
                'enable sharing 1:60 grouping 1:60,{}:60 lacp'.format(stack_amount),
                'configure vlan Default delete ports all',
                'create qosprofile "QP6"',
                'configure qosprofile QP6 maxbuffer 100 use-strict-priority',
                'configure qosprofile QP6 minbw 0 maxbw 100 ports {}'.format(edge_ports),
                'configure diffserv examination code-point 24 qosprofile QP6',
                'configure diffserv examination code-point 46 qosprofile QP6',
                'enable diffserv examination ports {}'.format(edge_ports),
                'disable dot1p examination ports all',
                'configure vlan untagged-ports auto-move inform',
                'configure cli moved-keywords show',
                'configure cli idle-timeout 240',
                'configure log target memory-buffer format timestamp hundredths date mm/dd/yyyy event-name condition severity',
                'configure log target nvram format timestamp hundredths date mm/dd/yyyy event-name condition severity',
                'configure log target console format timestamp hundredths date mm/dd/yyyy event-name condition severity',
                'configure vlan Staff add ports {} untagged'.format(edge_ports),
                'configure vlan NetMgmt ipaddress {}/23'.format(switch_ip),
                'configure iproute add default {}'.format(gateway_ip),
                'configure snmp sysContact "hostmaster@example.com, 999-888-7777"',
                'configure snmp sysName {}'.format(snmp_name),
                'configure snmp sysLocation {}'.format(snmp_name),
                'disable snmpv3 default-group',
                'enable snmp access snmpv3',
                'enable ssh2',
                'enable igmp snooping',
                'enable lldp ports all',
                'configure lldp ports all advertise all-tlvs',
                'configure lldp ports all advertise vendor-specific med capabilities',
                'configure lldp management-address vlan NetMgmt',
                'configure ntp server add pool.ntp.org vr VR-Default',
                'enable ntp vlan NetMgmt',
                'configure vlan ElrpVlan add ports all tagged',
                'configure timezone name EDT -300 autodst name EDT begins every second sunday march at 2 0 ends every first sunday november at 2 0',
                'enable tech-support collector',
                'enable loopback-mode vlan NetMgmt',
                'configure stacking slot 2 master-capability off',
                'configure stacking slot {} master-capability on'.format(stack_amount),
            ]

            for vlan in vlans:
                if vlan in clicmd('show vlan | include "^{} "'.format(vlan), capture=True):
                    continue
                else:
                    try:
                        clicmd('create vlan {} tag {}'.format(vlan, vlans[vlan]))
                        clicmd('configure vlan {} add ports 1:57-60 tagged'.format(vlan))
                    except:
                        print('\033[41mThere were issues adding VLAN {}\033[0m'.format(vlan))

            for command in commands:
                try:
                    if 'configure banner before-login save-to-configuration' in command:
                        clicmd('{}'.format(command), args='*****Unauthorized access is prohibited:  All attempts logged*****')
                    else:
                        clicmd('{}'.format(command))
                except:
                    print('\033[41mThere were errors running this command: {}\033[0m'.format(command))
                        
            clicmd('save')
            done = True
            break
        else:
            raw_input('\033[41m\nAt least one variable is not defined, make sure all variables have the correct value before proceeding\033[0m\n')
    elif choice == 5:
        sys.exit(0)
    else:
        raw_input('\nInvalid selection, please try again...')

if done:
    print('\033[92m\nConfiguration built!\033[0m\n')
    firmware = clicmd('show version | include Image', capture=True)
    if '31.7.1.4-patch1-98' in firmware:
        sys.exit(0)
    else:
        upgrade = raw_input('Would you like to upgrade firmware now? (y/N): ')
        if str(upgrade).lower() == 'y':
            print('Beginning firmware upgrade. Switch will reboot.')
            clicmd('download url file:///usr/local/ext/summit_arm-31.7.1.4-patch1-98.xos')
            clicmd('reboot')