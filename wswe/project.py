from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify
)
from database_setup import *

app = Flask(__name__)


@app.route('/')
@app.route('/restaurants/')
def listRestaurants():
    with session_scope() as session:
        restaurants = session.query(Restaurant).order_by(Restaurant.name).all()
        return render_template('index.html', restaurants=restaurants)


@app.route('/restaurants/new/', methods=['GET', 'POST'])
def addRestaurant():
    if (request.method == 'POST'):
        newRestaurant = Restaurant(
            name=request.form['name'],
            description=request.form['description']
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
    if (request.method == 'POST'):
        with session_scope() as session:
            restaurant = session.query(Restaurant).filter_by(
                id=restaurant_id).one()
            session.delete(restaurant)
        flash('Restaurant deleted!')

        return redirect(url_for('listRestaurants'))
    else:
        with session_scope() as session:
            restaurant = session.query(Restaurant).filter_by(
                id=restaurant_id).one()
            return render_template(
                'deleterestaurant.html',
                restaurant_id=restaurant_id,
                name=restaurant.name
            )


@app.route('/restaurants/<int:restaurant_id>/edit/', methods=['GET', 'POST'])
def updateRestaurant(restaurant_id):
    if (request.method == 'POST'):
        with session_scope() as session:
            restaurant = session.query(Restaurant).filter_by(
                id=restaurant_id).one()
            restaurant.name = request.form['name']
            restaurant.description = request.form['description']
            session.add(restaurant)
        flash('Restaurant edited successfully!')

        return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
    else:
        with session_scope() as session:
            restaurant = session.query(Restaurant).filter_by(
                id=restaurant_id).one()
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
        return render_template(
            'restaurant.html', restaurant=restaurant, items=items)


@app.route('/restaurants/<int:restaurant_id>/new/', methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
    if (request.method == 'POST'):
        newItem = MenuItem(
            name=request.form['name'],
            description=request.form['description'],
            price=request.form['price'],
            course=request.form['course'],
            restaurant_id=restaurant_id
        )
        with session_scope() as session:
            session.add(newItem)
        flash('New menu item created!')
        return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
    else:
        return render_template('newmenuitem.html', restaurant_id=restaurant_id)


@app.route(
    '/restaurants/<int:restaurant_id>/<int:menu_id>/edit/',
    methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    if (request.method == 'POST'):
        with session_scope() as session:
            item = session.query(MenuItem).filter_by(id=menu_id).one()
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
    if (request.method == 'POST'):
        with session_scope() as session:
            item = session.query(MenuItem).filter_by(id=menu_id).one()
            session.delete(item)
        flash('Menu item deleted!')

        return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
    else:
        with session_scope() as session:
            item = session.query(MenuItem).filter_by(id=menu_id).one()
            item_name = item.name
        return render_template(
            'deletemenuitem.html',
            restaurant_id=restaurant_id,
            menu_id=menu_id,
            item_name=item_name
        )


if (__name__) == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
