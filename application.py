import os

from flask import Flask, session,render_template,request,redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))



@app.route("/",methods=["GET", "POST"])
def index():
    if request.method=="GET":
        if(session=={}):
            return redirect("/login")

        username=list(db.execute("SELECT username FROM login WHERE user_id=:id",{"id":session["user_id"]}).first())
        s={}
        for i in username:
            print(i)
            s["username"]=i
        return render_template("index.html",user=s)

    #for POST request    

    else:
        if(session=={}):
            return redirect("/login")
        session["prev_search"]=request.form.get("search")
        print(session["prev_search"])
        return redirect("/result")

@app.route("/login",methods=["GET", "POST"])
def login():
    session.clear()

    if request.method=="GET":
        return render_template("login.html")

    else:
        if not request.form.get("username"):
            return render_template("error.html",message="Please enter username", redirect="/login")

        if not request.form.get("password"):
            return render_template("error.html",message="Please enter password", redirect="/login")

        a=db.execute("SELECT * FROM login WHERE username=:username",{"username":request.form.get("username")}).first()
        if(a==None):
            return render_template("error.html",message="You are not yet Registered", redirect="/login")
        if a.password!=request.form.get("password"):
            return render_template("error.html",message="Invalid password/username", redirect="/login")
        session["user_id"]=a.user_id
        session["prev_search"]="~"
        return redirect("/")


@app.route("/register",methods=["GET", "POST"])
def register():
    if request.method=="GET":
        return render_template("register.html")        


    #for POST request
    else:
        if not request.form.get("username"):
            return render_template("error.html",message="Please enter username", redirect="/register")
        if not request.form.get("password"):
            return render_template("error.html",message="Please enter password", redirect="/register")
        if not request.form.get("cpassword"):
            return render_template("error.html",message="Please enter password again", redirect="/register")

        username=request.form.get("username")
        password=request.form.get("password")
        cpassword=request.form.get("cpassword")
        if(password!=cpassword):
            return render_template("error.html",message="Password did not Match", redirect="/register")
        exist=list(db.execute("SELECT * FROM login WHERE username=:username",{"username":username}))
        if(exist!=[]):
            return render_template("error.html",message="Username already Exists", redirect="/register")
        db.execute("INSERT INTO login (username,password) VALUES (:username, :password)",
                        {"username":username,"password":password})
        db.commit()
        a=list(db.execute("SELECT user_id FROM login WHERE username=:username",{"username":username}))
        session["user_id"]=a[0].user_id
        return redirect("/")


@app.route("/book/<int:book_id>",methods=["GET","POST"])
def book(book_id):

    bookinfo=list(db.execute("SELECT * FROM books WHERE book_id=:id",{"id":book_id}))
    s={}
    for i in bookinfo:
            s["book_id"]=i[0]
            s["isbn"]=i[1]
            s["title"]=i[2]
            s["author"]=i[3]
            s["year"]=i[4]
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "OkxC60nEoBYaLTo1hkb0xw", "isbns":s["isbn"]})
    goodreads={}
    if res!=None:
        books=res.json()
        goodreads["average"]=books["books"][0]["average_rating"]
        goodreads["ratings_count"]=books["books"][0]["work_ratings_count"]

    #for GET request
    if(request.method=="GET"):
        if(session=={}):
            return redirect("/login")
        comment=list(db.execute("SELECT login.username ,reviews.comment, reviews.rating  FROM login,reviews  WHERE book_id=:id AND reviews.user_id=login.user_id",{"id":book_id}))
        r=[]
        for i in comment:
            ec={}
            ec["username"]=i[0]
            ec["comment"]=i[1]
            ec["rating"]=i[2]
            r.append(ec)
        return render_template("book.html",book=s,reviews=r,goodreads=goodreads)

    #for POST request
    else:
        if(session=={}):
            return redirect("/login")
        comment=request.form.get("review")
        rating=request.form.get("rating")
        a=list(db.execute("SELECT user_id,book_id FROM reviews WHERE user_id=:user_id AND book_id=:id",{"user_id":session["user_id"], "id":book_id}))
        if(a==[]):
            db.execute("INSERT INTO reviews (user_id,book_id,comment,rating) VALUES(:user_id,:book_id,:comment,:rate)",{"user_id":session["user_id"], "book_id":book_id, "comment":comment,"rate":rating})
            db.commit()
        else:
            db.execute("UPDATE reviews SET comment = :comment, rating =:rate WHERE user_id=:user_id AND book_id=:id",{"comment":comment,"user_id":session["user_id"], "id":book_id, "rate":rating})
            db.commit()
        comment=list(db.execute("SELECT login.username ,reviews.comment, reviews.rating  FROM login,reviews  WHERE reviews.book_id=:id AND reviews.user_id=login.user_id",
                    {"id":book_id}))
        
        r=[]
        for i in comment:
            ec={}
            ec["username"]=i[0]
            ec["comment"]=i[1]
            ec["rating"]=i[2]
            r.append(ec)
        return render_template("book.html",book=s,reviews=r,goodreads=goodreads)



@app.route("/result",methods=["GET", "POST"])
def result():

    if(session=={}):
        return redirect("/login")
   
    if session["prev_search"]=="~":
        return redirect("/")
    query="%"+session["prev_search"]+"%"
    result=[]
    result[-1:-1]=list(db.execute("SELECT * FROM books WHERE isbn LIKE :query",{"query":query}))
    result[0:0]=list(db.execute("SELECT * FROM books WHERE title LIKE :query",{"query":query}))
    result[0:0]=list(db.execute("SELECT * FROM books WHERE author LIKE :query",{"query":query}))
        
    r=[]
    for i in result:
        s={}   
        s["book_id"]=i[0]
        s["isbn"]=i[1]
        s["title"]=i[2]
        r.append(s)
        
    if r==[]:
        return render_template("error.html",message="No Books Found", redirect="/")
    return render_template("result.html",books=r)


@app.route("/review",methods=["GET", "POST"])
def review():
    if(request.method=="GET"):
        reviews=list(db.execute("SELECT books.title,reviews.book_id,reviews.comment,reviews.rating FROM books,reviews  WHERE books.book_id=reviews.book_id AND user_id=:id",
                        {"id":session["user_id"]}))
        r=[]
        for i in reviews:
            print(i)
            s={}
            s["title"]=i[0]
            s["book_id"]=i[1]
            s["comment"]=i[2]
            s["rating"]=i[3]
            r.append(s)

        return render_template("review.html",reviews=r)