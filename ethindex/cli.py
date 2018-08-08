import click
import ethindex.pgimport


@click.group()
def cli():
    pass


cli.add_command(ethindex.pgimport.importabi)
cli.add_command(ethindex.pgimport.runsync)
cli.add_command(ethindex.pgimport.createtables)
cli.add_command(ethindex.pgimport.droptables)
