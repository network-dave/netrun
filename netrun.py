#!/usr/bin/env python3

'''

netrun.py - Run commands on network devices from the command line

Usage: use --help for help

Author: David Paneels

'''

import os
import sys
import argparse
import re
import time
import getpass
import logging
from datetime import datetime

from scrapli import Scrapli


# Used to split username/password lists
DELIMITER = ","

# Define SSH transport type for Scrapli driver 
TRANSPORT = "system"


def parse_arguments():
    '''
    Parse command line arguments.

    '''

    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Run commands on network devices from the command-line", 
        add_help=False
        )

    # Devices arguments
    arg_group_devices = parser.add_argument_group(
        title="Device(s)"
        )
    arg_device = arg_group_devices.add_mutually_exclusive_group(
        required=True
        )
    arg_device.add_argument(
        "-d",
        "--device", 
        metavar="<ipaddress>",
        help="IP address(es) of the device(s) to connect to (multiple separated by commas)"
        )
    arg_device.add_argument(
        "-D",
        "--device-list",
        metavar="<filename>",
        help="text file containing a list of IP addresses"
        )
    arg_group_devices.add_argument(
        "--port",
        help="SSH port (default=22)",
        metavar="<port>",
        default="22"
        )
    
    # Command arguments
    arg_group_commands = parser.add_argument_group(
        title="Command(s)"
        )
    arg_commands = arg_group_commands.add_mutually_exclusive_group(
        required=True
        )
    arg_commands.add_argument(
        "-c",
        "--commands",
        metavar="<command>",
        help="command(s) to execute (multiple separated by commas)",
        nargs="*"
        )
    arg_commands.add_argument(
        "-C",
        "--command-list",
        metavar="<filename>",
        help="text file containing a list of commands"
        )
    arg_commands.add_argument(
        "--autodeploy",
        help="load commands from file <ipaddress>_autodeploy.txt for each device", 
        action="store_true"
        )

    # Authentication credentials arguments
    arg_group_authentic = parser.add_argument_group(
        title="Authentication"
        )
    arg_group_authentic.add_argument(
        "-u",
        "--username",
        metavar="<username>",
        required=True
        )
    arg_group_authentic.add_argument(
        "-p",
        "--password",
        metavar="<password>",
        )
    arg_group_authentic.add_argument(
        "-e", 
        "--enable-password", 
        metavar="<secret>",
        help="enable password/secret (if empty, use authentication password)"
        )
    arg_group_authentic.add_argument(
        "-n",
        "--no-enable",
        help="do not go into enable mode",
        action="store_true"
        )

    # Output arguments
    third_arg_group = parser.add_argument_group(
        title="Save output"
        )
    third_arg_group.add_argument(
        "-s",
        "--save",
        help="save the output to a text file (1 file per IP address)",
        action="store_true"
        )
    third_arg_group.add_argument(
        "-S",
        "--separate-output",
        help="save the output of each command to a separate text file",
        action="store_true"
        )
    third_arg_group.add_argument(
        "-O",
        "--output-directory",
        metavar="\b",
        help="path/directory where to save the output files to"
        )

    # Misc options
    fourth_arg_group = parser.add_argument_group(
        title="Misc"
        )
    fourth_arg_group.add_argument(
        "-v", 
        "--verbose", 
        help="verbose output (useful for debbugging)", 
        action="store_true"
        )
    fourth_arg_group.add_argument(
        "-h",
        "--help",
        help="display this message and exit",
        action="help"
        )

    return parser.parse_args()


