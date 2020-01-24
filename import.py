import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL")) # database engine object from SQLAlchemy that manages connections to the database
                                                    # DATABASE_URL is an environment variable that indicates where the database lives
db = scoped_session(sessionmaker(bind=engine))    # create a 'scoped session' that ensures different users' interactions with the
                                                    # database are kept separate

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    count=0
    for isbna, titlea, authora, yeara in reader: # loop gives each column a name
        count+=1
        print(count)
        a=db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn":isbna,"title":titlea,"author": authora,"year":yeara}) 
    print("sucess")
    db.commit() # transactions are assumed, so close the transaction finished


if __name__ == "__main__":
    main()