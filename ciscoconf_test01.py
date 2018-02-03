import os
import argparse
import paramiko
import getpass
import socket
import re
import sys
import time

'''***** Get command line arguments, set global variables, and define supportive functions *****'''
# Define command line arguments and globals

def args():
		parser = argparse.ArgumentParser(description='Python program to search through switches ' 'and autoconfigure ports.')
		parser.add_argument('-f', '--hosts', help='Specifiy a hosts file', required=True)
		parser.add_argument('-a', '--access', help='Enter Access Vlan Value -- ' '(default = 1)', default='1')
		parser.add_argument('-w', '--wireless', help='Enter Wireless vlan value' '(default = 1)', default='1')
		parser.add_argument('-v', '--voice', help='Enter Voice vlan value --' '(default = 1)', default='1')
		
		arg = vars(parser.parse_args())
		
		global main_menu_actions, sub_menu_actions, config_menu_actions, hosts_file, \
		 network_devices, int_sts, access_list, ap_list, trunk_list, starts_items, \
		 access_vlan, ap_vlan, voice_vlan
		 
		 network_devices = {}
		 int_sts = {}
		 start_items = ('Te', 'Po')
		 hosts_file = arg['hosts']
		 access_vlan = arg['access']
		 ap_vlan = arg['wireless']
		 voice_vlan = arg['voice']
		 
		 main_menu_actions = {
			'main_menu': main_menu,
			'1': sh_host_list,
			'2': select_vlans,
			'3': connect,
			'0': prog_exit}
		
		sub_menu_actions = {
			'cmd_outputs': sh_cmd_outputs,
			'1': sh_cdp,
			'2': sh_int_sts,
			'3': sh_err_dis,
			'4': in_cdp_and_int,
			'5': in_int_not_cdp,
			'6': sh_config_outputs,
			'7': get_int_and_cdp,
			'9': main_menu}
		
		config_menu_actions = {
			'config_outputs': sh_config_outputs,
			'1': config_cdp,
			'2': config_non_cdp,
			'3': config_err_dis,
			'4': man_config_port,
			'9': sh_cmd_outputs}
		
		access_list = [
			'switchport mode access',
			'switchport access vlan %s' % access_vlan,
			'switchport voice vlan %s' % voice_vlan,
			'switchport port-security',
			'switchport port-security maximum 3',
			'switchport port-security aging time 1',
			'switchport port-security violation restrict',
			'spanning-tree portfast',
			'auto qos voip cisco-phone',
			'no shut']
		
		ap_list = [
			'description AP',
			'switchport mode access',
			'switchport access vlan 90',
			'shut',
			'no shut']
		
		trunk_list = [
			'description SWITCH'
			'switchport trunk encapsulation dot1q',
			'switchport mode trunk',
			'auto qos trust dscp',
			'spanning-tree link-type point-to-point',
			'no shut']

# Default interface

def default_list(item):
	print '\t*** Defaulting the Interface *** \n'
	remote_conn.send('conf t\n')
	remote_conn.send('default interface %s \n' % item)
	time.sleep(1)
	remote_conn.send('interface %s \n' % item)
	time.sleep(.5)

# Send commands to end and write mem

def end_write():
	remote_conn.send('end\n')
	remote_conn.send('write mem\n')
	
# Natural sorter

def sortkey_natural(s):
 return tuple(int(part) if re.match(r'[0-9]+$', part) 
						else part
							for part in re.split(r'([0-9]+)', s))

# Clear screen

def clear_screen():
	os.system('cls' if os.name == 'nt' else 'clear')
	
# Press to return

def press_return():
	print '\n\n(Make sure to resync the device to see any conf changes)'
	print '\n\nPress enter to go back\n'
	raw_input(' >> ')
	
#Menu choice validator

def exec_menu(menu_actions, menu_return, choice):
	clear_screen()
	try:
		menu_actions[choice]()
	except KeyError:
		print 'Invalid Selection, Please try again.\n'
		time.sleep(1)
		menu_return()
		
# Exit commands

def prog_exit():
	if os.path.isfile('cdp') is True: os.remove('cdp')
	if os.path.isfile('int') is True: os.remove('int')
	sys.exit()
	
'''********Main menu and associated functions ********'''

#Printed main menu
def main_menu():
	clear_screen()
	menu_actions = main_menu_actions
	menu_return = main_menu
	print '\n\n'
	print '\t* * * * * * * * * * * * * * * * * * * * * * * * * * * * *
	print '\t
	print '\t  Bienvenido !
	print '\t
	print '\t
	print '\t* * * * * * * * * * * * * * * * * * * * * * * * * * * * *
	print '\n\n\tPlease choose an option from the following:\n\n'
	print '\t\t1. Show IP address in list file\n'
	print '\t\t2. Show current vlan settings\n'
	print '\t\t3. Connect to device (or next device in list)'
	print '\n\n\t\t0. Quit'
	choice = raw_input('\n\n >> ')
	exec_menu(menu_actions, menu_return, choice)
	return
	
