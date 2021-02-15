import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


db.execute("""
    CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL,
    password VARCHAR NOT NULL
    );
""")



db.execute("""
    CREATE TABLE books (
    isbn  VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    author VARCHAR NOT NULL,
    year INTEGER NOT NULL
    );
""")


db.execute("""
    CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    book  VARCHAR REFERENCES books (isbn),
    reviewer  INTEGER REFERENCES users,
    rate INTEGER NOT NULL,
    review VARCHAR NOT NULL
    );
""")

def main():
    f = csv.reader(open("books.csv"))
    next(f)
    for isbn, title, author, year in f:
     	db.execute("INSERT into books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",{"isbn": isbn, "title": title, "author": author, "year": year})
     	print("adding.....")
    db.commit()

if __name__=="__main__":
    main()
