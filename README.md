# Netrun

Netrun is a small tool aimed at easily interacting with network devices from the command-line.

## Requirements

```shell
pip install scrapli
```

**Attention: at the time of this writing, a bug in the IOS-XE driver would prevent to go into enable mode. I did modify the 'base' driver's source code in order to make this work. Hopefully this should be fixed very soon.**


## Getting started/Usage

```shell
python netrun.py -u <username> -p <password> -d <device> -c <command> [...]
```
See ```netrun.py --help``` for a complete list of command-line arguments.

- Devices and commands can be specified as command-line arguments or loaded from a text file.
- If no password is specified, it will be prompted at runtime.
- If no enable password/secret is specified, the user password will be used. 
- By default, enable mode is entered after login
- Use '-n' to avoid going into enable mode and stay in exec mode (quicker for show commands)


## Device file ##
- No hostnames, only IP addresses!
- The file does not need to be formatted in any specific way, all IP addresses will be extracted

## SSH configuration file

By default, Netrun uses the system's SSH as transport mecanism. The system and the user's SSH config is loaded like with a regular SSH command, which means hosts, options like ProxyCommand can be used.

## Examples

```shell
$ python netrun.py -d 172.16.10.10,172.16.10.11 -u id123456 -c show version

$ python netrun.py -D my_switches.txt -C show_commands.txt -u dpaneels -p C00lp4$$ -n -sSO ./netrun_output/
```


## License

Author: David Paneels

For internal use only.