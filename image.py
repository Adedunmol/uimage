import sys
import click
from app.models import Permissions
import os
from app import create_app, db
from flask_migrate import Migrate, upgrade
from app.models import User, Role
import subprocess
from flask import current_app


COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()


app = create_app(os.environ.get('FLASK_CONFIG') or 'default')
Migrate(app, db)


@app.shell_context_processor
def shell_contexts():
    return dict(db=db, User=User, Role=Role, Permissions=Permissions)

@app.cli.command()
@click.option('--coverage/--no-coverage', help='Run tests under coverage.', default=False)
def test(coverage):
     """ Runs the test in the tests directoory """
     if coverage and not os.environ.get('FLASK_COVERAGE'):
         os.environ['FLASK_COVERAGE'] = '1'
         sys.exit(subprocess.call(sys.argv))
         
     import unittest

     tests = unittest.TestLoader().discover('tests')
     unittest.TextTestRunner(verbosity=2).run(tests)
     if COV:
         COV.stop()
         COV.save()
         print('Coverage Summary:')
         COV.report()
         basedir = os.path.abspath(os.path.dirname(__file__))
         covdir = os.path.join(basedir, 'tmp/coverage')
         COV.html_report(directory=covdir)
         print(f'HTML Version: file://{covdir}/index.html')
         COV.erase()


@app.cli.command()
def deploy():
    """Run deployment tasks."""

    #migrate database to latest version
    upgrade()

    #create or update roles
    Role.insert_roles()

    #ensure users are following themselves
    User.add_self_follows()