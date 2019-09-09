import os

import click

from developers_chamber.click.options import ContainerDirToCopyType, ContaineCommandType
from developers_chamber.scripts import cli
from developers_chamber.project_utils import (
    set_hosts, compose_build, compose_run, compose_exec, compose_up, docker_clean, compose_install, compose_kill_all
)


default_project_name = os.environ.get('PROJECT_DOCKER_COMPOSE_PROJECT_NAME')
default_compose_files = (
    os.environ.get('PROJECT_DOCKER_COMPOSE_FILES').split(',')
    if os.environ.get('PROJECT_DOCKER_COMPOSE_FILES') else None
)
default_domains = (
    os.environ.get('PROJECT_DOMAINS').split(',')
    if os.environ.get('PROJECT_DOMAINS') else None
)
default_containers = (
    os.environ.get('PROJECT_DOCKER_COMPOSE_CONTAINERS').split(',')
    if os.environ.get('PROJECT_DOCKER_COMPOSE_CONTAINERS') else None
)
default_var_dir = os.environ.get('PROJECT_DOCKER_COMPOSE_VAR_DIR')
default_containers_dir_to_copy = os.environ.get('PROJECT_DOCKER_COMPOSE_CONTAINERS_DIR_TO_COPY', '').split(',')
default_containers_install_command = os.environ.get('PROJECT_DOCKER_COMPOSE_CONTAINERS_INSTALL_COMMAND', '').split(',')

@cli.group()
def project():
    """Project commands"""


@project.command()
@click.option('--domain', help='Domain which will be set to the hosts file', type=str, required=True, multiple=True,
              default=default_domains)
def set_domain(domain):
    """
    Set local hostname translation to localhost
    """
    set_hosts(domain)
    click.echo(
        'Host file was set: {} -> 127.0.0.1'.format(', '.join(domain))
    )


@project.command()
@click.option('--project_name', help='Name of the project', type=str, required=True, default=default_project_name)
@click.option('--compose_file', help='Compose file', type=str, required=True, multiple=True,
              default=default_compose_files)
@click.option('--container', help='Container name', type=str, required=False, multiple=True)
def build(project_name, compose_file, container):
    """
    Build docker container
    """
    compose_build(project_name, compose_file, container)


@project.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True
    )
)
@click.argument('command')
@click.option('--project_name', help='Name of the project', type=str, required=True, default=default_project_name)
@click.option('--compose_file', help='Compose file', type=str, required=True, multiple=True,
              default=default_compose_files)
@click.option('--container', help='Container name', type=str, required=True, multiple=True, default=default_containers)
@click.pass_context
def run(ctx, project_name, compose_file, container, command):
    """
    Run one time command in docker container
    """
    compose_run(project_name, compose_file, container, ' '.join([command] + ctx.args))


@project.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True
    )
)
@click.argument('command')
@click.option('--project_name', help='Name of the project', type=str, required=True, default=default_project_name)
@click.option('--compose_file', help='Compose file', type=str, required=True, multiple=True,
              default=default_compose_files)
@click.option('--container', help='Container name', type=str, required=True, multiple=True, default=default_containers)
@click.pass_context
def exec(ctx, project_name, compose_file, container, command):
    """
    Run command in docker service
    """
    compose_exec(project_name, compose_file, container, ' '.join([command] + ctx.args))


@project.command()
@click.option('--project_name', help='Name of the project', type=str, required=True, default=default_project_name)
@click.option('--compose_file', help='Compose file', type=str, required=True, multiple=True,
              default=default_compose_files)
@click.option('--container', help='Container name', type=str, required=False, multiple=True)
def up(project_name, compose_file, container):
    """
    Builds, (re)creates, starts, and attaches to containers for a service.
    """
    compose_up(project_name, compose_file, container)


@project.command()
@click.option('--project_name', help='Name of the project', type=str, required=True, default=default_project_name)
@click.option('--compose_file', help='Compose file', type=str, required=True, multiple=True,
              default=default_compose_files)
@click.option('--var-dir', help='Variable content directory', type=str, required=True,
              default=default_var_dir)
@click.option('--container-dir-to-copy',
              help='Container dir which will be copied after build in format '
                   'DOCKER_CONTAINER_NAME:CONTAINER_DIRECTORY:HOST_DIRECTORY',
              type=ContainerDirToCopyType(), required=True, multiple=True, default=default_containers_dir_to_copy)
@click.option('--install-container-command',
              help='Container command which will be run after build in format DOCKER_CONTAINER_NAME:COMMAND',
              type=ContaineCommandType(), required=False, multiple=True, default=default_containers_install_command)
def install(project_name, compose_file, var_dir, container_dir_to_copy, install_container_command):
    """
    Builds, (re)creates, starts, and attaches to containers for a service.
    """
    compose_install(project_name, compose_file, var_dir, container_dir_to_copy, install_container_command)


@project.command()
def kill_all():
    """
    Kill all running docker instances
    """
    compose_kill_all()


@project.command()
@click.option('--hard', help='Clean hard', default=False, is_flag=True)
def clean(hard):
    """
    Clean docker images and its volumes
    """
    docker_clean(hard)
