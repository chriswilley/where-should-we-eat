import httplib2
import json
import random
import requests
import string

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session as login_session,
    make_response
)

from oauth2client.client import flow_from_clientsecrets, FlowExchangeError

from database_setup import *

app = Flask(__name__)
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


@app.route('/login/')
def showLogin():
    state = ''.join(random.choice(
        string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    if (request.args.get('state') != login_session['state']):
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data

    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
        % access_token
    )
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    if (result.get('error') is not None):
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
    gplus_id = credentials.id_token['sub']

    if (result['user_id'] != gplus_id):
        response.make_response(
            json.dumps('Token\'s user ID doesn\'t match given user ID.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    if (result['issued_to'] != CLIENT_ID):
        response.make_response(
            json.dumps('Token\'s client ID doesn\'t match app\'s.'), 401)
        print 'Token\'s client ID doesn\' match app\'s'
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if (stored_credentials is not None and gplus_id == stored_gplus_id):
        response = make_response(
            json.dumps('Current user is already connected'), 200)
        response.headers['Content-Type'] = 'application/json'

    login_session['provider'] = 'google'
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not (user_id):
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' style="width: 300px; height: 300px; border-radius: 150px; '
    output += '-webkit-border-radius: 150px; -moz-border-radius: 150px;">'
    flash('You are now logged in as %s' % login_session['username'])
    return output


@app.route('/gdisconnect')
def gdisconnect():
    credentials = login_session.get('credentials')
    if (credentials is None):
        response = make_response(
            json.dumps('Current user is not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if (result['status'] == '200'):
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if (request.args.get('state') != login_session['state']):
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data

    app_id = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type='
    url += 'fb_exchange_token&client_id=%s' % app_id
    url += '&client_secret=%s' % app_secret
    url += '&fb_exchange_token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # userinfo_url = 'https://graph.facebook.com/v2.5/me'
    token = result.split('&')[0]

    url = 'https://graph.facebook.com/v2.5/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['facebook_id'] = data['id']

    url = 'https://graph.facebook.com/v2.5/me/picture?%s' % token
    url += '&redirect=0&height=200&width=200'
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data['data']['url']

    user_id = getUserID(login_session['email'])
    if not (user_id):
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' style="width: 300px; height: 300px; border-radius: 150px; '
    output += '-webkit-border-radius: 150px; -moz-border-radius: 150px;">'
    flash('You are now logged in as %s' % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    access_token = login_session['access_token']
    url = 'https://graphs.facebook.com/%s' % facebook_id
    url += '/permissions?access_token=%s' % access_token
    h = httplib2.Http()
    h.request(url, 'DELETE')[1]
    return 'You have been logged out'


@app.route('/disconnect')
def disconnect():
    if ('provider' in login_session):
        if (login_session['provider'] == 'google'):
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']

        if (login_session['provider'] == 'facebook'):
            fbdisconnect()
            del login_session['facebook_id']

        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash('You have been successfully logged out.')
        return redirect(url_for('listRestaurants'))
    else:
        flash('You were not logged in to begin with!')
        return redirect(url_for('listRestaurants'))


@app.route('/')
@app.route('/restaurants/')
def listRestaurants():
    with session_scope() as session:
        restaurants = session.query(Restaurant).order_by(Restaurant.name).all()
        try:
            user_id = login_session['user_id']
        except:
            user_id = 0

        print login_session
        if ('username' not in login_session):
            return render_template(
                'index_public.html', restaurants=restaurants)
        else:
            return render_template(
                'index.html', restaurants=restaurants, user=user_id)


@app.route('/restaurants/new/', methods=['GET', 'POST'])
def addRestaurant():
    if ('username' not in login_session):
        return redirect('/login')

    if (request.method == 'POST'):
        newRestaurant = Restaurant(
            name=request.form['name'],
            description=request.form['description'],
            user_id=login_session['user_id']
        )
        with session_scope() as session:
            session.add(newRestaurant)
        flash('New restaurant created!')
        return redirect(url_for('listRestaurants'))
    else:
        return render_template('newrestaurant.html')


@app.route(
    '/restaurants/<int:restaurant_id>/delete/',
    methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    if ('username' not in login_session):
        return redirect('/login')

    if (request.method == 'POST'):
        with session_scope() as session:
            restaurant = session.query(Restaurant).filter_by(
                id=restaurant_id).one()
            if (login_session['user_id'] == restaurant.user_id):
                session.delete(restaurant)
                flash('Restaurant deleted!')

        return redirect(url_for('listRestaurants'))
    else:
        with session_scope() as session:
            restaurant = session.query(Restaurant).filter_by(
                id=restaurant_id).one()
            if (login_session['user_id'] != restaurant.user_id):
                return redirect(url_for('listRestaurants'))

            return render_template(
                'deleterestaurant.html',
                restaurant_id=restaurant_id,
                name=restaurant.name
            )


@app.route('/restaurants/<int:restaurant_id>/edit/', methods=['GET', 'POST'])
def updateRestaurant(restaurant_id):
    if ('username' not in login_session):
        return redirect('/login')

    if (request.method == 'POST'):
        with session_scope() as session:
            restaurant = session.query(Restaurant).filter_by(
                id=restaurant_id).one()
            if (login_session['user_id'] != restaurant.user_id):
                return redirect('/restaurants')
            restaurant.name = request.form['name']
            restaurant.description = request.form['description']
            session.add(restaurant)
        flash('Restaurant edited successfully!')

        return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
    else:
        with session_scope() as session:
            restaurant = session.query(Restaurant).filter_by(
                id=restaurant_id).one()
            if (login_session['user_id'] != restaurant.user_id):
                return redirect('/restaurants')

            return render_template(
                'editrestaurant.html',
                restaurant_id=restaurant.id,
                name=restaurant.name,
                description=restaurant.description
            )


@app.route('/restaurants/<int:restaurant_id>/menu/JSON/')
def restaurantMenuJSON(restaurant_id):
    with session_scope() as session:
        restaurant = session.query(Restaurant).filter_by(
            id=restaurant_id).one()
        items = session.query(MenuItem).filter_by(
            restaurant_id=restaurant.id).order_by(MenuItem.name)
        return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON/')
def menuItemJSON(restaurant_id, menu_id):
    with session_scope() as session:
        item = session.query(MenuItem).filter_by(
            id=menu_id).one()
        return jsonify(MenuItem=item.serialize)


@app.route('/restaurants/<int:restaurant_id>/')
def restaurantMenu(restaurant_id):
    with session_scope() as session:
        restaurant = session.query(Restaurant).filter_by(
            id=restaurant_id).one()
        items = session.query(MenuItem).filter_by(
            restaurant_id=restaurant.id
        ).order_by(MenuItem.course, MenuItem.name)

        try:
            user_id = login_session['user_id']
        except:
            user_id = 0

        if ('username' not in login_session):
            return render_template(
                'restaurant_public.html', restaurant=restaurant, items=items)
        else:
            return render_template(
                'restaurant.html',
                restaurant=restaurant,
                items=items,
                user=user_id
            )


@app.route('/restaurants/<int:restaurant_id>/new/', methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
    if ('username' not in login_session):
        return redirect('/login')

    if (request.method == 'POST'):
        newItem = MenuItem(
            name=request.form['name'],
            description=request.form['description'],
            price=request.form['price'],
            course=request.form['course'],
            restaurant_id=restaurant_id,
            user_id=login_session['user_id']
        )
        with session_scope() as session:
            r = session.query(Restaurant).filter_by(id=restaurant_id).one()
            if (login_session['user_id'] == r.user_id):
                session.add(newItem)
                flash('New menu item created!')

        return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
    else:
        with session_scope() as session:
            r = session.query(Restaurant).filter_by(id=restaurant_id).one()
            if (login_session['user_id'] != r.user_id):
                return redirect(
                    url_for('restaurantMenu', restaurant_id=restaurant_id))

        return render_template('newmenuitem.html', restaurant_id=restaurant_id)


@app.route(
    '/restaurants/<int:restaurant_id>/<int:menu_id>/edit/',
    methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    if ('username' not in login_session):
        return redirect('/login')

    if (request.method == 'POST'):
        with session_scope() as session:
            item = session.query(MenuItem).filter_by(id=menu_id).one()
            if (login_session['user_id'] == item.user_id):
                item.name = request.form['name']
                item.description = request.form['description']
                item.price = request.form['price']
                item.course = request.form['course']
                session.add(item)
                flash('Menu item edited successfully!')

        return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
    else:
        with session_scope() as session:
            item = session.query(MenuItem).filter_by(id=menu_id).one()
            if (login_session['user_id'] != item.user_id):
                return redirect(
                    url_for('restaurantMenu', restaurant_id=restaurant_id))

            return render_template(
                'editmenuitem.html',
                restaurant_id=restaurant_id,
                menu_id=menu_id,
                item_name=item.name,
                description=item.description,
                price=item.price,
                course=item.course
            )


@app.route(
    '/restaurants/<int:restaurant_id>/<int:menu_id>/delete/',
    methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    if ('username' not in login_session):
        return redirect('/login')

    if (request.method == 'POST'):
        with session_scope() as session:
            item = session.query(MenuItem).filter_by(id=menu_id).one()
            if (login_session['user_id'] == item.user_id):
                session.delete(item)
                flash('Menu item deleted!')

        return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
    else:
        with session_scope() as session:
            item = session.query(MenuItem).filter_by(id=menu_id).one()
            item_name = item.name
            if (login_session['user_id'] != item.user_id):
                return redirect(
                    url_for('restaurantMenu', restaurant_id=restaurant_id))

        return render_template(
            'deletemenuitem.html',
            restaurant_id=restaurant_id,
            menu_id=menu_id,
            item_name=item_name
        )


def createUser(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture']
    )
    with session_scope() as session:
        session.add(newUser)
        user = session.query(User).filter_by(
            email=login_session['email']).one()
        return user.id


def getUserInfo(user_id):
    with session_scope() as session:
        user = session.query(User).filter_by(id=user_id).one()
        return user


def getUserID(email):
    with session_scope() as session:
        try:
            user = session.query(User).filter_by(email=email).one()
            return user.id
        except:
            return None


if (__name__) == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
