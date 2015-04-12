import muffin
from example import app

from example.models import User, Test


# Add to context providers
@app.ps.jade.ctx_provider
def add_constant():
    """ This method implements a template context provider. """
    return {'MUFFIN': 'ROCKS'}


# Setup an user loader
@app.ps.session.user_loader
def get_user(user_id):
    """ This provides a user loading procedure to the application. """
    return User.select().where(User.id == user_id).get()


@app.register('/')
def index(request):
    """ Get a current logged user and render a template. """
    user = yield from app.ps.session.load_user(request)
    return app.ps.jade.render('index.jade', user=user)


@app.register(muffin.sre('/login/?'), methods='POST')
def login(request):
    """ Implement user's login. """
    data = yield from request.post()
    user = User.select().where(User.email == data.get('email')).get()
    if user.check_password(data.get('password')):
        yield from app.ps.session.login(request, user.pk)

    return muffin.HTTPFound('/')


@app.register('/logout')
def logout(request):
    """ Implement user's logout. """
    yield from app.ps.session.logout(request)
    return muffin.HTTPFound('/')


# app.register supports multi paths
@app.register('/profile', '/auth')
# ensure that request user is logged to the application
@app.ps.session.user_pass(lambda u: u, '/')
def profile(request):
    return app.ps.jade.render('profile.jade', user=request.user)


@app.register('/db-sync')
def db_sync(request):
    return [t.data for t in Test.select()]


@app.register('/json')
def json(request):
    return {'json': 'here'}


@app.register('/404')
def raise404(request):
    raise muffin.HTTPNotFound


@app.register('/github')
@app.ps.oauth.login('github')
def oauth(request, client):
    response = yield from client.request('GET', 'user')
    json = yield from response.json()
    return json


@app.register('/db-async')
def db_async(request):
    results = yield from app.peewee.query(Test.select())
    return [t.data for t in results]


@app.register('/api/example', '/api/example/{example}')
class Example(muffin.Handler):

    def get(self, request):
        return {'simple': 'rest', 'example': request.match_info.get('example')}

    def post(self, request):
        return [1, 2, 3]