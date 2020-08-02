import os
from flask import Flask, request, jsonify, json
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import datetime
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
basedir = os.path.abspath(os.path.dirname(__file__))

# database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(basedir, 'IMDb.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# INIT IMDb
IMDb = SQLAlchemy(app)

# init Marshmallow
ma = Marshmallow(app)

# product class/model


class Movie(IMDb.Model):
    movie_id = IMDb.Column(IMDb.Integer, primary_key=True)
    movie_name = IMDb.Column(IMDb.String(255), unique=True)
    movie_trailer = IMDb.Column(IMDb.String(255))
    movie_overview = IMDb.Column(IMDb.String(255))
    movie_poster = IMDb.Column(IMDb.String(255))
    length = IMDb.Column(IMDb.Integer)

    def __init__(self, movie_name, movie_trailer, movie_overview, movie_poster, length):
        self.movie_name = movie_name
        self.movie_trailer = movie_trailer
        self.movie_overview = movie_overview
        self.movie_poster = movie_poster
        self.length = length


class MovieSchema(ma.Schema):
    class Meta:
        fields = ('movie_id', 'movie_name', 'movie_trailer',
                  'movie_overview', 'movie_poster', 'length')


@app.route('/movies/create', methods=['POST'])
def get_movie():
    req_data = request.get_json()
    movie_name = req_data['movie_name']
    movie_trailer = req_data['movie_trailer']
    movie_overview = req_data['movie_overview']
    movie_poster = req_data['movie_poster']
    length = req_data['length']

    movieobj = Movie(movie_name, movie_trailer,
                     movie_overview, movie_poster, length)
    IMDb.session.add(movieobj)
    IMDb.session.commit()

    return jsonify({"movie_id":movieobj.movie_id, "movie_name": movie_name, "movie_trailer":movie_trailer,"movie_overview":movie_overview,
        "movie_poster":movie_poster,"length":length})


class Theatres(IMDb.Model):
    theatre_id = IMDb.Column(IMDb.Integer, primary_key=True)
    theatre_name = IMDb.Column(IMDb.String(255))
    theatre_location = IMDb.Column(IMDb.String(255))
    city = IMDb.Column(IMDb.String(255))
    pincode = IMDb.Column(IMDb.Integer)

    def __init__(self, theatre_name, theatre_location, city, pincode):
        self.theatre_name = theatre_name
        self.theatre_location = theatre_location
        self.city = city
        self.pincode = pincode


class TheatreSchema(ma.Schema):
    class Meta:
        fields = ('theatre_id', 'theatre_name',
                  'theatre_location', 'city', 'pincode')


@app.route('/theatres/create', methods=['POST'])
def add_theatre():
    req_data = request.get_json()
    theatre_name = req_data['theatre_name']
    theatre_location = req_data['theatre_location']
    city = req_data['city']
    pincode = req_data['pincode']

    if city not in ('Bengaluru', 'Mumbai', 'Delhi', 'Lucknow'):
        abort(400)

    theatreobj = Theatres(theatre_name, theatre_location, city, pincode)
    IMDb.session.add(theatreobj)
    IMDb.session.commit()

    return jsonify({"theatre_id": theatreobj.theatre_id, "theatre_name": theatre_name, "theatre_location": theatre_location, "city": city, "pincode": pincode})


class Shows(IMDb.Model):
    theatre_id = IMDb.Column(IMDb.Integer, primary_key=True)
    movie_id = IMDb.Column(IMDb.Integer, primary_key=True)
    date = IMDb.Column(IMDb.String(10), primary_key=True)
    time = IMDb.Column(IMDb.String(8), primary_key=True)

    def __init__(self, theatre_id, movie_id, date, time):
        self.theatre_id = theatre_id
        self.movie_id = movie_id
        self.date = date
        self.time = time


class ShowSchema(ma.Schema):
    class Meta:
        fields = ('theatre_id', 'movie_id', 'date', 'time')


