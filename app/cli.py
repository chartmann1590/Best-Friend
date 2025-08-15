import click
from flask.cli import with_appcontext
from app import db
from app.models import User
import os

@click.command('create-admin')
@with_appcontext
def create_admin():
    """Create admin user."""
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@bestfriend.local')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    # Check if admin already exists
    admin = User.query.filter_by(email=admin_email).first()
    if admin:
        click.echo(f'Admin user {admin_email} already exists.')
        return
    
    # Create admin user
    admin = User(
        email=admin_email,
        name='Administrator',
        is_admin=True
    )
    admin.set_password(admin_password)
    
    db.session.add(admin)
    db.session.commit()
    
    click.echo(f'Admin user created: {admin_email}')
    click.echo(f'Password: {admin_password}')
    click.echo('⚠️  Please change the password after first login!')

def init_app(app):
    """Initialize CLI commands."""
    app.cli.add_command(create_admin)
