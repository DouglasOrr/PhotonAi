import click


@click.command()
@click.argument('bot-a', type=click.Path(dir_okay=False, exists=True))
@click.argument('bot-b', type=click.Path(dir_okay=False, exists=True))
@click.argument('out', type=click.Path(exists=False))
def run():
    '''Run a single competitive game with two bots, and save the log.
    '''
    pass


run()
