import sys

import click

from ai.backend.client.session import Session
from ai.backend.client.func.scaling_group import (
    _default_list_fields,
    _default_detail_fields,
)
from ai.backend.client.output.fields import scaling_group_fields
from . import admin
from ..pretty import print_done, print_error, print_fail
from ..params import JSONParamType
from ..types import CLIContext


@admin.group()
def scaling_group() -> None:
    """
    Scaling group (resource group) administration commands.
    """


@scaling_group.command()
@click.pass_obj
@click.argument('group', type=str, metavar='GROUP_NAME')
def get_available(ctx: CLIContext, group: str) -> None:
    with Session() as session:
        try:
            items = session.ScalingGroup.list_available(group)
            ctx.output.print_list(items, [scaling_group_fields['name']])
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(1)


@scaling_group.command()
@click.pass_obj
@click.argument('name', type=str)
def info(ctx: CLIContext, name: str) -> None:
    """
    Show the information about the given scaling group.
    (superadmin privilege required)
    """
    with Session() as session:
        try:
            item = session.ScalingGroup.detail(name=name)
            ctx.output.print_item(item, _default_detail_fields)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(1)


@scaling_group.command()
@click.pass_obj
def list(ctx: CLIContext) -> None:
    """
    List and manage scaling groups.
    (superadmin privilege required)
    """
    with Session() as session:
        try:
            items = session.ScalingGroup.list()
            ctx.output.print_list(items, _default_list_fields)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(1)


@scaling_group.command()
@click.argument('name', type=str, metavar='NAME')
@click.option('-d', '--description', type=str, default='',
              help='Description of new scaling group')
@click.option('-i', '--inactive', is_flag=True,
              help='New scaling group will be inactive.')
@click.option('--driver', type=str, default='static',
              help='Set driver.')
@click.option('--driver-opts', type=JSONParamType(), default={},
              help='Set driver options as a JSON string.')
@click.option('--scheduler', type=str, default='fifo',
              help='Set scheduler.')
@click.option('--scheduler-opts', type=JSONParamType(), default={},
              help='Set scheduler options as a JSON string.')
def add(name, description, inactive,
        driver, driver_opts, scheduler, scheduler_opts):
    """
    Add a new scaling group.

    NAME: Name of new scaling group.
    """
    with Session() as session:
        try:
            data = session.ScalingGroup.create(
                name,
                description=description,
                is_active=not inactive,
                driver=driver,
                driver_opts=driver_opts,
                scheduler=scheduler,
                scheduler_opts=scheduler_opts,
            )
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('Scaling group creation has failed: {0}'.format(data['msg']))
            sys.exit(1)
        item = data['scaling_group']
        print_done('Scaling group name {0} is created.'.format(item['name']))


@scaling_group.command()
@click.argument('name', type=str, metavar='NAME')
@click.option('-d', '--description', type=str, default='',
              help='Description of new scaling group')
@click.option('-i', '--inactive', is_flag=True,
              help='New scaling group will be inactive.')
@click.option('--driver', type=str, default='static',
              help='Set driver.')
@click.option('--driver-opts', type=JSONParamType(), default=None,
              help='Set driver options as a JSON string.')
@click.option('--scheduler', type=str, default='fifo',
              help='Set scheduler.')
@click.option('--scheduler-opts', type=JSONParamType(), default=None,
              help='Set scheduler options as a JSON string.')
def update(name, description, inactive,
           driver, driver_opts, scheduler, scheduler_opts):
    """
    Update existing scaling group.

    NAME: Name of new scaling group.
    """
    with Session() as session:
        try:
            data = session.ScalingGroup.update(
                name,
                description=description,
                is_active=not inactive,
                driver=driver,
                driver_opts=driver_opts,
                scheduler=scheduler,
                scheduler_opts=scheduler_opts,
            )
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('Scaling group update has failed: {0}'.format(data['msg']))
            sys.exit(1)
        print_done('Scaling group {0} is updated.'.format(name))


@scaling_group.command()
@click.argument('name', type=str, metavar='NAME')
def delete(name):
    """
    Delete an existing scaling group.

    NAME: Name of a scaling group to delete.
    """
    with Session() as session:
        try:
            data = session.ScalingGroup.delete(name)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('Scaling group deletion has failed: {0}'.format(data['msg']))
            sys.exit(1)
        print_done('Scaling group is deleted: ' + name + '.')


@scaling_group.command()
@click.argument('scaling_group', type=str, metavar='SCALING_GROUP')
@click.argument('domain', type=str, metavar='DOMAIN')
def associate_scaling_group(scaling_group, domain):
    """
    Associate a domain with a scaling_group.

    \b
    SCALING_GROUP: The name of a scaling group.
    DOMAIN: The name of a domain.
    """
    with Session() as session:
        try:
            data = session.ScalingGroup.associate_domain(scaling_group, domain)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('Associating scaling group with domain failed: {0}'.format(data['msg']))
            sys.exit(1)
        print_done('Scaling group {} is assocatiated with domain {}.'.format(scaling_group, domain))


@scaling_group.command()
@click.argument('scaling_group', type=str, metavar='SCALING_GROUP')
@click.argument('domain', type=str, metavar='DOMAIN')
def dissociate_scaling_group(scaling_group, domain):
    """
    Dissociate a domain from a scaling_group.

    \b
    SCALING_GROUP: The name of a scaling group.
    DOMAIN: The name of a domain.
    """
    with Session() as session:
        try:
            data = session.ScalingGroup.dissociate_domain(scaling_group, domain)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('Dissociating scaling group from domain failed: {0}'.format(data['msg']))
            sys.exit(1)
        print_done('Scaling group {} is dissociated from domain {}.'.format(scaling_group, domain))
