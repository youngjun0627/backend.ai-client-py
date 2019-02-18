import sys

import click
from tabulate import tabulate

from . import admin
from ...session import Session, is_legacy_server
from ..pretty import print_error


@admin.command()
@click.option('-i', '--id', 'agent_id', required=True,
              help='The agent Id to inspect.')
def agent(agent_id):
    '''
    Show the information about the given agent.
    '''
    fields = [
        ('ID', 'id'),
        ('Status', 'status'),
        ('Region', 'region'),
        ('First Contact', 'first_contact'),
        ('CPU Usage (%)', 'cpu_cur_pct'),
        ('Used Memory (MiB)', 'mem_cur_bytes'),
        ('Total slots', 'available_slots'),
        ('Occupied slots', 'occupied_slots'),
    ]
    if is_legacy_server():
        del fields[9]
        del fields[6]
    q = 'query($agent_id:String!) {' \
        '  agent(agent_id:$agent_id) { $fields }' \
        '}'
    q = q.replace('$fields', ' '.join(item[1] for item in fields))
    v = {'agent_id': agent_id}
    with Session() as session:
        try:
            resp = session.Admin.query(q, v)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        info = resp['agent']
        rows = []
        for name, key in fields:
            if key == 'mem_cur_bytes' and info[key] is not None:
                info[key] = round(info[key] / 2 ** 20, 1)
            if key in info:
                rows.append((name, info[key]))
        print(tabulate(rows, headers=('Field', 'Value')))


@admin.command()
@click.option('-s', '--status', type=str, default='ALIVE',
              help='Filter agents by the given status.')
@click.option('--all', is_flag=True, help='Display all agents.')
def agents(status, all):
    '''
    List and manage agents.
    (admin privilege required)
    '''
    fields = [
        ('ID', 'id'),
        ('Status', 'status'),
        ('Region', 'region'),
        ('First Contact', 'first_contact'),
        ('CPU Usage (%)', 'cpu_cur_pct'),
        ('Used Memory (MiB)', 'mem_cur_bytes'),
        ('Total slots', 'available_slots'),
        ('Occupied slots', 'occupied_slots'),
    ]
    if is_legacy_server():
        del fields[9]
        del fields[6]

    def execute_paginated_query(limit, offset):
            try:
                resp_agents = session.Agent.list_with_limit(limit, offset, status,
                                                            fields=(item[1] for item in fields))
            except Exception as e:
                print_error(e)
                sys.exit(1)
            return resp_agents

    def round_mem(results):
        for item in results:
            if 'mem_cur_bytes' in item and item['mem_cur_bytes'] is not None:
                item['mem_cur_bytes'] = round(item['mem_cur_bytes'] / 2 ** 20, 1)
        return results

    def _generate_paginated_results(interval):
        offset = 0
        is_first = True
        total_count = -1
        while True:
            limit = (interval if is_first else
                    min(interval, total_count - offset))
            try:
                result = execute_paginated_query(limit, offset)
            except Exception as e:
                print_error(e)
                sys.exit(1)
            offset += interval
            total_count = result['total_count']
            items = result['items']
            items = round_mem(items)
            table = tabulate((item.values() for item in items),
                                headers=(item[0] for item in fields))
            if is_first:
                is_first = False
            else:
                table_rows = table.split('\n')
                table = '\n'.join(table_rows[2:])
            yield table + '\n'

            if not offset < total_count:
                break

    with Session() as session:
        paginating_interval = 10
        if all:
            click.echo_via_pager(_generate_paginated_results(paginating_interval))
        else:
            result = execute_paginated_query(paginating_interval, offset=0)
            total_count = result['total_count']
            if total_count == 0:
                print('There are no matching agents.')
                return
            items = result['items']
            items = round_mem(items)
            fields = [field for field in fields if field[1] in items[0]]
            print(tabulate((item.values() for item in items),
                            headers=(item[0] for item in fields)))
            if total_count > paginating_interval:
                print("More agents can be displayed by using --all option.")