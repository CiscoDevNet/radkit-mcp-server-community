#!/usr/bin/env python3
import sys
import base64
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
import questionary

console = Console()

def onboard_user():
    """Handles non-interactive Cisco RADKit authentication onboarding."""
    username = questionary.text("Enter Cisco RADKit username:").ask()
    if not username:
        console.print("[red]Username cannot be empty.[/red]")
        sys.exit(1)

    try:
        from radkit_client.sync import Client
    except ImportError:
        console.print("[red]Error: radkit_client not installed. Please run this tool from the virtualenv provided.[/red]")
        sys.exit(1)

    console.print(Panel.fit(f"Starting Cisco RADKit onboarding for user: [bold cyan]{username}[/bold cyan]"))

    try:
        with Client.create() as client:
            client.sso_login(username).enroll_client()
        console.print("[green]✅ Onboarding completed successfully![/green]")
    except Exception as ex:
        console.print(f"[red]❌ Error during onboarding: {str(ex)}[/red]")
        sys.exit(1)


def generate_env():
    """Generates .env file for Cisco RADKit MCP server."""
    console.print(Panel.fit(
        "[bold yellow]Warning:[/bold yellow] Make sure Cisco RADKit certificates for this username already exist.\n"
        "If not, run the onboarding process first using option 1."
    ))

    username = questionary.text("Enter Cisco RADKit username:").ask()
    service_code = questionary.text("Enter Cisco RADKit service code:").ask()
    password = questionary.password("Enter non-interactive authentication password:").ask()

    if not all([username, service_code, password]):
        console.print("[red]All fields are required.[/red]")
        sys.exit(1)

    encoded_pw = base64.b64encode(password.encode("utf-8")).decode("utf-8")

    env_content = (
        f"RADKIT_CLIENT_PRIVATE_KEY_PASSWORD_BASE64={encoded_pw}\n"
        f"RADKIT_SERVICE_USERNAME={username}\n"
        f"RADKIT_SERVICE_CODE={service_code}\n"
    )

    Path(".env").write_text(env_content)
    console.print(Panel.fit("[green]✅ .env file generated successfully![/green]\nSaved as [bold].env[/bold]"))


def main():
    console.print(Panel.fit("[bold cyan]🚀 Cisco RADKit MCP Server Utility Tool[/bold cyan]", border_style="cyan"))

    while True:
        choice = questionary.select(
            "Choose an option:",
            choices=[
                "1. 👾 Onboard user to non-interactive Cisco RADKit authentication",
                "2. 📚 Generate .env file for Cisco RADKit MCP server",
                "Exit",
            ],
        ).ask()

        if choice.startswith("1"):
            onboard_user()
        elif choice.startswith("2"):
            generate_env()
        else:
            console.print("[bold green]Goodbye![/bold green]")
            sys.exit(0)


if __name__ == "__main__":
    main()
