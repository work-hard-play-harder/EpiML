from EpiML import app, db
from EpiML.db_tables import Job, Model



@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Job': Job, 'Model': Model}


if __name__ == '__main__':
    # app.run(ssl_context=('cert.pem','key.pem'), host='0.0.0.0', port=80)
    app.run(ssl_context=('cert.pem', 'key.pem'), host='0.0.0.0', port=80)
