
# ZFS Command Generator

A simple web application built with Flask to generate ZFS send commands for both incremental and full snapshots. This tool simplifies the process of creating ZFS commands, allowing users to specify the necessary parameters through a web form.

## Features

- Generate incremental ZFS send commands.
- Generate full ZFS send commands.
- Option to enable forced synchronization and compression.
- Easy-to-use web interface with copy-to-clipboard functionality.

## Requirements

- Python 3.x
- Flask
- pyperclip (for clipboard functionality)
- mbuffer


This code is designed with specific assumptions regarding the locations and naming conventions of ZFS pools. If both the sending and receiving pools share the same prefix (for example, "l1"), the code assumes they are located in the same location and selects an alternative SSH alias for local transfers. Additionally, it is expected that all pool names follow a consistent naming pattern, ending with "p1."