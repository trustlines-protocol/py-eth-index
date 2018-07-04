import click
import ethindex.pgimport


@click.group()
def cli():
    pass


cli.add_command(ethindex.pgimport.importabi)
cli.add_command(ethindex.pgimport.runsync)