def main():
    '''
    netrun.py Main program

    '''
    # Parse command line arguments
    args = parse_arguments()

    # Initialize logging
    if args.verbose:
        logging.basicConfig(format="%(message)s", level=logging.INFO)
    else:
        logging.basicConfig(format="%(message)s", level=logging.WARNING)

    # Get list of devices
    logging.info("[+] Parsing device list")
    if args.device_list:
        with open(args.device_list) as f:
            content = f.readlines()
            list_ip_addresses = []
            # Get a list of unique IP addresses (to be upgraded...)
            for line in content:
                if not line.startswith("!") and not line.startswith("#") and line.strip():
                    for ip_address in re.findall(r"(?:\d{1,3}\.){3}\d{1,3}", line):
                        if ip_address not in list_ip_addresses and not ip_address.startswith("255."):
                            list_ip_addresses.append(ip_address)
    else:
        list_ip_addresses = args.device.split(",")
    logging.info(f"[+] Found devices: {','.join(list_ip_addresses)}")

    # Get commands from text file or arguments
    if args.command_list:
        with open(args.command_list, "r") as f:
            commands = [ line.rstrip() for line in f.readlines() if line.strip() ]
    elif args.autodeploy:
        # In case of autodeploy we will load the commands further up
        pass
    else:
        # Build commands from the command-line arguments
        commands = " ".join(args.commands).split(",")

    # Used to redirect stdout to screen if not saving to file
    output_file_object = None

    # If no password is specified, we will prompt at runtime
    if not args.password:
        args.password = getpass.getpass("SSH Password: ")

    # Define privilege level (exec or enable mode) to use after login
    if args.no_enable:
        privilege_level = "exec"
    else:
        privilege_level = "privilege_exec"    
        # If no enable password is set, we will use the user password
        if not args.enable_password:
            logging.info(f"[+] No enable secret has been specified, using the user password")
            args.enable_password = args.password

    # Connect to each device, run the commands and print the output
    for ip_address in list_ip_addresses:
        logging.info(f"[+] Initializing network driver for {ip_address}")
        try:
            # Create Scrapli network driver object and open SSH channel
            conn = Scrapli(
                host = ip_address,
                port = int(args.port), 
                auth_username = args.username, 
                auth_password = args.password, 
                auth_secondary = args.enable_password,
                auth_strict_key = False,
                ssh_config_file = True,
                default_desired_privilege_level = privilege_level,
                transport = TRANSPORT,
                platform = "cisco_iosxe"
                )
            print(f"[+] Opening connection to {ip_address}")
            conn.open()
        except Exception as e:
            print(f"[!] Error: {str(e)}")
            continue
        print(f"[+] Successfully connected and authenticated to {ip_address}")

        # If saving is enabled, build the output path and filename
        if args.save:
            logging.info(f"[+] Setting output directory")
            if args.output_directory:
                save_dir = args.output_directory.format(
                    date_time=date_time, 
                    ip_address=ip_address, 
                    hostname=conn.host, 
                    username=conn.auth_username
                    )
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir, exist_ok=True)
            else:
                save_dir = os.getcwd()
            # Timestamping for filename
            date_time = datetime.strftime(datetime.now(), "%Y-%m-%d_%Hh%Mm%S")
            filename = os.path.join(save_dir, f"netrun_output_{ip_address}_{date_time}.txt")
            output_file_object = open(filename, "w")
            logging.info(f"[+] Output will be saved to {filename}")

        # If we use autodeploy, we'll load the commands from a text file names <ip_address>_autodeploy.txt
        if args.autodeploy:
            filename = f"{ip_address}_autodeploy.txt"
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    commands = [ line.rstrip() for line in f.readlines() if line.strip() ]
                    logging.info(f"[+] Successfully loaded autodeploy commands from {filename}")
            else:
                logging.warn("[!] No autodeploy file found. Skipping device.")
                continue

        # Run all commands sequentially
        logging.info(f"[+] Sending commands to device")
        for c in commands:
            now = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
            response = conn.send_command(c)
            if args.save and args.separate_output:
                # Note: whitespaces in the command will be replaced by dashes
                filename = os.path.join(
                    save_dir, 
                    f"{ip_address}_{c.replace(' ', '-')}_{date_time}.txt"
                    )
                output_file_object = open(filename, "w")
                print(response.result, file=output_file_object)
            else:
                print(f"\n[{now}] {ip_address}: Output of command \'{c}\' \
                    \n\n{response.result}", file=output_file_object)
            if args.save:
                print(f"[+] Saving output of {c} to {filename}")

        # Close the output file handler and close the connection
        if output_file_object:
            output_file_object.close()
        logging.info(f"[+] Closing connection")
        conn.close()

    sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit(1)
