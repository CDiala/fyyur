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

    venue_list = []
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

    user_input = request.form.get('search_term')
    venue_result = db.session.query(Show).join(Venue, Show.venue_id == Venue.id).with_entities(
        Venue.id, Venue.name, Show.start_time).filter(
            Venue.name.ilike('%' + user_input + '%'), Show.start_time > datetime.now()).order_by(Venue.id).all()

    response = {
        "count": 0,
        "data": []
    }

    for venue in venue_result:
        # Increment num_upcoming_shows by 1 if last record in response dictionary has the same id as venue.id
        if (response["data"] and response["data"][len(response["data"]) - 1]["id"] == venue.id):
            response["data"][len(response["data"]) - 1]["num_upcoming_shows"] += 1
        else:
            data_item = {
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": 1,
            }
            response["count"] += 1
            response["data"].append(data_item)
    
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venues = db.session.query(Show).join(Venue, Show.venue_id == Venue.id).join(
        Artist, Artist.id == Show.artist_id).with_entities(
        Venue.id, Venue.name, Venue.genres, Venue.address, Venue.city,
        Venue.state, Venue.phone, Venue.website_link, Venue.facebook_link,
        Venue.seeking_talent, Venue.seeking_description, Venue.image_link,
        Artist.id, Artist.name, Artist.image_link, Show.start_time
    ).filter(Show.venue_id == venue_id).order_by(Venue.id).all()

    if venues:

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
    else:
        new_data = {}

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
                name = venue_form.name.data,
                city = venue_form.city.data,
                state = venue_form.state.data,
                address = venue_form.address.data,
                phone = venue_form.phone.data,
                image_link = venue_form.image_link.data,
                genres = ",".join(venue_form.genres.data),
                facebook_link = venue_form.facebook_link.data,
                website_link = venue_form.website_link.data,
                seeking_talent = venue_form.seeking_talent.data,
                seeking_description = venue_form.seeking_description.data
            )

            db.session.add(new_venue)
            db.session.commit()
            flash('Venue ' + request.form['name'] + ' was successfully listed!')
        except:
            db.session.rollback()
            flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.\n' + sys.exc_info())
        finally:
            db.session.close()
            return redirect(url_for('index'))
    else:
        flash('An error occurred. Check form inputs and try again.')


@app.route('/venues/<venue_id>/delete', methods=['POST'])
def delete_venue(venue_id):
    
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash('successfully deleted')
    except:
        db.session.rollback()
        flash('an error occurred.\n' + sys.exc_info())
    finally:
        db.session.close()
        return redirect(url_for('index'))


#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():

    artist_list = []
    artists = Artist.query.order_by(Artist.id).all()

    for artist in artists:
        new_artist = {
            "id": artist.id,
            "name": artist.name
        }
        artist_list.append(new_artist)

    return render_template('pages/artists.html', artists=artist_list)


@app.route('/artists/search', methods=['POST'])
def search_artists():

    user_input = request.form.get('search_term')
    artist_result = db.session.query(Artist).join(Show, Show.artist_id == Artist.id).with_entities(Artist.id, Artist.name, Show.start_time).filter(Artist.name.ilike('%' + user_input + '%'), Show.start_time > datetime.now()).order_by(Artist.id).all()

    response = {
        "count": 0,
        "data": []
    }

    for artist in artist_result:
        if (response["data"] and response["data"][len(response["data"]) - 1]["id"] == artist.id):
            response["data"][len(response["data"]) - 1]["num_upcoming_shows"] += 1
        else:
            data_item = {
                "id": artist.id,
                "name": artist.name,
                "num_upcoming_shows": 1,
            }
            response["count"] += 1
            response["data"].append(data_item)

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

    artists = db.session.query(Show).join(Venue, Show.artist_id == Venue.id).join(Artist, Artist.id == Show.artist_id).with_entities(
        Artist.id, Artist.name, Artist.genres, Artist.city, Artist.state, Artist.phone, Artist.website_link, Artist.facebook_link,
        Artist.seeking_venue, Artist.seeking_description, Artist.image_link, Venue.id, Venue.name, Venue.image_link, Show.start_time
    ).filter(Show.artist_id == artist_id).order_by(Artist.id).all()

    if artists:
        # sort shows into past & upcoming
        past_shows= []
        upcoming_shows= []

        for artist in artists:
            temp_show = {
                "venue_id": artist[11],
                "venue_name": artist[12],
                "venue_image_link": artist[13],
                "start_time": artist[14].strftime("%m/%d/%Y %H:%M:%S")
            }
            if artist[14] <= datetime.now():
                past_shows.append(temp_show)
            else:
                upcoming_shows.append(temp_show)
        
        new_data = {
            "id": artists[0][0],
            "name": artists[0][1],
            "genres": (artists[0][2]).split(","),
            "city": artists[0][3],
            "state": artists[0][4],
            "phone": artists[0][5],
            "website": artists[0][6],
            "facebook_link": artists[0][7],
            "seeking_venue": artists[0][8],
            "seeking_description": artists[0][9],
            "image_link": artists[0][10],
            "past_shows": past_shows,
            "upcoming_shows": upcoming_shows,
            "past_shows_count": len(past_shows),
            "upcoming_shows_count": len(upcoming_shows),
        }
    else:
        new_data = {}

    return render_template('pages/show_artist.html', artist=new_data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

    artist_detail = Artist.query.get(artist_id)
    form = ArtistForm()

    artist = {
        "id": artist_detail.id,
        "name": artist_detail.name,
        "genres": artist_detail.genres.split(","),
        "city": artist_detail.city,
        "state": artist_detail.state,
        "phone": artist_detail.phone,
        "website": artist_detail.website_link,
        "facebook_link": artist_detail.facebook_link,
        "seeking_venue": artist_detail.seeking_venue,
        "seeking_description": artist_detail.seeking_description,
        "image_link": artist_detail.image_link
    }

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

    artist_form = ArtistForm(request.form)

    if (artist_form.validate()):
        try:
            artist_info = Artist.query.get(artist_id)
            artist_info.name = artist_form.name.data
            artist_info.city = artist_form.city.data
            artist_info.state = artist_form.state.data
            artist_info.phone = artist_form.phone.data
            artist_info.image_link = artist_form.image_link.data
            artist_info.genres = ",".join(artist_form.genres.data)
            artist_info.facebook_link = artist_form.facebook_link.data
            artist_info.website_link = artist_form.website_link.data
            artist_info.seeking_venue = artist_form.seeking_venue.data
            artist_info.seeking_description = artist_form.seeking_description.data

            db.session.commit()
            flash(artist_form.name.data + ' was successfully updated!')
        except:
            db.session.rollback()
            flash('An error occurred. ' + artist_form.name.data + ' could not be updated. \n' + sys.exc_info())

        finally:
            db.session.close()
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
            flash('Artist ' + request.form['name'] + ' was successfully listed!')
        except:
            db.session.rollback()
            flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.\n' + sys.exc_info())
        finally:
            db.session.close()
            return redirect(url_for('index'))
    else:
        flash('An error occurred. Check form inputs and try again.' + sys.exc_info())


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

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
