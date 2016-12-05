import click
from photonai import run, server, tourney


@click.group()
def cli():
    '''Top-level PhotonAI command line interface.
    '''
    pass


cli.add_command(run.cli)
cli.add_command(tourney.cli)
cli.add_command(server.cli)
