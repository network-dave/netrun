# Netrun

## Introduction

```netrun``` is an easy-to-use tool to run commands on network devices from the command line.


## Getting Started

```shell
$ pip install -r requirements.txt
```

```shell
$ python3 netrun.py -u <username> -p <password> -i <host1,host2,host3> -c <command1,command2> [...]
```

## When to (not) use netrun

Use netrun when you need to quickly run a number of CLI commands on network devices, and print the output to the terminal or save it to text files. You can either specify the hosts at the command line or read them from a simple text file, no inventory file required.

If you need complex inventories, multithreading, or complex runtime logic with safeguards included, use ```Ansible``` instead.

If you need the above things but in pure Python, use ```Nornir``` instead.


## But why ?

Becayse I needed something simple for my day-to-day routine as a network engineer. Because sometimes you can't install Ansible, or want to start building inventory files, just to run a few "show" commands.

Because the code is simple and easy to read, because it is cross-platform, contained in a single source file, and requires no specific setup except installing the required Python libraries. It will run on any system where Python3.7+ is installed, Windows, Mac and Linux. 

And as long as you know how to install Python libraries offline, it makes a convenient tool for air-gapped systems with no Internet access, or where you can't deploy a full blown network automation platform.


## How does it work

Initially based on Netmiko, netrun now uses ```Scrapli``` under the hood. All ```netrun``` is doing is providing a command-line wrapper around Scrapli, with a couple of opiniated choices about how to provide the host information and the commands to run against them, which ciphers to use, and how to handle the output.


## Can I use my SSH configuration file?

By default, ```netrun```  uses ```libssh2``` as transport as it is the only crossplatform library so far. On POSIX systems (Windows is not supported), the system SSH can be used as transport mecanism instead. The SSH config files will be loaded like with the regular SSH CLI, which means any configuration like hosts and options (for example ProxyCommand) can be used.


## A few examples


```shell
$ python3 netrun.py -i '172.16.10.10,172.16.10.11' -u johndoe -c 'show version| i Serial'

$ python3 netrun.py -I my_switches.txt -C show_commands.txt -u johndoe -p C00lp4$$ -n -sSo ./Switches
```
See ```python3 netrun.py --help``` for a complete set of options.

## Notes

- Hosts and commands can be specified at the command-line or loaded from text files
- Commands can be loaded either from a single text file (use it to send the same commands to each host), or from a "netrun_deploy_<host>.txt" file unique to each host (use this to send unique commands to each host)
- When loading hosts from a text file, put a single hostname or IP address per line
- Usernames and passwords can be specified at the command line or loaded from the following environment variables: NETRUN_USERNAME, NETRUN_PASSWORD, NETRUN_ENABLE ***(UNSAFE)***
- If no username/passwords are specified at all, they will be prompted at runtime
- By default, enable mode is entered after login. Use '-n' to avoid going into enable mode and stay in exec mode (this is quicker to run show commands)
- When connecting to a host fails, it's hostname/IP is appended to the 'netrun_failed_{{timestamp}}.txt' file
- Default timeout for socket and transport operations is set to 10 seconds


## License

©️ 2022 David Paneels

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

https://www.gnu.org/licenses/gpl-3.0.html
