from EpiML import app, db
from EpiML.db_tables import User, Job, Model


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Job': Job, 'Model': Model}


if __name__ == '__main__':
    app.run(debug=True)
