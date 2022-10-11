from .meta import *



@app.route("/")
def index():
    """
    Main Page
    """

    #Get data from the DB using meta function
    
    rows = query_db("SELECT * FROM product")
    app.logger.info(rows)
    
    return flask.render_template("index.html",
                                 bookList = rows)


@app.route("/products", methods=["GET","POST"])
def products():
    """
    Single Page (ish) Application for Products
    """
    theItem = flask.request.args.get("item")
    if theItem:
        
        #We Do A Query for It
        itemQry = query_db(f"SELECT * FROM product WHERE id = ?",[theItem], one=True)
        #And Associated Review
        reviewQry = query_db("SELECT * FROM review WHERE productID = ?", [theItem])


        
        #If there is form interaction and they put somehing in the basket
        if flask.request.method == "POST":

            quantity = flask.request.form.get("quantity")
            try:
                quantity = int(quantity)
            except ValueError:
                flask.flash("Error Buying Item")
                return flask.render_template("product.html",
                                             item = itemQry,
                                             reviews=reviewQry)
            
            logging.warning("Buy Clicked %s items", quantity)
            
            #And we add something to the Session for the user to keep track
            basket = flask.session.get("basket", {})

            basket[theItem] = quantity
            flask.session["basket"] = basket
            flask.flash("Item Added to Cart")

            
        return flask.render_template("product.html",
                                     item = itemQry,
                                     reviews=reviewQry)
    else:
        
        books = query_db("SELECT * FROM product")        
        return flask.render_template("products.html",
                                     books = books)


@app.route("/user/login", methods=["GET", "POST"])
def login():
    """
    Login Page
    """
    
    if flask.request.method == "POST":
        #Get data
        user = flask.request.form.get("email")
        password = flask.request.form.get("password")
        app.logger.info("Attempt to login as %s:%s", user, password)

        theQry = "Select * FROM User WHERE email = '{0}'".format(user)

        userQry =  query_db(theQry, one=True)

        if userQry is None:
            flask.flash("No Such User")
        else:
            app.logger.info("User is Ok")
            if userQry["password"] == password:
                app.logger.info("Login as %s Success", userQry["email"])
                flask.session["user"] = userQry["id"]
                flask.flash("Login Successful")
                return (flask.redirect(flask.url_for("index")))
            else:
                flask.flash("Password is Incorrect")
            
    return flask.render_template("login.html")

@app.route("/user/create", methods=["GET","POST"])
def create():
    """ Create a new account,
    we will redirect to a homepage here
    """

    if flask.request.method == "GET":
        return flask.render_template("create_account.html")
    
    #Get the form data
    email = flask.request.form.get("email")
    password = flask.request.form.get("password")
    
    #Sanity check do we have a name, email and password
    if not email or not password: 
        flask.flash("Not all info supplied")
        return flask.render_template("create_account.html",
                                     email = email)


    #Otherwise we can add the user
    theQry = "Select * FROM User WHERE email = '{0}'".format(email)                                                   
    userQry =  query_db(theQry, one=True)
   
    if userQry:
        flask.flash("A User with that Email Exists")
        return flask.render_template("create_account.html",
                                     name = name,
                                     email = email)

    else:
        #Crate the user
        app.logger.info("Create New User")
        theQry = f"INSERT INTO user (id, email, password) VALUES (NULL, '{email}', '{password}')"

        userQry = write_db(theQry)
        
        flask.flash("Account Created, you can now Login")
        return flask.redirect(flask.url_for("login"))

@app.route("/user/<userId>/settings")
def settings(userId):
    """
    Update a users settning

    IE password etc.

    """

    theQry = "Select * FROM User WHERE id = '{0}'".format(userId)                                                   
    thisUser =  query_db(theQry, one=True)

    
    if not thisUser:
        flask.flash("No Such User")
        return flask.redirect(flask.url_for("index"))

    #Purchaces
    theSQL = f"Select * FROM purchase WHERE userID = {userId}"
    purchaces = query_db(theSQL)
    
    return flask.render_template("usersettings.html",
                                 user = thisUser,
                                 purchaces = purchaces)


    
@app.route("/logout")
def logout():
    """
    Login Page
    """
    flask.session.clear()
    return flask.redirect(flask.url_for("index"))
    


@app.route("/user/<userId>/update", methods=["GET","POST"])
def updateUser(userId):

    #thisUser = User.query.filter_by(id = userId).first()
    theQry = "Select * FROM User WHERE id = '{0}'".format(userId)   
    thisUser = query_db(theQry, one=True)
    if not thisUser:
        flask.flash("No Such User")
        return flask.redirect(flask_url_for("index"))

    #otherwise we want to do the checks
    if flask.request.method == "POST":
        current = flask.request.form.get("current")
        password = flask.request.form.get("password")
        app.logger.info("Attempt password update for %s from %s to %s", userId, current, password)
        app.logger.info("%s == %s", current, thisUser["password"])
        if current:
            if current == thisUser["password"]:
                app.logger.info("Password OK, update")
                #Update the Password
                theSQL = f"UPDATE user SET password = '{password}' WHERE id = {userId}"
                app.logger.info("SQL %s", theSQL)
                write_db(theSQL)
                flask.flash("Password Updated")
                
            else:
                app.logger.info("Mismatch")
                flask.flash("Current Password is incorrect")
            return flask.redirect(flask.url_for("settings",
                                                userId = thisUser['id']))

            
    
        flask.flash("Update Error")

    return flask.redirect(flask.url_for("settings", userId=userId))




@app.route('/uploads/<name>')
def serve_image(name):
    """
    Helper function to serve an uploaded image
    """
    return flask.send_from_directory(app.config["UPLOAD_FOLDER"], name)


@app.route("/initdb")
def database_helper():
    """
    Helper / Debug Function to create the initial database
    """
    init_db()
    return "Done"

