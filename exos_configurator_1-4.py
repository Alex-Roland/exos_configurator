#!/usr/bin/env python
# 
# Created by Alex Roland
# For support, email alex.roland@peacefulnetworks.com
# or open an issue on GitHub at https://github.com/Alex-Roland/exos_configurator/issues
# 
# This script is meant to be ran directly on an EXOS switch and will build the configuration directly to memory based on answers provided in the script prompt.
# 
# Version: 1.4
# Built: 05/26/2022

import os
import random
import string
import sys
from crypt import crypt
from exsh import clicmd

def get_severity(x):
    '''
    This function returns the severity level to set for logging
    '''
    return {
        2: 'critical',
        3: 'error',
        4: 'warning',
        5: 'notice',
        6: 'info',
        7: 'debug-summary',
    }.get(x, 'info')

def hash_password():
    '''
    This function returns a hashed password with the correct salt size for EXOS
    '''
    salt = ''.join(random.choice(string.lowercase) for _ in range(6))
    return crypt(raw_input('Admin password: '), '$5${}'.format(salt))

def get_ports(edge_ports, x):
    '''
    This function returns a formatted port string depending on the number of switches in the stack
    '''
    return {
        1: '1-{0}'.format(edge_ports),
        2: '1:1-{0},2:1-{0}'.format(edge_ports),
        3: '1:1-{0},2:1-{0},3:1-{0}'.format(edge_ports),
        4: '1:1-{0},2:1-{0},3:1-{0},4:1-{0}'.format(edge_ports),
        5: '1:1-{0},2:1-{0},3:1-{0},4:1-{0},5:1-{0}'.format(edge_ports),
        6: '1:1-{0},2:1-{0},3:1-{0},4:1-{0},5:1-{0},6:1-{0}'.format(edge_ports),
        7: '1:1-{0},2:1-{0},3:1-{0},4:1-{0},5:1-{0},6:1-{0},7:1-{0}'.format(edge_ports),
        8: '1:1-{0},2:1-{0},3:1-{0},4:1-{0},5:1-{0},6:1-{0},7:1-{0},8:1-{0}'.format(edge_ports),
    }.get(x, '1-48')

def get_vlans():
    '''
    This function returns a dictionary of VLAN name to ID mappings
    '''
    selection = raw_input('Do you want the default VLAN set? (y/N): ')
    if selection.lower() == 'y':
        return {
            # You can define a default VLAN set here if you don't want to have to keep entering values when running this script. Examples are below:
            'Staff': '10',
            'Student': '5',
            'AV': '15',
            'VoIP': '99',
        }
    elif selection.lower() == 'n' or selection == '':
        vlans = {}
        while True:
            vlan = raw_input('VLAN name and ID (q = quit): ')
            if vlan.lower() == 'q':
                break
            if ' ' not in vlan:
                raw_input('Please enter the VLAN name and ID separated by a space, example: NIMM 172')
                continue
            vlans.update(vlan.split() for _ in vlan.split())
        return vlans
    else:
        raw_input('\nInvalid selection, please try again...')

def menu():
    '''
    This function provides the menu context to ask for information before building the configuration. The entered values will be displayed here in green.
    '''
    print('\n' + '-'*20 + ' MENU ' + '-'*20)
    print('1.  Switch IP: \033[92m{}{}\033[0m'.format('\n\tIP: ' + switch_ip if switch_ip else '', '\n\tGateway: ' + gateway_ip if gateway_ip else ''))
    print('2.  SNMP: \033[92m{}{}{}{}\033[0m'.format('\n\tAuth: ' + snmp_auth if snmp_auth else '', '\n\tPriv: ' + snmp_priv if snmp_priv else '', '\n\tName: ' + snmp_name if snmp_name else '', '\n\tLocation: ' + snmp_location if snmp_location else ''))
    print('3.  Syslog: \033[92m{}{}{}\033[0m'.format('\n\tSyslog IP: ' + syslog_ip if syslog_ip else '', '\n\tFacility: ' + facility if facility and syslog_ip else '', '\n\tSeverity: ' + severity if severity and syslog_ip else ''))
    print('4.  RADIUS: \033[92m{}{}\033[0m'.format('\n\tPrimary: ' + radius_primary if radius_primary else '', '\n\tSecondary: ' + radius_secondary if radius_secondary else ''))
    print('5.  RADIUS Secret: \033[92m{}\033[0m'.format('\n\t' + radius_secret if radius_secret else ''))
    print('6.  Admin password: \033[92m{}\033[0m'.format('\n\t******' if admin_password else ''))
    print('7.  Switches: \033[92m{}{}\033[0m'.format('\n\tQty: ' + str(stack_amount) if stack_amount else '', '\n\tPorts: ' + ports if ports else ''))
    print('8.  Uplink port(s): \033[92m{}\033[0m'.format('\n\t' + str(uplink) if uplink else ''))
    print('9.  VLANs:')
    if vlans:
        for vlan in vlans:
            print('\033[92m\t{}\t{}\033[0m'.format(vlan, vlans[vlan]))
    print('10. Build the configuration')
    print('11. Report issues')
    print('12. Exit')
    print(46 * "-")