@app.route('/shows/create', methods=['POST'])
def create_show():
    req_data = request.get_json()
    theatre_id = req_data['theatre_id']
    movie_id = req_data['movie_id']
    date = req_data['date']
    time = req_data['time']

    #Check if entered date is correct

    dt = date.split('-')
    datetime.datetime(int(dt[0]),int(dt[1]),int(dt[2]))

    #Details of the theatre

    theatre = Theatres.query.filter_by(theatre_id = theatre_id).first()

    # Get the movie to be added

    movie_det = Movie.query.filter_by(movie_id=movie_id).first()

    # Get the currently running shows on this day

    shows = Shows.query.filter_by(date=date).filter_by(theatre_id=theatre_id).all()
    result = shows_schema.dump(shows)

    # Current show start time

    mov_time = time.split(':')

    if(int(mov_time[0])>23):
        abort(400)
    
    if(int(mov_time[1])>59):
        abort(400)

    if(int(mov_time[2])>59):
        abort(400)
    movie_start = mov_time[0]+mov_time[1]+mov_time[2]
    runtime = movie_det.length*60

    # Calculation of current show end time

    hh = int(mov_time[0])
    mm = int(mov_time[1])
    ss = int(mov_time[2])

    while(runtime > 0):
        ss += 1
        if (ss == 60):
            mm += 1
            ss = 0
            if(mm == 60):
                hh += 1
                ss = 0
                mm = 0
                if(hh == 25):
                    hh = 0
                    mm = 0
                    ss = 0
        runtime -= 1

    movie_end = ""
    if(hh < 10):
        movie_end += '0'+str(hh)
    else:
        movie_end += str(hh)
    if(mm < 10):
        movie_end += '0'+str(mm)
    else:
        movie_end += str(mm)
    if(ss < 10):
        movie_end += '0'+str(ss)
    else:
        movie_end += str(ss)

    # Check for overlap in current showtime to be added and the shows running already

    for x in result:
        running_movie_id = x['movie_id']
        ts = x['time'].split(':')
        start_time = ts[0]+ts[1]+ts[2]
        running_movie_det = Movie.query.filter_by(movie_id=running_movie_id).first()
        runtime = running_movie_det.length*60

        hh = int(ts[0])
        mm = int(ts[1])
        ss = int(ts[2])

        while(runtime > 0):
            ss += 1
            if (ss == 60):
                mm += 1
                ss = 0
                if(mm == 60):
                    hh += 1
                    ss = 0
                    mm = 0
                    if(hh == 24):
                        hh = 0
                        mm = 0
                        ss = 0
            runtime -= 1

        end_time = ""

        if(hh < 10):
            end_time += '0'+str(hh)
        else:
            end_time += str(hh)
        if(mm < 10):
            end_time += '0'+str(mm)
        else:
            end_time += str(mm)

        if(ss < 10):
            end_time += '0'+str(ss)
        else:
            end_time += str(ss)

        if (int(movie_start)==int(start_time)):
                abort(400)

        if (int(movie_start)<int(start_time)):
                if(int(movie_end)>int(start_time)):
                        abort(400)

        if (int(movie_start)>int(start_time)):
                if(int(end_time)>int(movie_start)):
                        abort(400)

    showobj = Shows(theatre_id, movie_id, date, time)
    IMDb.session.add(showobj)
    IMDb.session.commit()

    #return show_schema.jsonify(showobj)

    return jsonify({
        "movie": {
            "movie_id": movie_det.movie_id,
            "movie_name": movie_det.movie_name,
            "movie_trailer": movie_det.movie_trailer,
            "movie_overview":movie_det.movie_overview,
            "movie_poster": movie_det.movie_poster,
            "length": movie_det.length
        },
        "theatre": {
            "theatre_id": theatre.theatre_id,
            "theatre_name": theatre.theatre_name,
            "theatre_location": theatre.theatre_location,
            "city": theatre.city,
            "pincode": theatre.pincode
        },
        "shows": [
            {
                "date": date,
                "time": time
            }]
    })


@app.route('/showsBy')
def shows_By():
        city = request.args['city']
        date = request.args['date']
        movie_id = request.args['movie_id']
        the_ids=set()
        all_theatres=set()

        movie = Movie.query.filter_by(movie_id=movie_id).first()

        shows_det = Shows.query.filter_by(movie_id=movie_id).filter_by(date=date).all()
        result = shows_schema.dump(shows_det)

        for x in result:
                the_ids.add(x['theatre_id'])

        for x in the_ids:
                theatre_det = Theatres.query.filter_by(theatre_id=x).first()
                if (theatre_det.city == city):
                        all_theatres.add(x)

        theatres_info=[]        
        

        for x in all_theatres:
                all_timings=set()
                showtimings=[]
                theatre = Theatres.query.filter_by(theatre_id=x).first()
                timing_det = Shows.query.filter_by(theatre_id=x).filter_by(movie_id=movie_id).filter_by(date=date).all()
                result_timings = shows_schema.dump(timing_det)
                for y in result_timings:
                        element = {"date":date,"time":y['time']}
                        showtimings.append(element)

                ttr = {"theatre_id":x,
                "theatre_name": theatre.theatre_name,
                "theatre_location": theatre.theatre_location,
                "city": theatre.city,
                "pincode": theatre.pincode,
                "shows":showtimings}

                theatres_info.append(ttr)




        return jsonify({"movie":{
                "movie_id": movie.movie_id,
                "movie_name": movie.movie_name,
                "movie_trailer": movie.movie_trailer,
                "movie_poster": movie.movie_poster,
                "length": movie.length
                },
                "theatres":theatres_info
                })
        #return jsonify(theatres_info)




@app.errorhandler(Exception)
def show_error(error):
    return jsonify({"status": "failure", "reason": "Incorrect Input"}), 400


movie_schema = MovieSchema()
movies_schema = MovieSchema(many=True)
theatre_schema = TheatreSchema()
theatres_schema = TheatreSchema(many=True)
show_schema = ShowSchema()
shows_schema = ShowSchema(many=True)

@app.route("/")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)