#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from termios import VEOF
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from pytz import utc
from sqlalchemy import outerjoin
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import enum
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# connect to a local postgresql database

migrate = Migrate(app, db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(120)))
    phone = db.Column(db.String(120), unique=True)
    image_link = db.Column(db.String(500))
    website_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent=db.Column(db.Boolean, nullable=False, default=False)
    seeking_description=db.Column(db.Text())

    def __repr__(self) -> str:
      return f'<Venue ID: {self.id}, Name: {self.name} >'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120), unique=True)
    genres = db.Column(db.ARRAY(db.String(120)))
    image_link = db.Column(db.String(500))
    website_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue=db.Column(db.Boolean, nullable=False, default=False)
    seeking_description=db.Column(db.Text())
    show = db.relationship('Shows')

    def __repr__(self) -> str:
      return f'<Artist ID: {self.id}, Name: {self.name} >'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Shows(db.Model):
  __tablename__ = 'Shows'

  start_time = db.Column(db.DateTime(timezone=True))
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), primary_key=True)
  venue = db.relationship("Venue")

  def __repr__(self) -> str:
    return f'<Venue ID: {self.venue_id}, Artist ID: {self.artist_id}, StartTime: {self.start_time}>'

db.create_all()
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
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
  isEmpty = False
  error = False
  try:
    venues = db.session.query(Venue.city, Venue.state, \
              db.func.array_agg(db.func.json_build_object('name', Venue.name, 'id', Venue.id)) \
              .label('venues')) \
              .group_by(Venue.state, Venue.city).all()
    
    db.session.commit()
    if (venues == []) | (venues == {}):
      isEmpty = True
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    if ((isEmpty == False) & (error==False)):
      return render_template('pages/venues.html', areas=venues);
    elif error == True:
      return render_template('errors/500.html')
    else:
      return render_template('errors/404.html')

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search = request.form.get('search_term', '')
  res = Venue.query.filter(Artist.name.ilike("%"+search.lower()+"%")).all()
  response = {}
  response['data'] = [{'id': venue.id, 'name': venue.name, 'num_upcoming_shows': 0} for venue in res]
  response['count'] = len(res)

  return render_template('pages/search_venues.html', results=response, search_term=search)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  error = False
  data = {}
  try:
    venue = Venue.query.get(venue_id)
    shows = db.session.query(Shows.start_time, Shows.artist_id, Shows.venue_id, Artist).filter_by(venue_id=venue_id)\
            .outerjoin(Artist, Artist.id == Shows.artist_id)\
            .outerjoin(Venue, Venue.id == Shows.venue_id).all()
    past_shows = list(filter(lambda s: s.start_time < datetime.now().replace(tzinfo=utc), shows))
    upcoming_shows = list(filter(lambda s: s.start_time >= datetime.now().replace(tzinfo=utc), shows))

    data['id'] = venue.id
    data['name'] = venue.name
    data['genres'] = venue.genres
    data['address'] = venue.address
    data['city'] = venue.city
    data['state'] = venue.state
    data['phone'] = venue.phone
    data['website'] = venue.website_link
    data['facebook_link'] = venue.facebook_link
    data['seeking_talent'] = venue.seeking_talent
    data['seeking_description'] = venue.seeking_description
    data['image_link'] = venue.image_link
    data['past_shows'] = [ 
                          {
                            "artist_id": show[3].id, 
                            "artist_name": show[3].name,
                            "artist_image_link": show[3].image_link,
                            "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                          } for show in past_shows]
    data['past_shows_count'] = len(past_shows)
    data['upcoming_shows'] = [ 
                            {
                              "artist_id": show[3].id, 
                              "artist_name": show[3].name,
                              "artist_image_link": show[3].image_link,
                              "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                            } for show in upcoming_shows]

    data['upcoming_shows_count'] = len(upcoming_shows)

    data1={
      "id": 1,
      "name": "The Musical Hop",
      "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
      "address": "1015 Folsom Street",
      "city": "San Francisco",
      "state": "CA",
      "phone": "123-123-1234",
      "website": "https://www.themusicalhop.com",
      "facebook_link": "https://www.facebook.com/TheMusicalHop",
      "seeking_talent": True,
      "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
      "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
      "past_shows": [{
        "artist_id": 4,
        "artist_name": "Guns N Petals",
        "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
        "start_time": "2019-05-21T21:30:00.000Z"
      }],
      "upcoming_shows": [],
      "past_shows_count": 1,
      "upcoming_shows_count": 0,
    }
    data2={
      "id": 2,
      "name": "The Dueling Pianos Bar",
      "genres": ["Classical", "R&B", "Hip-Hop"],
      "address": "335 Delancey Street",
      "city": "New York",
      "state": "NY",
      "phone": "914-003-1132",
      "website": "https://www.theduelingpianos.com",
      "facebook_link": "https://www.facebook.com/theduelingpianos",
      "seeking_talent": False,
      "image_link": "https://images.unsplash.com/photo-1497032205916-ac775f0649ae?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=750&q=80",
      "past_shows": [],
      "upcoming_shows": [],
      "past_shows_count": 0,
      "upcoming_shows_count": 0,
    }
    data3={
      "id": 3,
      "name": "Park Square Live Music & Coffee",
      "genres": ["Rock n Roll", "Jazz", "Classical", "Folk"],
      "address": "34 Whiskey Moore Ave",
      "city": "San Francisco",
      "state": "CA",
      "phone": "415-000-1234",
      "website": "https://www.parksquarelivemusicandcoffee.com",
      "facebook_link": "https://www.facebook.com/ParkSquareLiveMusicAndCoffee",
      "seeking_talent": False,
      "image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
      "past_shows": [{
        "artist_id": 5,
        "artist_name": "Matt Quevedo",
        "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
        "start_time": "2019-06-15T23:00:00.000Z"
      }],
      "upcoming_shows": [{
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-01T20:00:00.000Z"
      }, {
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-08T20:00:00.000Z"
      }, {
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-15T20:00:00.000Z"
      }],
      "past_shows_count": 1,
      "upcoming_shows_count": 1,
    }
    #data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
  except:
    error = True
    db.rollback()
    print(sys.exc_info())
  finally:
    if error == False:
      db.session.close()
      return render_template('pages/show_venue.html', venue=data)
    else:
      return render_template('errors/500.html')

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  data = {}
  error = False
  form = VenueForm()
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']
    website_link = request.form['website_link']
    if VenueForm(seeking_talent=form.seeking_talent.data) == 'y':
      seeking_talent=True 
    else:
      seeking_talent=False
    seeking_description = request.form['seeking_description']

    venue = Venue(name=name, city=city, state=state, address=address, 
            phone=phone, genres=genres, facebook_link=facebook_link, 
            image_link=image_link, website_link=website_link, 
            seeking_talent=seeking_talent, seeking_description=seeking_description)
    db.session.add(venue)
    db.session.commit()
    print(venue)
    # TODO: modify data to be the data object returned from db insertion
    data['name'] = venue.name
    data['city'] = venue.city
    data['state'] = venue.state
    data['address'] = venue.address
    data['phone'] = venue.phone
    data['genre'] = venue.genres
    data['facebok_link'] = venue.facebook_link
    data['image_link'] = venue.image_link
    data['website_link'] = venue.website_link
    data['seeking_talent'] = venue.seeking_talent
    data['seeking_description'] = venue.seeking_description
    # on successful db insert, flash success
    flash('Venue ' + data['name']+ ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    if error == False:
      db.session.close()
      return render_template('pages/home.html')
    else:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
      return render_template('forms/new_venue.html', form=form)

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  isEmpty = False
  try:
    artist = Artist.query.all()
    if (artist == [] ) | (artist == {}):
      isEmpty = True
  except:
    return render_template('errors/500.html')
  finally:
    if isEmpty == False:
      return render_template('pages/artists.html', artists=artist)
    else:
      return render_template('errors/404.html')

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search = request.form.get('search_term', '')
  res = Artist.query.filter(Artist.name.ilike("%"+search.lower()+"%")).all()
  response = {}
  response['data'] = [{'id': artist.id, 'name': artist.name} for artist in res]
  response['count'] = len(res)

  return render_template('pages/search_artists.html', results=response, search_term=search)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  data = {}
  try:
    artist = Artist.query.get(artist_id)
    shows = db.session.query(Shows.start_time, Venue, Shows.artist_id).filter_by(artist_id=artist_id)\
            .outerjoin(Venue, Venue.id == Shows.venue_id).all()

    past_shows = list(filter(lambda s: s.start_time < datetime.now().replace(tzinfo=utc), shows))
    upcoming_shows = list(filter(lambda s: s.start_time >= datetime.now().replace(tzinfo=utc), shows))

    data['id'] = artist.id
    data['name'] = artist.name
    data['genres'] = artist.genres
    data['city'] = artist.city
    data['state'] = artist.state
    data['phone'] = artist.phone
    data['website'] = artist.website_link
    data['facebook_link'] = artist.facebook_link
    data['seeking_venue'] = artist.seeking_venue
    data['seeking_description'] = artist.seeking_description
    data['image_link'] = artist.image_link
    data['past_shows'] = [ 
                            {
                              "venue_id": show[1].id, 
                              "venue_name": show[1].name,
                              "venue_image_link": show[1].image_link,
                              "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                            } for show in past_shows]
    data['past_shows_count'] = len(past_shows)
    data['upcoming_shows'] = [ 
                            {
                              "venue_id": show[1].id, 
                              "venue_name": show[1].name,
                              "venue_image_link": show[1].image_link,
                              "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                            } for show in upcoming_shows]

    data['upcoming_shows_count'] = len(upcoming_shows)

    data1={
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
    data2={
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
    data3={
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
    
    #data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
  except:
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  try:
    artist = Artist.query.get(artist_id)
    #db.session.commit()
    artist1={
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
    form.name.data = artist.name
    form.genres.data = artist.genres
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.website_link.data = artist.website_link
    form.facebook_link.data = artist.facebook_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
    form.image_link.data = artist.image_link
  except:
    print(sys.exc_info())
  finally:
    db.session.close()  
    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm()
  try:
    artist = Artist.query.get(artist_id)
    artist.name = ArtistForm(name=form.name.data)
    artist.city = ArtistForm(city=form.city.data)
    artist.state = ArtistForm(state=form.state.data)
    artist.phone = ArtistForm(phone=form.phone.data)
    artist.genres = ArtistForm(genres=form.genres.data)
    artist.facebook_link = ArtistForm(facebook_link=form.facebook_link.data)
    artist.website_link = ArtistForm(website_link=form.website_link.data)
    artist.image_link = ArtistForm(image_link=form.image_link.data)
    artist.seeking_venue = ArtistForm(state=form.seeking_venue.data) != None
    artist.seeking_description = ArtistForm(state=form.seeking_description.data)

    db.session.add(artist)
    db.session.commit()
    print(artist.genres)
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    if error == False:
      db.session.close()
      return redirect(url_for('show_artist', artist_id=artist_id))
    else:
      return render_template('errors/500.html')

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  error = False
  form = VenueForm()
  try:
    venue = Venue.query.get(venue_id)
    db.session.commit()
    venues={
      "id": 1,
      "name": "The Musical Hop",
      "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
      "address": "1015 Folsom Street",
      "city": "San Francisco",
      "state": "CA",
      "phone": "123-123-1234",
      "website": "https://www.themusicalhop.com",
      "facebook_link": "https://www.facebook.com/TheMusicalHop",
      "seeking_talent": True,
      "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
      "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
    }
    # populate form with values from venue with ID <venue_id>
    form.name.data = venue.name
    form.genres.data = venue.genres
    form.address.data = venue.address
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.website_link.data = venue.website_link
    form.facebook_link.data = venue.facebook_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
    form.image_link.data = venue.image_link
  except:
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
    if error == False:
      return render_template('forms/edit_venue.html', form=form, venue=venue)

    else:
      render_template('errors/500.html')

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False
  form = VenueForm()
  try:
    venue = Venue.query.get(venue_id)
    venue.name = form.name.data
    venue.genres = request.form.getlist('genres')
    print(request.form.getlist('genres'))
    venue.address = form.address.data
    venue.city = form.city.data
    venue.state = form.state.data
    #venue.phone = VenueForm(phone=form.phone.data)
    #venue.website_link = VenueForm(website_link=form.website_link.data)
    #venue.facebook_link = VenueForm(facebook_link=form.facebook_link.data)
    venue.seeking_talent = form.seeking_talent.data
    #venue.seeking_description = VenueForm(seeking_description=form.seeking_description.data)
    #venue.image_link = VenueForm(state=form.image_link.data)

    db.session.add(venue)
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    if error == False:
      return redirect(url_for('show_venue', venue_id=venue_id))
    else:
      return render_template('errors/500.html')

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  error =  False
  data = {}
  form = ArtistForm()
  try:
    # insert form data as a new Venue record in the db, instead
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres= request.form.getlist('genres')
    facebook_link=request.form['facebook_link']
    image_link=request.form['image_link']
    website_link=request.form['website_link']
    seeking_venue= request.form.get('seeking_value') != None
    seeking_description=request.form['seeking_description']
    artist = Artist(name=name,city=city,state=state,phone=phone,genres=genres, facebook_link=facebook_link,\
                      image_link=image_link, website_link=website_link,seeking_venue=seeking_venue, \
                      seeking_description=seeking_description)
    db.session.add(artist)
    db.session.commit()
    # modify data to be the data object returned from db insertion
    data['name'] = artist.name
    # on successful db insert, flash success
    flash('Artist ' + data['name']+ ' was successfully listed!')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
    
  finally:
    db.session.close()
    if error == False:
      return render_template('pages/home.html')
    else:
      # on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
      return render_template('forms/new_artist.html', form=form)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  isEmpty = False
  data = []
  form = ShowForm()
  try:
    shows = db.session.query(Venue.id, Venue.name, Artist.id, Artist.name, Artist.image_link, Shows.start_time)\
      .join(Venue, Venue.id == Shows.venue_id)\
      .join(Artist, Artist.id == Shows.artist_id).all()
    if shows != []:
      data = [{
                "venue_id": s[0],
                "venue_name": s[1],
                "artist_id": s[2],
                "artist_name": s[3],
                "artist_image_link": s[4],
                "start_time": s[5].strftime('%Y-%m-%d %H:%M:%S')
              } for s in shows]
      
      data1=[{
        "venue_id": 1,
        "venue_name": "The Musical Hop",
        "artist_id": 4,
        "artist_name": "Guns N Petals",
        "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
        "start_time": "2019-05-21T21:30:00.000Z"
      }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 5,
        "artist_name": "Matt Quevedo",
        "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
        "start_time": "2019-06-15T23:00:00.000Z"
      }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-01T20:00:00.000Z"
      }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-08T20:00:00.000Z"
      }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-15T20:00:00.000Z"
      }]
    else:
      isEmpty = True

  except:
    print(sys.exc_info())
  finally:
    if isEmpty == False:
      return render_template('pages/shows.html', shows=data)
    elif isEmpty == True:
      return redirect(url_for('forms/new_show.html', form=form))

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # insert form data as a new Show record in the db, instead
  error = False
  form  = ShowForm()
  try:
    artist_id = form.artist_id.data
    venue_id = form.venue_id.data
    start_time = form.start_time.data

    show = Shows(artist_id=artist_id, venue_id=venue_id, start_time=start_time)

    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')

  except:
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    error = True
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
    print(sys.exc_info())
  finally:
    db.session.close()
    if error == False:
      return render_template('pages/home.html')
    else:
      return render_template('forms/new_show.html', form=form)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
