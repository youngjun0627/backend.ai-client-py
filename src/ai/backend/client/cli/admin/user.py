from __future__ import annotations

import sys

import click

from ai.backend.client.session import Session
from ai.backend.client.output.fields import user_fields
from ..interaction import ask_yn
from ..pretty import print_error, print_info, print_fail
from ..types import CLIContext
from . import admin


@admin.group()
def user() -> None:
    """
    User administration commands.
    """


@user.command()
@click.pass_obj
@click.option('-e', '--email', type=str, default=None,
              help='Email of a user to display.')
def info(ctx: CLIContext, email: str) -> None:
    """
    Show the information about the given user by email. If email is not give,
    requester's information will be displayed.
    """
    fields = [
        user_fields['uuid'],
        user_fields['username'],
        user_fields['role'],
        user_fields['email'],
        user_fields['full_name'],
        user_fields['need_password_change'],
        user_fields['status'],
        user_fields['status_info'],
        user_fields['created_at'],
        user_fields['domain_name'],
        user_fields['groups'],
    ]
    with Session() as session:
        try:
            item = session.User.detail(email=email, fields=fields)
            ctx.output.print_item(item, fields=fields)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(1)


@user.command()
@click.pass_obj
@click.option('-s', '--status', type=str, default=None,
              help='Filter users in a specific state (active, inactive, deleted, before-verification).')
@click.option('-g', '--group', type=str, default=None,
              help='Filter by group ID.')
@click.option('--filter', 'filter_', default=None,
              help='Set the query filter expression.')
@click.option('--order', default=None,
              help='Set the query ordering expression.')
@click.option('--offset', default=0,
              help='The index of the current page start for pagination.')
@click.option('--limit', default=None,
              help='The page size for pagination.')
def list(ctx: CLIContext, status, group, filter_, order, offset, limit) -> None:
    """
    List users.
    (admin privilege required)
    """
    fields = [
        user_fields['uuid'],
        user_fields['username'],
        user_fields['role'],
        user_fields['email'],
        user_fields['full_name'],
        user_fields['need_password_change'],
        user_fields['status'],
        user_fields['status_info'],
        user_fields['created_at'],
        user_fields['domain_name'],
        user_fields['groups'],
    ]
    try:
        with Session() as session:
            fetch_func = lambda pg_offset, pg_size: session.User.paginated_list(
                status, group,
                fields=fields,
                page_offset=pg_offset,
                page_size=pg_size,
                filter=filter_,
                order=order,
            )
            ctx.output.print_paginated_list(
                fetch_func,
                initial_page_offset=offset,
                page_size=limit,
            )
    except Exception as e:
        ctx.output.print_error(e)
        sys.exit(1)


@user.command()
@click.argument('domain_name', type=str, metavar='DOMAIN_NAME')
@click.argument('email', type=str, metavar='EMAIL')
@click.argument('password', type=str, metavar='PASSWORD')
@click.option('-u', '--username', type=str, default='', help='Username.')
@click.option('-n', '--full-name', type=str, default='', help='Full name.')
@click.option('-r', '--role', type=str, default='user',
              help='Role of the user. One of (admin, user, monitor).')
@click.option('-s', '--status', type=str, default='active',
              help='Account status. One of (active, inactive, deleted, before-verification).')
@click.option('--need-password-change', is_flag=True,
              help='Flag indicate that user needs to change password. '
                   'Useful when admin manually create password.')
@click.option('--description', type=str, default='', help='Description of the user.')
def add(domain_name, email, password, username, full_name, role, status,
        need_password_change, description):
    """
    Add new user. A user must belong to a domain, so DOMAIN_NAME should be provided.

    \b
    DOMAIN_NAME: Name of the domain where new user belongs to.
    EMAIL: Email of new user.
    PASSWORD: Password of new user.
    """
    with Session() as session:
        try:
            data = session.User.create(
                domain_name, email, password,
                username=username, full_name=full_name, role=role,
                status=status,
                need_password_change=need_password_change,
                description=description,
            )
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('User creation has failed: {0}'.format(data['msg']))
            sys.exit(1)
        item = data['user']
        print('User {0} is created in domain {1}.'.format(item['email'], item['domain_name']))


@user.command()
@click.argument('email', type=str, metavar='EMAIL')
@click.option('-p', '--password', type=str, help='Password.')
@click.option('-u', '--username', type=str, help='Username.')
@click.option('-n', '--full-name', type=str, help='Full name.')
@click.option('-d', '--domain-name', type=str, help='Domain name.')
@click.option('-r', '--role', type=str, default='user',
              help='Role of the user. One of (admin, user, monitor).')
@click.option('-s', '--status', type=str,
              help='Account status. One of (active, inactive, deleted, before-verification).')
@click.option('--need-password-change', is_flag=True,
              help='Flag indicate that user needs to change password. '
                   'Useful when admin manually create password.')
@click.option('--description', type=str, default='', help='Description of the user.')
def update(email, password, username, full_name, domain_name, role, status,
           need_password_change, description):
    """
    Update an existing user.

    EMAIL: Email of user to update.
    """
    with Session() as session:
        try:
            data = session.User.update(
                email,
                password=password, username=username, full_name=full_name,
                domain_name=domain_name,
                role=role, status=status, need_password_change=need_password_change,
                description=description,
            )
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('User update has failed: {0}'.format(data['msg']))
            sys.exit(1)
        print('User {0} is updated.'.format(email))


@user.command()
@click.argument('email', type=str, metavar='EMAIL')
def delete(email):
    """
    Inactivate an existing user.

    EMAIL: Email of user to inactivate.
    """
    with Session() as session:
        try:
            data = session.User.delete(email)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('User inactivation has failed: {0}'.format(data['msg']))
            sys.exit(1)
        print('User is inactivated: ' + email + '.')


@user.command()
@click.argument('email', type=str, metavar='EMAIL')
@click.option('--purge-shared-vfolders', is_flag=True, default=False,
              help='Delete user\'s all virtual folders. '
                   'If False, shared folders will not be deleted '
                   'and migrated the ownership to the requested admin.')
def purge(email, purge_shared_vfolders):
    """
    Delete an existing user. This action cannot be undone.

    NAME: Name of a domain to delete.
    """
    with Session() as session:
        try:
            if not ask_yn():
                print_info('Cancelled')
                sys.exit(1)
            data = session.User.purge(email, purge_shared_vfolders)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('User deletion has failed: {0}'.format(data['msg']))
            sys.exit(1)
        print('User is deleted: ' + email + '.')
