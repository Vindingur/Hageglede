# PURPOSE: Re-exports close_connection from the db package so that
# `from db.utils import close_connection` in pipeline.py resolves correctly.
from db import close_connection
