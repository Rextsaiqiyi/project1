
import os, requests

from flask import Flask, session, render_template, request, redirect, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


app = Flask(__name__)

if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/", methods=['GET','POST'])
def index():
    if request.method == 'POST':
        username=request.form.get("username")
        password=request.form.get("password")
        users=db.execute("SELECT * FROM users WHERE username=:username and password = :password",
        {"username": username, "password": password}).fetchone()
        if users is None or username is None or password is None:
            return render_template("warning.html", text = "wrong username/password")
        else:
            session["username"]=users.username
            return render_template("booksearch.html",username=username)
    elif session.get("username") is not None:
        return render_template("booksearch.html", username=session.get("username"))
    else:
        return render_template("index.html")

@app.route("/register", methods=['GET','POST'])
def register():
    if request.method=='POST':
        un=request.form.get("username")
        pw=request.form.get("password")
        db.execute("INSERT into users(username, password) VALUES (:username, :password)",
        {"username":un, "password": pw})
        db.commit()
        return render_template("index.html")
    else:
        return render_template("register.html")

@app.route("/booksearch", methods=['GET','POST'])
def booksearch():
    if session.get("username") == None:
        return render_template("index.html")
    booksearch=request.form['booksearch']
    books = db.execute(f"""select * from books where author like '%{booksearch}%' or title like '%{booksearch}%' or isbn like '%{booksearch}';
    """).fetchall()
    if len(books)==0:
        return render_template("warning.html", text = "there is no result.")
    else:
        return render_template("results.html", books=books, booksearch=booksearch)

@app.route("/information/<string:isbn>", methods=['GET','POST'])
def information(isbn):
    userid=db.execute(f"select id from users where username='{session['username']}'").fetchone().id
    if db.execute('SELECT * FROM books WHERE isbn = :isbn',{"isbn": isbn}).rowcount == 0:
        return render_template("warning.html", text = "ERROR 404: no book found")
    book=db.execute('SELECT * FROM books WHERE isbn = :isbn', {"isbn": isbn}).fetchone()
    res = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q":isbn})
    ratingAVG=res.json()['items'][0]['volumeInfo']['averageRating']
    ratingCOUNT=res.json()['items'][0]['volumeInfo']['ratingsCount']
    reviews=db.execute(f""" SELECT * FROM books join reviews on books.isbn = reviews.book where books.isbn='{isbn}';""").fetchall()
    reviewcount=0
    for review in reviews:
        if review.reviewer==userid:
            reviewcount=reviewcount+1
            break
    if request.method=="GET":
        return render_template("information.html", book=book, reviews=reviews, reviewcount=reviewcount,ratingCOUNT=ratingCOUNT,ratingAVG=ratingAVG)
    if request.method=="POST":
        rate=request.form['rating']
        review=request.form['review']
        username=session['username']
        user=db.execute(f"select id from users where username='{username}';").fetchone().id
        db.execute(f"""INSERT INTO reviews (book,reviewer,rate,review) VALUES ('{isbn}',{user},{rate},'{review}')""")
        db.commit()
        reviews=db.execute(f"""select * from books join reviews on books.isbn = reviews.book where books.isbn = '{isbn}';""").fetchall()
        return render_template("information.html", book=book, reviews=reviews,reviewcount=reviewcount+1,ratingAVG=ratingAVG,ratingCOUNT=ratingCOUNT)
@app.route("/api/<string:isbn>")
def api(isbn):
    bookapi=db.execute('SELECT * FROM books WHERE isbn = :isbn',{"isbn": isbn}).fetchone()
    if bookapi is None:
        return jsonify({"error": "book not found"}), 404
    else:
        res = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q":isbn})
        count=res.json()['items'][0]['volumeInfo']['ratingsCount']
        ratings=res.json()['items'][0]['volumeInfo']['averageRating']
        ISBN_10=res.json()['items'][0]['volumeInfo']['industryIdentifiers'][0]['identifier']
        ISBN_13=res.json()['items'][0]['volumeInfo']['industryIdentifiers'][1]['identifier']
        publication=res.json()['items'][0]['volumeInfo']['publishedDate']
        return jsonify({
            "title": bookapi.title,
            "author": bookapi.author,
            "PublishedDate": publication,
            "ISBN_10": ISBN_10,
            "ISBN_13": ISBN_13,
            "reviewcount": count,
            "averageratings": ratings
        })
@app.route("/logout")
def logout():
    session.pop("username", None)
    return render_template("index.html")
