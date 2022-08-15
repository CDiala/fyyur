#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import sys
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment

import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

# from flask_sqlalchemy import SQLAlchemy

from models import Show, db, Venue, Artist
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#


app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)
# TODO: connect to a local postgresql database


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.

    venue_list = []

    # get all venues records
    venues = Venue.query.group_by(Venue.city, Venue.state, Venue.id).order_by(
        Venue.city, Venue.state, Venue.id).all()

    for venue in venues:

        venue_item = {
            "city": venue.city,
            "state": venue.state,
            "venues": [
                {
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": 0,
                }
            ]
        }

        # append venues if city already exists in venue_list.
        # Otherwise, add venue_item to venue list
        if len(venue_list) and venue_list[len(venue_list) - 1]['city'] == venue_item["city"]:
            venue_list[len(venue_list) -
                       1]['venues'].append(venue_item["venues"][0])
        else:
            venue_list.append(venue_item)

    return render_template('pages/venues.html', areas=venue_list)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

    response = {
        "count": 1,
        "data": [{
            "id": 2,
            "name": "The Dueling Pianos Bar",
            "num_upcoming_shows": 0,
        }]
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venues = db.session.query(Show).join(Venue, Show.venue_id == Venue.id).join(Artist, Artist.id == Show.artist_id).with_entities(
        Venue.id, Venue.name, Venue.genres, Venue.address, Venue.city,
        Venue.state, Venue.phone, Venue.website_link, Venue.facebook_link,
        Venue.seeking_talent, Venue.seeking_description, Venue.image_link,
        Artist.id, Artist.name, Artist.image_link, Show.start_time
    ).filter(Show.venue_id == venue_id).order_by(Venue.id).all()

    # sort shows into past & upcoming
    past_shows= []
    upcoming_shows= []

    for venue in venues:
        temp_show = {
            "artist_id": venue[12],
            "artist_name": venue[13],
            "artist_image_link": venue[14],
            "start_time": venue[15].strftime("%m/%d/%Y %H:%M:%S")
        }
        if venue[15] <= datetime.now():
            past_shows.append(temp_show)
        else:
            upcoming_shows.append(temp_show)

    new_data = {
        "id": venues[0][0],
        "name": venues[0][1],
        "genres": (venues[0][2]).split(","),
        "address": venues[0][3],
        "city": venues[0][4],
        "state": venues[0][5],
        "phone": venues[0][6],
        "website": venues[0][7],
        "facebook_link": venues[0][8],
        "seeking_talent": venues[0][9],
        "seeking_description": venues[0][10],
        "image_link": venues[0][11],
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    # data = list(filter(lambda d: d['id'] ==
    #             venue_id, [data1, data2, data3]))[0]
    return render_template('pages/show_venue.html', venue=new_data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

    venue_form = VenueForm(request.form)

    if (venue_form.validate()):
        try:
            new_venue = Venue(
                name=venue_form.name.data,
                city=venue_form.city.data,
                state=venue_form.state.data,
                address=venue_form.address.data,
                phone=venue_form.phone.data,
                image_link=venue_form.image_link.data,
                genres=",".join(venue_form.genres.data),
                facebook_link=venue_form.facebook_link.data,
                website_link=venue_form.website_link.data,
                seeking_talent=venue_form.seeking_talent.data,
                seeking_description=venue_form.seeking_description.data
            )

            db.session.add(new_venue)
            db.session.commit()
            flash('Venue ' + request.form['name'] +
                  ' was successfully listed!')
        except:
            db.session.rollback()
            flash('An error occurred. Venue ' +
                  request.form['name'] + ' could not be listed.\n' + sys.exc_info())
        finally:
            db.session.close()
            return redirect(url_for('index'))
    else:
        flash('An error occurred. Check form inputs and try again.')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database

    artist_list = []

    artists = Artist.query.order_by(Artist.id).all()

    for artist in artists:
        new_artist = {
            "id": artist.id,
            "name": artist.name
        }
        artist_list.append(new_artist)

    print(artist_list)

    return render_template('pages/artists.html', artists=artist_list)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    response = {
        "count": 1,
        "data": [{
            "id": 4,
            "name": "Guns N Petals",
            "num_upcoming_shows": 0,
        }]
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    data1 = {
        "id": 4,
        "name": "Guns N Petals",
        "genres": ["Rock n Roll"],
        "city": "San Francisco",
        "state": "CA",
        "phone": "326-123-5000",
        "website": "https://www.gunsnpetalsband.com",
        "facebook_link": "https://www.facebook.com/GunsNPetals",
        "seeking_venue": True,
        "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
        "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
        "past_shows": [{
            "venue_id": 1,
            "venue_name": "The Musical Hop",
            "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
            "start_time": "2019-05-21T21:30:00.000Z"
        }],
        "upcoming_shows": [],
        "past_shows_count": 1,
        "upcoming_shows_count": 0,
    }
    data2 = {
        "id": 5,
        "name": "Matt Quevedo",
        "genres": ["Jazz"],
        "city": "New York",
        "state": "NY",
        "phone": "300-400-5000",
        "facebook_link": "https://www.facebook.com/mattquevedo923251523",
        "seeking_venue": False,
        "image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
        "past_shows": [{
            "venue_id": 3,
            "venue_name": "Park Square Live Music & Coffee",
            "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
            "start_time": "2019-06-15T23:00:00.000Z"
        }],
        "upcoming_shows": [],
        "past_shows_count": 1,
        "upcoming_shows_count": 0,
    }
    data3 = {
        "id": 6,
        "name": "The Wild Sax Band",
        "genres": ["Jazz", "Classical"],
        "city": "San Francisco",
        "state": "CA",
        "phone": "432-325-5432",
        "seeking_venue": False,
        "image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "past_shows": [],
        "upcoming_shows": [{
            "venue_id": 3,
            "venue_name": "Park Square Live Music & Coffee",
            "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
            "start_time": "2035-04-01T20:00:00.000Z"
        }, {
            "venue_id": 3,
            "venue_name": "Park Square Live Music & Coffee",
            "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
            "start_time": "2035-04-08T20:00:00.000Z"
        }, {
            "venue_id": 3,
            "venue_name": "Park Square Live Music & Coffee",
            "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
            "start_time": "2035-04-15T20:00:00.000Z"
        }],
        "past_shows_count": 0,
        "upcoming_shows_count": 3,
    }
    data = list(filter(lambda d: d['id'] ==
                artist_id, [data1, data2, data3]))[0]
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = {
        "id": 4,
        "name": "Guns N Petals",
        "genres": ["Rock n Roll"],
        "city": "San Francisco",
        "state": "CA",
        "phone": "326-123-5000",
        "website": "https://www.gunsnpetalsband.com",
        "facebook_link": "https://www.facebook.com/GunsNPetals",
        "seeking_venue": True,
        "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
        "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
    }
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

    venue_detail = Venue.query.get(venue_id)
    
    form = VenueForm()

    venue = {
        "id": venue_detail.id,
        "name": venue_detail.name,
        "genres": venue_detail.genres.split(","),
        "address": venue_detail.address,
        "city": venue_detail.city,
        "state": venue_detail.state,
        "phone": venue_detail.phone,
        "website": venue_detail.website_link,
        "facebook_link": venue_detail.facebook_link,
        "seeking_talent": venue_detail.seeking_talent,
        "seeking_description": venue_detail.seeking_description,
        "image_link": venue_detail.image_link,
    }

    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

    venue_form = VenueForm(request.form)

    if (venue_form.validate()):
        try:
            venue_info = Venue.query.get(venue_id)
            venue_info.name = venue_form.name.data
            venue_info.city = venue_form.city.data
            venue_info.state = venue_form.state.data
            venue_info.address = venue_form.address.data
            venue_info.phone = venue_form.phone.data
            venue_info.image_link = venue_form.image_link.data
            venue_info.genres = ",".join(venue_form.genres.data)
            venue_info.facebook_link = venue_form.facebook_link.data
            venue_info.website_link = venue_form.website_link.data
            venue_info.seeking_talent = venue_form.seeking_talent.data
            venue_info.seeking_description = venue_form.seeking_description.data

            db.session.commit()
            flash(venue_form.name.data + ' was successfully updated!')
        except:
            db.session.rollback()
            flash('An error occurred. ' + venue_form.name.data + ' could not be updated. \n' + sys.exc_info())

        finally:
            db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    artist_form = ArtistForm(request.form)

    if (artist_form.validate()):
        try:
            new_artist = Artist(
                name=artist_form.name.data,
                city=artist_form.city.data,
                state=artist_form.state.data,
                phone=artist_form.phone.data,
                image_link=artist_form.image_link.data,
                genres=",".join(artist_form.genres.data),
                facebook_link=artist_form.facebook_link.data,
                website_link=artist_form.website_link.data,
                seeking_venue=artist_form.seeking_venue.data,
                seeking_description=artist_form.seeking_description.data,
            )

            db.session.add(new_artist)
            db.session.commit()
            flash('Artist ' + request.form['name'] +
                  ' was successfully listed!')

        except:
            db.session.rollback()
            flash('An error occurred. Artist ' +
                  request.form['name'] + ' could not be listed.\n' + sys.exc_info())

        finally:
            db.session.close()
            return redirect(url_for('index'))
    else:
        flash('An error occurred. Check form inputs and try again.' + sys.exc_info())

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    # return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.

    shows_list = []

    # fetch required records from related tables
    shows = db.session.query(Show).join(Artist, Artist.id == Show.artist_id).join(Venue, Venue.id == Show.venue_id).with_entities(
        Show.venue_id, Venue.name, Show.artist_id, Artist.name, Artist.image_link, Show.start_time
    ).all()

    for show in shows:
        show_info = {
            "venue_id": show[0],
            "venue_name": show[1],
            "artist_id": show[2],
            "artist_name": show[3],
            "artist_image_link": show[4],
            "start_time": show[5].strftime("%m/%d/%Y %H:%M:%S")
            }
        shows_list.append(show_info)

    return render_template('pages/shows.html', shows=shows_list)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead

    show_form = ShowForm(request.form)

    if (show_form.validate()):
        try:
            new_show = Show(
                artist_id = show_form.artist_id.data,
                venue_id = show_form.venue_id.data,
                start_time = show_form.start_time.data
            )

            db.session.add(new_show)
            db.session.commit()
            flash('Show was successfully listed!')
        except:
            db.session.rollback()
            flash('An error occurred. Show could not be listed. \n' + sys.exc_info())
        finally:
            db.session.close()

    # on successful db insert, flash success
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=3000)