# Print IP address list

def sh_host_list():
	hosts = open(host_file, 'r')
	print '\n\n\tHosts in file: \n'
	for x in hosts:
		print '\t\t' + x.strip('\n')
	print '\n\n'
	hosts.close()
	press_return()
	main_menu()
	
# Choose vlans if other than default

def select_vlans():
	print '\n\n\t Current vlan settings are: '
	print '\n\n\t Access vlan: ' + access_vlan
	print '\n\n\t AP vlan: ' + ap_vlan
	print '\n\n\t  Voice vlan: ' + voice_vlan
	print '\n\n\n If you would like to change them, exit out of the program and add the proper tags and values.\n\n'
	press_return()
	main_menu()
	
# SSH and start program
def connect():
	creds()
	global remote_conn
	global host
	if os.path.isfile(hosts_file):
		myfile = open(hosts_file, 'r')
		for ip in myfile:
			client = paramiko.SSHClient()
			client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			remote_conn = ()
			ip = ip.strip('\n')
			host = ip
			print_host = host
			print_host = print_host.replace('\n', '')
			try:
				print '\n------ Connecting to %s ------\n' % print_host
				client.connect(host, username=username, password=password, timeout=5)
				print '\t*** SSH session established with %s ****' % print_host
				remote_conn = client.invoke_shell()
				output = remote_conn.recv(1000)
				time.sleep(1)
				print '\t*** Sending enable password ****'
				remote_conn.send(en_password)
				remote_conn.send('\n')
				time.sleep(1)
				output = remote_conn.recv(1000)
			if '#' in output:
				print '\t*** Successfully Entered Enable mode ***'
				remote_conn.send('terminal length 0\n')
				time.sleep(1)
				get_int_and_cdp()
			else:
				print '\t*** Incorrect Enable Password ***'
		except paramiko.SSHException:
			print '\t*** Authentication failed ***'
		except socket.error:
			print '\t*** %s in Unreachable ***' % host
		client.close()
		
# Get username and passwords

def creds():
	global username, password, en_password
	print '\n\n'
	print '\t* * * * *'
	print '\t*       *'	
	print '\t*       *'
	print '\t* * * * *'
	print '\n\n Please enter username, password, and enable  password:\n'
	print '\t(Note that username is the onlu one that shows ' \
	'up while typing, passwords are not shown.)\n\n'
	username = raw_input(' Enter Username: ')
	password = getpass.getpass(' Enter Password: ')
	en_password = getpass.getpass(' Enter Enable Password: ')
	
# Send show cdp neighbors and interface status

def get_int_and_cdp():
	print '\n------ Downloading CDP and Interface Information ------\n'
	remote_conn.send('show cdp neighbors detail\n')
	print '\t*** Getting CDP Neighbors Detail ***'
	time.sleep(5)
	output = remote_conn.recv(50000)
	file = open('cdp', 'w')
	file.write(output)
	file.close()
	print '\t*** Received CDP Neighbors Detail ***'
	remote_conn.send('show int status\n')
	print '\t*** Getting show int status ***'
	time.sleep(3)
	output = remote_conn.recv(10000)
	file = open('int', 'w')
	file.write(output)
	file.close()
	file = open('int', 'r+')
	for line in file:
		if line.strip() == 'show int status':
			break
		file.write(line)
	file.close()
	print '\t*** Receive Show int status ***'
	parse_cdp()
	print '\t*** Parsed CDP neighbors ***'
	parse_int()
	print '\t*** Parsed Show int status ***'
	time.sleep(1)
	sh_cmd_outputs()
	
# Parse cdp neighbors file

def parse_cdp()
	network_devices.clear()
	ip, model, hostname = '', '', ''
	file = open('cdp', 'r')
	for data in file:
		data_line = data.split('\n')
		for line in data_line:
			if 'Device ID: ' in line:
				(junk, hostname) = line.split('Device ID: ')
				hostname = hostname.strip()
			if 'IP address: ' in line:
				(junk, ip) = line.split('IP address: ')
				ip = ip.strip()
			if 'Platform: ' in line:
				(platform, capabilities) = line.split(',')
				(junk, model) = platform.split('Platform: ')
				model = model.strip()
			if 'Interface: ' in line:
				(loc_int, junk) = line.split(',')
				(junk, loc_int) = loc_int.split('Interface: ')
				loc_int = loc_int.strip()
				loc_int = re.sub('TenGigabitEthernet', 'Te', loc_int)
				loc_int = re.sub('GigabitEthernet', 'Gi', loc_int)
				loc_int = re.sub('FastEthernet', 'Fa', loc_int)
				network_devices[loc_int] = {}
				network_devices[loc_int]['IP'] = ip
				network_devices[loc_int]['Model'] = model
				network_devices[loc_int]['Hostname'] = hostname
		file.close()

