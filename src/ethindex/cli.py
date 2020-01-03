import click
import pkg_resources

import ethindex.pgimport


def report_version():
    click.echo(pkg_resources.get_distribution("eth-index").version)


@click.group(invoke_without_command=True)
@click.option("--version", help="Prints the version of the software", is_flag=True)
@click.pass_context
def cli(ctx, version):
    if version:
        report_version()
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit()


cli.add_command(ethindex.pgimport.importabi)
cli.add_command(ethindex.pgimport.runsync)
cli.add_command(ethindex.pgimport.createtables)
cli.add_command(ethindex.pgimport.droptables)
