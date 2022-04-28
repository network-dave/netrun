#!/usr/bin/env python3

'''

netrun.py - Run commands on network hosts from the command line

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

# Additional DNS search domain to append to hostnames if not specified
DOMAIN = "net.scrl.local"

# Define SSH transport type for Scrapli driver 
TRANSPORT = "system"


def parse_arguments():
    '''
    Parse command line arguments.

    '''

    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Run commands on network hosts from the command-line", 
        add_help=False
        )

    # hosts arguments
    arg_group_hosts = parser.add_argument_group(
        title="host(s)"
        )
    arg_host = arg_group_hosts.add_mutually_exclusive_group(
        required=True
        )
    arg_host.add_argument(
        "-h",
        "--host", 
        metavar="<hostname-or-ip>",
        help="IP address(es) of the host(s) to connect to (provide multiple separated by commas)"
        )
    arg_host.add_argument(
        "-H",
        "--hosts-file",
        metavar="<filename>",
        help="text file containing a list of hostnames/IP addresses"
        )
    arg_group_hosts.add_argument(
        "-P",
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
        help="command(s) to execute (provide multiple separated by commas)",
        nargs="*"
        )
    arg_commands.add_argument(
        "-C",
        "--commands-file",
        metavar="<filename>",
        help="text file containing a list of commands"
        )
    arg_commands.add_argument(
        "--autodeploy",
        help="load commands from file <host>_autodeploy.txt for each host", 
        action="store_true"
        )

    # Authentication credentials arguments
    arg_group_authentic = parser.add_argument_group(
        title="Authentication"
        )
    arg_group_authentic.add_argument(
        "-u",
        "--username",
        metavar="<username>"
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
        help="save the output to a text file (1 file per host)",
        action="store_true"
        )
    third_arg_group.add_argument(
        "-S",
        "--separate-output",
        help="save the output of each command to a different text file",
        action="store_true"
        )
    third_arg_group.add_argument(
        "-o",
        "--output-directory",
        metavar="\b",
        help="path/directory where to save the output files to"
        )

    # Misc options
    fourth_arg_group = parser.add_argument_group(
        title="Misc"
        )
    fourth_arg_group.add_argument(
        "--debug", 
        help="show debugging output", 
        action="store_true"
        )
    fourth_arg_group.add_argument(
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
    if args.debug:
        logging.basicConfig(format="%(message)s", level=logging.DEBUG)
    else:
        logging.basicConfig(format="%(message)s", level=logging.WARNING)

    # Get list of hosts from file or CLI
    logging.info("[+] Parsing host list")
    if args.hosts_file:
        with open(args.hosts_file) as f:
            list_of_hosts = f.readlines()
    else:
        list_of_hosts = args.host.split(",")
    logging.info(f"[+] Found hosts: {','.join(list_of_hosts)}")

    # Get commands from text file or arguments
    if args.commands_file:
        with open(args.commands_file, "r") as f:
            commands = [ line.rstrip() for line in f.readlines() if line.strip() ]
    elif args.autodeploy:
        # In case of autodeploy we will load the commands further up
        pass
    else:
        # Build commands from the command-line arguments
        commands = " ".join(args.commands).split(",")

    # Used to redirect stdout to screen if not saving to file
    output_file_object = None

    # If no username is specified, we will prompt at runtime
    if not args.username:
        args.password = input("SSH Username: ")

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

    # Registering date/time for use in filenames
    date_time = datetime.strftime(datetime.now(), "%Y-%m-%d_%Hh%Mm%S")

    # Connect to each host, run the commands and print the output
    for host in list_of_hosts:
        logging.info(f"[+] Initializing network driver for {host}")
        try:
            # Create Scrapli network driver object and open SSH channel
            conn = Scrapli(
                host = host,
                port = int(args.port), 
                auth_username = args.username, 
                auth_password = args.password, 
                auth_secondary = args.enable_password,
                auth_strict_key = False,
                ssh_config_file = True,
                default_desired_privilege_level = privilege_level,
                transport = TRANSPORT,
                platform = "cisco_iosxe",
                timeout_socket = 10,
                timeout_transport = 10,
                transport_options = {"open_cmd": ["-o", "KexAlgorithms=+diffie-hellman-group1-sha1"]}
                )
            print(f"[+] Opening connection to {host}")
            conn.open()
        except Exception as e:
            print(f"[!] Error: {str(e)}")
            with open(f"netrun_failed_{date_time}.txt", "a") as f:
                f.write(host + "\n")
            continue
        print(f"[+] Successfully connected and authenticated to {host}")

        # If saving is enabled, build the output path and filename
        if args.save:
            logging.info(f"[+] Setting output directory")
            if args.output_directory:
                save_dir = args.output_directory.format(
                    date_time=date_time, 
                    host=host, 
                    username=args.username
                    )
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir, exist_ok=True)
            else:
                save_dir = os.getcwd()
            filename = os.path.join(save_dir, f"netrun_output_{host}_{date_time}.txt")
            if not args.separate_output:
                output_file_object = open(filename, "w")
            logging.info(f"[+] Output will be saved to {filename}")

        # If we use autodeploy, we'll load the commands from a text file names <host>_autodeploy.txt
        if args.autodeploy:
            filename = f"{host}_autodeploy.txt"
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    commands = [ line.rstrip() for line in f.readlines() if line.strip() ]
                    logging.info(f"[+] Successfully loaded autodeploy commands from {filename}")
            else:
                logging.warn("[!] No autodeploy file found. Skipping host.")
                continue

        # Run all commands sequentially
        logging.info(f"[+] Sending commands to host")
        for c in commands:
            now = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
            response = conn.send_command(c)
            if args.save and args.separate_output:
                # Note: whitespaces in the command will be replaced by dashes
                filename = os.path.join(
                    save_dir, 
                    f"{host}_{c.replace(' ', '-')}_{now}.txt"
                    )
                output_file_object = open(filename, "w")
                print(response.result, file=output_file_object)
                print(f"[+] Saving output of '{c}' to {filename}")
            else:
                print(f"[{now}] {host}: Output of command \'{c}\' \
                    \n{response.result}\n", file=output_file_object)
                if args.save:
                    print(f"[+] Saving output of '{c}' to {filename}")

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
