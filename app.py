import flask

from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from flask_pyoidc import OIDCAuthentication
from flask_pyoidc.provider_configuration import ProviderConfiguration, ClientMetadata
from flask_pyoidc.user_session import UserSession

app = Flask(__name__)

app.config.update({'SERVER_NAME': 'localhost:5000',
                   'SECRET_KEY': 'dev_key',  # make sure to change this!!
                   'PERMANENT_SESSION_LIFETIME': 86400,
                   'PREFERRED_URL_SCHEME': 'http',
                   'DEBUG': True,
                   'SQLALCHEMY_DATABASE_URI': 'sqlite:///test.db'})

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

ISSUER1 = 'http://localhost:57480'
CLIENT1 = 'flask_pyoidc_test'
PROVIDER_NAME1 = 'bwh_authserver'
PROVIDER_CONFIG1 = ProviderConfiguration(issuer=ISSUER1,
                                         client_metadata=ClientMetadata(CLIENT1, 'secret'))

auth = OIDCAuthentication({PROVIDER_NAME1: PROVIDER_CONFIG1}, app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Task %r>' % self.id


@app.route('/', methods=['POST', 'GET'])
# @auth.oidc_auth(PROVIDER_NAME1)
def index():
    # user_session = UserSession(flask.session)

    if request.method == 'POST':
        task_content = request.form['content']
        new_task = Todo(content=task_content)

        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue adding your task'

    else:
        tasks = Todo.query.order_by(Todo.date_created).all()
        return render_template('index.html', tasks=tasks)


@app.route('/delete/<int:id>')
@auth.oidc_auth(PROVIDER_NAME1)
def delete(id):

    user_session = UserSession(flask.session)

    task_to_delete = Todo.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'There was a problem deleting that task'

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = Todo.query.get_or_404(id)

    if request.method == 'POST':
        task.content = request.form['content']

        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue updating your task'

    else:
        return render_template('update.html', task=task)

@app.route('/logout')
@auth.oidc_logout
def logout():
    return "You've been successfully logged out!"

if __name__ == "__main__":
    app.run(debug=True)
