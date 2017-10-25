#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "loomengine_server.core.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
    

if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    main()