def report_issues():
    '''
    This function displays the report issues tip
    '''
    os.system('clear')
    print('To report an issue, please use the GitHub repo issues page located at:')
    print('\033[4;94mhttps://github.com/Alex-Roland/exos_configurator/issues\033[0m')
    print('\nIf you get a traceback error, please include it in the issue report.')
    print('A traceback error looks something like this:\n')
    print('''\033[93mTraceback (most recent call last):
  File "<pyshell#46>", line 1, in <module>
    primary_uplink = int(uplink.split(',')[0])
ValueError: invalid literal for int() with base 10: '1:52'\033[0m
    ''')
    raw_input('Press enter to continue...')

switch_ip = None
gateway_ip = None
snmp_auth = None
snmp_priv = None
snmp_name = None
snmp_location = None
syslog_ip = None
facility = 'local4'
severity = get_severity(6)
radius_primary = None
radius_secondary = None
radius_secret = None
admin_password = None
stack_amount = None
ports = None
edge_ports = None
uplink = None
is_stack = None
vlans = {}
copper_uplink = False
done = False

ips = {
    'radius_pri': '10.0.0.1',
    'radius_sec': '10.0.0.2',
    'syslog_pri': '10.0.0.3',
    'syslog_sec': '10.0.0.4',
}

try:
    os.system('clear')
    acknowlegement = raw_input('\nAre you configuring a stack consisting of more than one switch? (y/N): ')
    if str(acknowlegement).lower() == 'y':
        verification = raw_input('Did you already run "enable stacking" on the primary member? (y/N): ')    
        if str(verification).lower() == 'y':
            is_stack = True
        else:
            stacking = raw_input('Would you like to run "enable stacking" now? This will reboot the switch! (y/N): ')
            if str(stacking).lower() == 'y':
                print('Enabling stacking support...please wait...')
                clicmd('enable stacking')
                sys.exit(0)
            else:
                print('Please enable stacking first before running this script')
                sys.exit(0)
    elif str(acknowlegement).lower() == 'n' or acknowlegement == '':
        pass
    else:
        print('Exiting...')
        sys.exit(0)
except TypeError:
    sys.exit(0)
except KeyboardInterrupt:
    sys.exit(0)

