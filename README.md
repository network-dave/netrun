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

- Devices and commands can be specified as command-line arguments or loaded from a text file.
- If no password is specified, it will be prompted at runtime.
- If no enable password/secret is specified, the user password will be used. 
- By default, enable mode is entered after login
- Use '-n' to avoid going into enable mode and stay in exec mode (quicker for show commands)
- When connecting to a device fails, it's IP address is appended to the 'netrun_failed.txt' file


## Device file ##
- No hostnames, only IP addresses!
- The file does not need to be formatted in any specific way, all IP addresses will be extracted

## SSH configuration file

By default, Netrun uses the system's SSH as transport mecanism. The system and the user's SSH config is loaded like with a regular SSH command, which means hosts, options like ProxyCommand can be used.

## Examples

```shell
$ python netrun.py -d 172.16.10.10,172.16.10.11 -u johndoe -c show version

$ python netrun.py -D my_switches.txt -C show_commands.txt -u johndoe -p C00lp4$$ -n -sSO ./netrun_output/
```


## License

Copyright (C) 2020 David Paneels

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

https://www.gnu.org/licenses/gpl-3.0.html
