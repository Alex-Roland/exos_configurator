# exos_configurator
Script to build EXOS switch configurations  

The purpose of this script is to build a configuration file for the Extreme switch families based on user input. The script should be ran directly on the EXOS switch since it uses the exsh library. Run the script using the command  
```run script /usr/local/ext/exos_configurator.py```

# Notes
When entering the VLAN information (for version 1.4), enter the VLAN name first then the ID. They should also be separated by a space  
Example: NetMgmt 90

# Supported firmware
- 30.7.2.1
- 30.7.1.1
- 30.4.1.2
- Other firmware will most likely work, it just has not been tested on anything except the above listed firmware
