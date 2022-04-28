# Netrun

Netrun is a small tool aimed at easily interacting with network devices from the command-line.

## Requirements / Getting Started

```shell
$ pip install -r requirements.txt
```

```shell
$ python netrun.py -u <username> -p <password> -d <device> -c <command> [...]
```


## Usage

See ```netrun.py --help``` for a complete list of command-line arguments.

- Hosts and commands can be specified at the command-line or loaded from a text file.
- Usernames and passwords can be specified at the command line or loaded from the following environment variables: NETRUN_USERNAME, NETRUN_PASSWORD, NETRUN_ENABLE
- If no username/passwords are specified at all, they will be prompted at runtime.
- By default, enable mode is entered after login
- Use '-n' to avoid going into enable mode and stay in exec mode (quicker for show commands)
- When connecting to a host fails, it's hostname/IP is appended to the 'netrun_failed_<date-time>.txt' file
- Timeout for socket and transport operations is set to 10 seconds


## Hosts file ##
- One hostname/IP address per line


## SSH configuration file

By default, Netrun uses the system's SSH as transport mecanism (through the Scrapli library). The system and the user's SSH config is loaded like with a regular SSH command, which means and configuration like hosts and options (for example ProxyCommand) can be used.


## Quick Examples

```shell
$ python netrun.py -h 172.16.10.10,172.16.10.11 -u johndoe -c show version

$ python netrun.py -H my_switches.txt -C show_commands.txt -u johndoe -p C00lp4$$ -n -sSo ./netrun_output/
```


## License

Copyright (C) 2022 David Paneels

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

https://www.gnu.org/licenses/gpl-3.0.html
