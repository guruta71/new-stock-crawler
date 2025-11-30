"""
Stock Crawler CLI - 단일 진입점
"""
import typer
from interface.cli.commands.full_crawl import full_crawl
from interface.cli.commands.daily_update import daily_update
from interface.cli.commands.enrich_data import enrich_data
from interface.cli.commands.auth import auth_drive

app = typer.Typer(help="IPO 데이터 크롤러 CLI")

app.command("full")(full_crawl)
app.command("daily")(daily_update)
app.command("enrich")(enrich_data)
app.command("auth")(auth_drive)

if __name__ == "__main__":
    app()