# Parse interface status file

def parse_int():
	int_sts.clear()
	file = open('int', 'r')
	myfile = file.readlines()[3:57]
	for line in myfile:
		port = line[:10]
		port = port.strip()
		name = line[10:29]
		name.strip()
		status =  line[29:42]
		status = status.strip()
		vlan = line[42:53]
		vlan = vlan.strip()
		duplex = line[53:60]
		duplex = duplex.strip()
		speed = line[60:67]
		speed = speed.strip()
		int_sts[port] = {}
		int_sts[port]['Port Label'] = name
		int_sts[port]['Status'] = status
		int_sts[port]['Vlan'] = vlan
		int_sts[port]['Duplex'] = duplex
		int_sts[port]['Speed'] = speed
	file.close()
	
''' **** Show gathered information in parsed from, show based on IF statement /
and commands to configure interfaces, resync info, or move to next switch ****'''

def sh_cmd_outputs():
	clear_screen()
	menu_actions = sub_menu_actions
	menu_return = sh_cmd_outputs
	print_host = host
	print_host = pint_host.replace('\n', '')
	print '\n\n\t-------- Connected to %s --------\n\n' % print_host
	print '\tPlease choose an option from the following:\n\n'
	print '\t\t1. Show parsed cdp neighbors detail\n'
	print '\t\t2. Show interface status\n'
	print '\t\t3. Show error disabled ports\n'
	print '\t\t4. Show devices without trunk or AP vlan in cdp\n'
	print '\t\t5. Show devices with trunk or AP vlan but not in cdp\n'
	print '\t\t6. Configure ports menu'
	print '\n\n\t\t7. Resync info with switch'
	print '\n\n\t\t8. Done and move on to next switch'
	print '\n\n\t\t9. Main menu'
	choice = raw_input('\n\n >> ')
	if choice == '8':
		pass
	else:
		exec_menu(menu_actions, menu_return, choice)
		return
	
# Print CDP information

def sh_cdp():
	for x in sorted(network_devices, key=sortkey_natural):
		print x
		for y in network_devices[x]:
			print '\t' + y, network_devices[x][y]
		press_return()
		sh_cmd_outputs()
		
# Print original show interface status

def sh_int_sts():
	file = open('int', 'r')
	int_face = file.readlines()[2:58]
	for x in int_face:
		print x.strip('\n')
	file.close()
	press_return()
	sh_cmd_outputs()
	
# Print error disabled ports

def sh_err_dis():
	err_dis = []
	print '\n\n\tChecking for error disabled ports'
	time.sleep(.5)
	for x in sorted(int_sts, key=sortkey_natural):
		if int_sts[x]['Status'] == 'err-disabled':
			err_dis.append(x)
			print (x)
			for y in int_sts[x]:
				print '\t' + y + ': ', int_sts[x][y]
	if len(err_dis) == 0:
		print '\n\n There are no error disabled ports!!!\n\n\n'
	press_return()
	sh_cmd_outputs()
	
# Print IF in CDP and != Trunk or AP vlan

def in_cdp_and_int():
	intersect = []
	for item in network_devices:
		if int_sts[item]['Vlan'] != 'trunk':
			if int_sts[item]['Vlan'] != ap_vlan:
				if 'IP Phone' not in network_devices[item]['Model']:
					intersec.append(item)
	intersec = sorted(intersec, key=sortkey_natural)
	print '\n\n\tChecking for devices that are not trunked or AP vlan with CDP'
	time.sleep(.5)
	for device in intersect:
		print device
		for values in network_devices[device]:
			print '\t' + values + ':', network_devices[device][values].rjust(50 - len(values))
		for values in int_sts[device]:
			print '\t' + values + ':', int_sts[device][values].just(50 - len(values))
	if len(intersec) == 0:
		print '\n\n There are no ports that need configuring!!!\n\n\n'
	press_return()
	sh_cmd_outputs()
	
# Print IF interface status == Trunk or AP Vlan AND no CDP neighbor

def in_int_not_cdp():
	if_no_cdp_intersect = []
	for item in int_sts:
		if not item.startswith(starts_items):
			if item not in network_devices:
				if int_sts[item]['Vlan'] == 'trunk' or int_sts[item] == ap_vlan:
					if_no_cdp_intersect.append(item)
	if_no_cdp_intersect = sorted(if_no_cdp_intersect, key=sortkey_natural)
	print '\n\n\tChecking for devices that are trunked or AP vlan but no CDP'
	time.sleep(.5)
	for device in if_no_cdp_intersect:
		print device
		for values in int_sts[device]:
			print '\t' + values + ':', int_sts[device][values].rjust(30 - len(values))
	if len(if_no_cdp_intersect) == 0:
		print '\n\n There are no ports that need configuring!!!\n\n\n'
	press_return()
	sh_cmd_outputs()