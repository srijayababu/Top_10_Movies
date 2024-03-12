from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import project_file_secrets_of_api

MOVIE_SEARCH_API_ENDPOINT = project_file_secrets_of_api.MOVIE_SEARCH_API_ENDPOINT
MOVIE_DETAILS_API_ENDPOINT = project_file_secrets_of_api.MOVIE_DETAILS_API_ENDPOINT
TMDB_IMAGE_URL = project_file_secrets_of_api.TMDB_IMAGE_URL

headers = {
    "accept": "application/json",
    "Authorization": project_file_secrets_of_api.AUTHORIZATION
}

app = Flask(__name__)
app.config['SECRET_KEY'] = project_file_secrets_of_api.DATABASE_SECRET
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///project.db"
Bootstrap(app)
db = SQLAlchemy(app)


class EditForm(FlaskForm):
    rating = StringField('Your Rating out of 10 eg:(7.8)', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Done')


class AddForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    year = db.Column(db.String)
    description = db.Column(db.String)
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer, unique=True)
    review = db.Column(db.String)
    img_url = db.Column(db.String)


# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )

with app.app_context():
    db.create_all()
    # db.session.add(new_movie)

# with app.app_context():
#     db.session.commit()


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()

    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i

    db.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route('/edit/<int:id>', methods=["GET", "POST"])
def edit(id):
    movie_to_update = db.session.execute(db.select(Movie).where(Movie.id == id)).scalar()
    edit_form = EditForm()
    if request.method == "POST":
        movie_to_update.rating = float(edit_form.rating.data)
        movie_to_update.review = edit_form.review.data
        db.session.commit()
        return redirect(url_for('home'))

    return render_template("edit.html", movie=movie_to_update, form=edit_form)


@app.route('/delete/<int:id>')
def delete(id):
    movie_to_delete = db.session.execute(db.select(Movie).where(Movie.id == id)).scalar()

    db.session.delete(movie_to_delete)
    db.session.commit()

    return redirect(url_for('home'))


@app.route('/add', methods=["GET", "POST"])
def add():
    add_form = AddForm()
    if request.method == "POST":
        search_title = add_form.title.data
        parameters = {
            "query": search_title
        }
        add_response = requests.get(url=MOVIE_SEARCH_API_ENDPOINT, params=parameters, headers=headers)

        results = add_response.json()["results"]
        return render_template("select.html", all_results=results)

    return render_template("add.html", form=add_form)


@app.route('/select/<int:id>')
def select(id):
    select_response = requests.get(url=f"{MOVIE_DETAILS_API_ENDPOINT}/{id}", headers=headers)
    result = select_response.json()

    new_movie = Movie(
        title=result["title"],
        year=result["release_date"],
        description=result["overview"],
        img_url=f"{TMDB_IMAGE_URL}{result['poster_path']}",
    )

    db.session.add(new_movie)
    db.session.commit()

    req_movie = db.session.execute(db.select(Movie).where(Movie.title == result["title"])).scalar()
    req_id = req_movie.id
    return redirect(url_for('edit', id=req_id))


if __name__ == '__main__':
    app.run(debug=True)

