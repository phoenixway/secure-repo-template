import click

# Використовуємо стилізацію від Click для кольорів
def echo_info(msg):
    click.echo(click.style(f"[i] {msg}", fg="blue"))

def echo_success(msg):
    click.echo(click.style(f"[✓] {msg}", fg="green"))

def echo_warning(msg):
    click.echo(click.style(f"[!] {msg}", fg="yellow"))

def echo_error(msg):
    click.echo(click.style(f"[✗] {msg}", fg="red"))
    
def echo_step(msg):
    click.echo(click.style(f"\n==> {msg}", fg="yellow"))

def prompt_yes_no(prompt):
    return click.confirm(prompt, default=False)