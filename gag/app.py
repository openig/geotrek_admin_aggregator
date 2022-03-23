import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config.from_pyfile('../config/config.py', silent=False)

DB = SQLAlchemy(app, session_options={"autoflush": False})

DB.init_app(app)


with app.app_context():
    from gag.commands import (
        fetch_api,
        test,
        populate_db
    )
    app.cli.add_command(fetch_api)
    app.cli.add_command(test)
    app.cli.add_command(populate_db)
