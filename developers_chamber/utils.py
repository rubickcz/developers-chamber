import logging
import subprocess
import sys

from click import ClickException


LOGGER = logging.getLogger()


def call_command(command):
    try:
        LOGGER.info(command if isinstance(command, str) else ' '.join(command))
        subprocess.check_call(command, stdout=sys.stdout, shell=isinstance(command, str))
    except subprocess.CalledProcessError:
        raise ClickException('Command returned error')


def print_bold(message):
    print('\033[1m{}\033[0m'.format(message))


def print_heading(message):
    print_bold('\033[34m{}\033[0m'.format(message))


def print_error(message):
    print_bold('\033[91m{}\033[0m'.format(message))


def print_success(message):
    print_bold('\033[92m{}\033[0m'.format(message))
