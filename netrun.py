#!/usr/bin/env python3

'''

***********************************************************************************************************
netrun.py
***********************************************************************************************************

Description:    Run commands on network devices straight from the command line
Author:         David Paneels
Usage:          see python3 netrun.py --help


'''

import os
import sys
import argparse
import getpass
import logging
from datetime import datetime

from scrapli import Scrapli


# Used to split username/password lists
DELIMITER = ","

# Define the width of separator lines in headers
SEPARATOR_WIDTH = 120



def parse_arguments():
    '''
    Parse command line arguments.

    '''

    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Run commands on network hosts from the command-line", 
        add_help=False
        )

    # Host inventory arguments
    arg_group_hosts = parser.add_argument_group(
        title="Host inventory"
        )
    arg_group_hosts.add_argument(
        "-t",
        "--transport", 
        metavar="<system|telnet|...>",
        help="transport mechanism (default=system SSH)",
        default="ssh2"
        )
    arg_group_hosts.add_argument(
        "-x",
        "--platform", 
        metavar="<platform>",
        help="network OS platform (default=cisco_iosxe)",
        default="cisco_iosxe"
        )
    arg_host = arg_group_hosts.add_mutually_exclusive_group(
        required=True
        )
    arg_host.add_argument(
        "-i",
        "--inventory", 
        metavar="<hostname-or-ip-addres>",
        help="IP address(es) of the host(s) to connect to (provide multiple hosts separated by commas)"
        )
    arg_host.add_argument(
        "-I",
        "--inventory-file",
        metavar="<filename>",
        help="text file containing a list of hostnames/IP addresses"
        )
    arg_group_hosts.add_argument(
        "--port",
        help="host port (default=22)",
        metavar="<port>"
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
        help="command(s) to execute (provide multiple commands separated by commas)",
        nargs="*"
        )
    arg_commands.add_argument(
        "-C",
        "--commands-file",
        metavar="<filename>",
        help="text file containing a list of commands"
        )
    arg_commands.add_argument(
        "--deploy",
        help="load commands from file netrun_deploy_<host>.txt for each host", 
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
        help="do not go into enable mode after login",
        action="store_true"
        )

    # Output arguments
    arg_group_output = parser.add_argument_group(
        title="Output"
        )
    arg_group_output.add_argument(
        "-s",
        "--save",
        help="save the output to a text file (1 file per host)",
        action="store_true"
        )
    arg_group_output.add_argument(
        "-S",
        "--separate-output",
        help="save the output of each command to a different text file (1 file per command)",
        action="store_true"
        )
    arg_group_output.add_argument(
        "-o",
        "--output-directory",
        metavar="\b",
        help="path/directory where to save the output files to"
        )

    # Misc options
    arg_group_misc = parser.add_argument_group(
        title="Misc"
        )
    arg_group_misc.add_argument(
        "--verbose", 
        help="display verbose debugging output", 
        action="store_true"
        )
    arg_group_misc.add_argument(
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
        logging.basicConfig(format="%(message)s", level=logging.DEBUG)
    else:
        logging.basicConfig(format="%(message)s", level=logging.WARNING)

    # Get list of hosts from file or CLI
    logging.info("[+] Parsing host list")
    if args.inventory_file:
        with open(args.inventory_file) as f:
            list_of_hosts = f.readlines()
    else:
        list_of_hosts = args.inventory.split(",")
    logging.info(f"[+] Found hosts: {','.join(list_of_hosts)}")

    # Get commands from text file or arguments
    if args.commands_file:
        with open(args.commands_file, "r") as f:
            commands = [ line.rstrip() for line in f.readlines() if line.strip() ]
    elif args.deploy:
        # In case of deploy mode we will load the commands further up
        pass
    else:
        # Build commands from the command-line arguments
        commands = " ".join(args.commands).split(",")

    # Used to redirect stdout to screen if not saving to file
    output_file_object = None

    # If no username is specified, we will prompt at runtime
    if not args.username:
        if os.environ.get("NETRUN_USERNAME"):
            args.username = os.environ.get("NETRUN_USERNAME")
        else:
            args.username = input("SSH Username: ")

    # If no password is specified, we will prompt at runtime
    if not args.password:
        if os.environ.get("NETRUN_PASSWORD"):
            args.password = os.environ.get("NETRUN_PASSWORD")
        else:
            args.password = getpass.getpass("SSH Password: ")

    # Define privilege level (exec or enable mode) to use after login
    if args.no_enable:
        privilege_level = "exec"
    else:
        privilege_level = "privilege_exec"    
        # If no enable password is set, we will use the user password
        if not args.enable_password:
            if os.environ.get("NETRUN_ENABLE"):
                args.enable_password = os.environ.get("NETRUN_ENABLE")
            else:
                logging.info(f"[+] No enable secret has been specified, using the user password")
                args.enable_password = args.password

    # Define SSH/Telnet default TCP port
    if not args.port:
        if args.transport == "telnet":
            args.port = 23
        else:
            args.port = 22

    # Registering date/time for use in filenames
    date_time = datetime.strftime(datetime.now(), "%Y-%m-%d_%Hh%Mm%S")

    # Connect to each host, run the commands and print the output
    for host in list_of_hosts:
        host = host.strip()
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
                transport = args.transport,
                platform = args.platform,
                timeout_socket = 15,
                timeout_transport = 15,
                transport_options = {"open_cmd": [
                    "-o", 
                    "KexAlgorithms=+diffie-hellman-group1-sha1,diffie-hellman-group-exchange-sha1,diffie-hellman-group14-sha1",
                    "-o",
                    "Ciphers=+aes128-ctr,aes192-ctr,aes256-ctr,aes128-cbc,3des-cbc,3des-cbc,aes192-cbc,aes256-cbc"
                    ]}
                )
            logging.warning(f"[+] Connecting to host {host}")
            conn.open()
        except Exception as e:
            logging.fatal(f"[!] Error: {str(e)}")
            with open(f"netrun_failed_{date_time}.txt", "a") as f:
                f.write(host + "\n")
            continue
        logging.info(f"[+] Successfully connected and authenticated to {host}")

        # If we use deploy mode, we'll load the commands from a text file named <host>_netrun_deploy.txt
        if args.deploy:
            filename = f"netrun_deploy_{host}.txt"
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    commands = [ line.rstrip() for line in f.readlines() if line.strip() ]
                    logging.info(f"[+] Successfully loaded commands from {filename}")
            else:
                logging.warn("[!] No netrun_deploy file found for this host. Skipping to next one.")
                continue

        # If saving and separate outputs are not enabled, print separator header per host
        if not args.save and not args.separate_output:
            print(file=output_file_object)
            print(f"*****".ljust(SEPARATOR_WIDTH, "*"), file=output_file_object)
            print(f"***** {host} ".ljust(SEPARATOR_WIDTH, "*"), file=output_file_object)
            print(f"*****".ljust(SEPARATOR_WIDTH, "*"), file=output_file_object)        

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

        # Run all commands sequentially
        logging.info(f"[+] Sending commands to host")
        for c in commands:
            now = datetime.strftime(datetime.now(), "%Y-%m-%d_%Hh%Mm%S")
            response = conn.send_command(c)
            if args.save and args.separate_output:
                # Whitespaces in the command will be replaced by dashes in the filename
                filename = os.path.join(
                    save_dir, 
                    f"{host}_{c.replace(' ', '-')}_{now}.txt"
                    )
                output_file_object = open(filename, "w")

            if args.save:
                logging.warning(f"[+] Saving output of '{c}' to {filename}")

            # Print separator header per command
            print(f"-----".ljust(SEPARATOR_WIDTH, "-"), file=output_file_object)
            print(f"[{now}] {host}: Output of command \'{c}\':", file=output_file_object)
            print(f"-----".ljust(SEPARATOR_WIDTH, "-"), file=output_file_object)
            print(f"{response.result}", file=output_file_object)
            print(file=output_file_object)

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