while True:
    os.system('clear')
    menu()
    try:
        choice = int(raw_input('Enter your selection [1-12]: '))
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
        snmp_auth = raw_input('Auth: ')
        snmp_priv = raw_input('Priv: ')
        snmp_name = raw_input('Hostname: ')
        snmp_location = raw_input('Location: ')
        if 'hmd' in snmp_name.lower():
            syslog_ip = ips['syslog_pri']
            radius_primary = ips['radius_pri']
            radius_secondary = ips['radius_sec']
        elif 'wst' in snmp_name.lower():
            syslog_ip = ips['syslog_sec']
            radius_primary = ips['radius_sec']
            radius_secondary = ips['radius_pri']
        else:
            raw_input('Unable to determine location based IPs\nMust have "pri" or "sec" in the hostname')
    elif choice == 3:
        syslog_ip = raw_input('Syslog IP: ')
        facility = raw_input('Facility: ')
        severity = get_severity(int(raw_input('Severity [2-7]: ')))
    elif choice == 4:
        radius_primary = raw_input('Primary: ')
        radius_secondary = raw_input('Secondary: ')
    elif choice == 5:
        radius_secret = raw_input('Secret: ')
    elif choice == 6:
        admin_password = hash_password()
    elif choice == 7:
        stack_amount = int(raw_input('Switch Quantity [1-8]: '))
        if stack_amount in range(1,9):
            if is_stack and stack_amount == 1:
                raw_input('Stack amount cannot be 1 if you acknowledged there is more than one switch')
                stack_amount = None
                continue
            elif not is_stack and stack_amount > 1:
                raw_input('Stack amount cannot be more than 1 if you acknowledged there is only one switch')
                stack_amount = None
                continue
            edge_ports = int(raw_input('Edge ports per switch [12, 24, or 48]: '))
            if edge_ports != 12 and edge_ports != 24 and edge_ports != 48:
                raw_input('\nInvalid selection...')
                stack_amount = None
                edge_ports = None
                continue
            ports = get_ports(edge_ports, stack_amount)
        else:
            raw_input('\nInvalid selection...')
    elif choice == 8:
        uplink = str(raw_input('Uplink port(s): '))
        if stack_amount > 1 and ':' not in uplink:
            raw_input('\nSince there is more than one switch in the stack, please input the uplink with the colon format\n\ti.e: 1:48')
            uplink = None
            continue
        elif stack_amount == 1 and ':' in uplink:
            uplink = int(uplink.split(':')[1])
            if uplink < 49:
                copper_uplink = True
            else:
                copper_uplink = False
        elif stack_amount == 1 and ':' not in uplink:
            if int(uplink) < 49:
                copper_uplink = True
            else:
                copper_uplink = False
        elif stack_amount > 1 and ',' in uplink:
            primary_uplink = uplink.split(',')[0]
            secondary_uplink = uplink.split(',')[1]
            if int(primary_uplink.split(':')[1]) < 49 or int(secondary_uplink.split(':')[1]) < 49:
                copper_uplink = True
            else:
                copper_uplink = False
        elif stack_amount > 1 and ',' not in uplink:
            if int(uplink.split(':')[1]) < 49:
                copper_uplink = True
            else:
                copper_uplink = False
    elif choice == 9:
        vlans = get_vlans()
    elif choice == 10:
        if switch_ip and gateway_ip and snmp_auth and snmp_priv and snmp_name and snmp_location and syslog_ip and radius_primary and radius_secondary and facility and severity and radius_secret and admin_password and stack_amount and ports and edge_ports and uplink:
            print('Building configuration...this may take a couple minutes...')
            commands = [
                'configure Default delete ports all',
                'configure vlan NetMgmt ipaddress {} 255.255.255.0'.format(switch_ip),
                'configure iproute add default {}'.format(gateway_ip),
                'configure snmp sysContact hostmaster@example.com',
                'configure snmp sysName {}'.format(snmp_name.lower()),
                'configure snmp sysLocation {}'.format(snmp_location.lower()),
                'configure snmpv3 add user snmpuser authentication md5 {} privacy des {}'.format(snmp_auth, snmp_priv),
                'configure snmpv3 add group public user snmpuser sec-model usm',
                'configure snmpv3 add access public sec-model usm sec-level priv read-view "defaultAdminView" write-view "defaultAdminView" notify-view "defaultAdminView"',
                'enable snmp access snmpv3',
                'enable ssh2',
                'disable telnet',
                'disable web http',
                'enable igmp snooping',
                'configure ports {} rate-limit flood broadcast 500'.format(ports),
                'create stpd s1',
                'disable s0 auto-bind Default',
                'configure mstp revision 3',
                'configure stpd s1 mode mstp msti 1',
                'enable s1 auto-bind vlan 1-4094',
                'enable stpd s1',
                'enable mac-locking',
                'enable mac-locking ports {}'.format(ports),
                'configure mac-locking ports {} first-arrival limit-learning 8'.format(ports),
                'configure stpd s0 ports link-type edge {} edge-safeguard enable bpdu-restrict'.format(ports),
                'configure stpd s1 ports link-type edge {} edge-safeguard enable bpdu-restrict'.format(ports),
                'create vlan nt_login',
                'enable policy',
                'enable netlogin mac',
                'configure netlogin mac authentication database-order radius',
                'configure netlogin add mac-list ff:ff:ff:ff:ff:ff 48',
                'configure netlogin mac timers reauth-period 3600',
                'enable netlogin ports {} mac'.format(ports),
                'enable lldp port all',
                'configure vlan VoIP add ports {} tagged'.format(ports),
                'configure lldp ports {} advertise port-description'.format(ports),
                'configure lldp ports {} advertise system-capabilities'.format(ports),
                'configure lldp ports {} advertise management-address'.format(ports),
                'configure lldp ports {} advertise vendor-specific dot3 power-via-mdi'.format(ports),
                'configure lldp ports {} advertise vendor-specific med capabilities'.format(ports),
                'configure sntp-client primary 10.1.1.1',
                'configure sntp-client secondary 10.1.1.2',
                'enable sntp-client',
                'configure timezone name CST -360 autodst name CDT begins every second sunday march at 2 0 ends every first sunday november at 2 0',
                'configure syslog {} vr VR-Default {}'.format(syslog_ip, facility),
                'configure syslog {} vr VR-Default {} severity {}'.format(syslog_ip, facility, severity),
                'enable log target syslog {} vr VR-Default {}'.format(syslog_ip, facility),
                'configure radius mgmt-access 3 server {} 1812 client-ip {} vr VR-Default'.format(radius_primary, switch_ip),
                'configure radius mgmt-access 4 server {} 1812 client-ip {} vr VR-Default'.format(radius_secondary, switch_ip),
                'configure radius 3 shared-secret {}'.format(radius_secret),
                'configure radius 4 shared-secret {}'.format(radius_secret),
                'enable radius mgmt-access',
                'configure account admin encrypted {}'.format(admin_password),
            ]
            uplink_commands = [
                'configure ports {} rate-limit flood broadcast no-limit'.format(uplink),
                'disable mac-locking ports {}'.format(uplink),
                'configure mac-locking ports {} first-arrival limit-learning 600'.format(uplink),
                'configure stpd s0 ports link-type auto {}'.format(uplink),
                'configure stpd s0 ports edge-safeguard disable {}'.format(uplink),
                'configure stpd s0 ports bpdu-restrict disable {}'.format(uplink),
                'configure stpd s1 ports link-type auto {}'.format(uplink),
                'configure stpd s1 ports edge-safeguard disable {}'.format(uplink),
                'configure stpd s1 ports bpdu-restrict disable {}'.format(uplink),
                'disable netlogin ports {} mac'.format(uplink),
                'unconfigure lldp ports {}'.format(uplink),
            ]

            try:
                if 'user' in clicmd('show accounts', True):
                    clicmd('delete account user')
            except:
                print('\033[41mThere were errors deleting the user account\033[0m')

            for vlan in vlans:
                if vlan in clicmd('show vlan | include ^{}'.format(vlan), True):
                    continue
                else:
                    try:
                        clicmd('create vlan {} tag {}'.format(vlan, vlans[vlan]))
                        clicmd('configure vlan {} add ports {} tagged'.format(vlan, uplink))
                    except:
                        print('\033[41mThere were issues adding VLAN {}\033[0m'.format(vlan))

            for command in commands:
                try:
                    clicmd('{}'.format(command))
                except:
                    print('\033[41mThere were errors running this command: {}\033[0m'.format(command))

            if copper_uplink:
                for command in uplink_commands:
                    try:
                        clicmd('{}'.format(command))
                    except:
                        print('\033[41mThere were errors running this command: {}\033[0m'.format(command))
            clicmd('save')
            done = True
            break
        else:
            raw_input('\033[41m\nAt least one variable is not defined, make sure all variables have the correct value before proceeding\033[0m\n')
    elif choice == 11:
        report_issues()
    elif choice == 12:
        sys.exit(0)
    else:
        raw_input('\nInvalid selection, please try again...')

if done:
    print('\033[92m\nConfiguration built\033[0m')