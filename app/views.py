from .meta import *
from datetime import datetime
from .helper import *



@app.route("/")
def index():
    """
    Main Page.
    """
    ip = flask.request.remote_addr
    route = "/"
    logAnalytics(ip, route)
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
    ip = flask.request.remote_addr
    route = "/products"
    logAnalytics(ip, route)

    theItem = flask.request.args.get("item")
    if theItem:
        
        #We Do A Query for It
        itemQry = query_db(f"SELECT * FROM product WHERE id = ?",[theItem], one=True)

        #And Associated Reviews
        #reviewQry = query_db("SELECT * FROM review WHERE productID = ?", [theItem])
        theSQL = f"""
        SELECT * 
        FROM review
        INNER JOIN user ON review.userID = user.id
        WHERE review.productID = {itemQry['id']};
        """
        reviewQry = query_db(theSQL)
        
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
            
            app.logger.warning("Buy Clicked %s items", quantity)
            
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


# ------------------
# USER Level Stuff
# ---------------------
    
@app.route("/user/login", methods=["GET", "POST"])
def login():
    """
    Login Page
    """
    ip = flask.request.remote_addr
    route = "/user/login"
    logAnalytics(ip, route)

    if flask.request.method == "POST":
        #Get data
        user = flask.request.form.get("email")
        password = flask.request.form.get("password")
        app.logger.info("Attempt to login as %s:%s", user, password)
        emailCheck = checkInput(user, True, False)
        passwordCheck = checkInput(password, False, False)
        if (emailCheck != True or passwordCheck != True):
            flask.flash('Input should not contain special characters.')
            return flask.render_template('login.html', email = user)
        else:
            theQry = "Select * FROM User WHERE email = '{0}'".format(user)
            hashedPassword, hashSalt = hashItem(password)
            userQry =  query_db(theQry, one=True)

            if userQry is None:
                flask.flash("No Such User")
            else:
                app.logger.info("User is Ok")
                if userQry["password"] == hashedPassword:
                    if userQry["role"] == 'admin':
                        app.logger.info("Login as %s Success", userQry["email"])
                        flask.session["admin"] = userQry["id"]
                        flask.flash("Login Successful")
                        return (flask.redirect(flask.url_for("index")))
                    else:
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
    route = "/user/create"
    ip =  flask.request.remote_addr
    if flask.request.method == "GET":
        return flask.render_template("create_account.html")
    
    logAnalytics(ip, route)
    #Get the form data
    email = flask.request.form.get("email")
    password = flask.request.form.get("password")
    
    #Sanity check do we have a name, email and password
    if not email or not password: 
        flask.flash("Not all info supplied")
        return flask.render_template("create_account.html",
                                     email = email)

    emailCheck = checkInput(email, True, False)
    passwordCheck = checkInput(password, False, False)
    if (emailCheck != True or passwordCheck != True):
        flask.flash('Input should not contain special characters.')
        return flask.render_template('create_account.html', email = email)
    else:
        hashedPassword, hashSalt = hashItem(password)
        #Otherwise we can add the user
        theQry = "Select * FROM User WHERE email = '{0}'".format(email)                                                   
        userQry =  query_db(theQry, one=True)
    
        if userQry:
            flask.flash("A User with that Email Exists")
            return flask.render_template("create_account.html",
                                        name = name,
                                        email = email)

        else:
            if (email == 'bernard@blackbooks.net'):
                theQry = f"INSERT INTO user (id, email, password, passwordHash, role) VALUES (NULL, '{email}', '{hashedPassword}', '{hashSalt}', 'admin')"
            #Crate the user
            else:
                theQry = f"INSERT INTO user (id, email, password, passwordHash, role) VALUES (NULL, '{email}', '{hashedPassword}', '{hashSalt}', 'user')"
            app.logger.info("Create New User")
            userQry = write_db(theQry)
            
            flask.flash("Account Created, you can now Login")
            return flask.redirect(flask.url_for("login"))

@app.route("/user/settings")
def settings():
    """
    Update a users settings, 
    Allow them to make reviews
    """
    currentUser = getCurrent()
    route = "/user/{0}/settings".format(currentUser)
    currentIp = flask.request.remote_addr
    
    theQry = "Select * FROM User WHERE id = '{0}'".format(currentUser)                                                   
    thisUser =  query_db(theQry, one=True)
    logAnalytics(currentIp, route) 
    
    if not thisUser:
        flask.flash("No Such User")
        return flask.redirect(flask.url_for("index"))
    #Purchases
    
    theSQL = f"Select * FROM purchase WHERE userID = {currentUser}"
    purchaces = query_db(theSQL)

    theSQL = """
    SELECT productId, date, product.name
    FROM purchase
    INNER JOIN product ON purchase.productID = product.id
    WHERE userID = {0};
    """.format(currentUser)

    purchaces = query_db(theSQL)
    
    return flask.render_template("usersettings.html",
                                 user = thisUser,
                                 purchaces = purchaces)

    
@app.route("/logout")
def logout():
    """
    Login Page
    """
    ip = flask.request.remote_addr
    route = '/logout'
    logAnalytics(ip, route)
    flask.session.clear()
    return flask.redirect(flask.url_for("index"))
    


@app.route("/user/update", methods=["GET","POST"])
def updateUser():
    """
    Process any chances from the user settings page
    """
    currentUser = getCurrent()
    ip = flask.request.remote_addr
    route = "/user/{0}/update".format(currentUser)
    logAnalytics(ip, route)
    
    theQry = "Select * FROM User WHERE id = '{0}'".format(currentUser)   
    thisUser = query_db(theQry, one=True)
    if not thisUser:
        flask.flash("No Such User")
        return flask.redirect(flask.url_for("index"))

    #otherwise we want to do the checks
    if flask.request.method == "POST":
        current = flask.request.form.get("current")
        password = flask.request.form.get("password")
        app.logger.info("Attempt password update for %s from %s to %s", currentUser, current, password)
        app.logger.info("%s == %s", current, thisUser["password"])
        if current:
            current, hashSalt = hashItem(current)
            if current == thisUser["password"]:
                app.logger.info("Password OK, update")
                #Update the Password
                password, hashSalt = hashItem(password)
                theSQL = f"UPDATE user SET password = '{password}' WHERE id = {currentUser}"
                app.logger.info("SQL %s", theSQL)
                write_db(theSQL)
                flask.flash("Password Updated")
                
            else:
                app.logger.info("Mismatch")
                flask.flash("Current Password is incorrect")
            return flask.redirect(flask.url_for("settings"))

            
    
        flask.flash("Update Error")

    return flask.redirect(flask.url_for("settings", userId=currentUser))

# -------------------------------------
#
# Functionality to allow user to review items
#
# ------------------------------------------

@app.route("/review/<itemId>", methods=["GET", "POST"])
def reviewItem(itemId):
    """Add a Review"""
    currentUser = getCurrent()
    ip = flask.request.remote_addr
    route = "/review/{0}".format(itemId)
    logAnalytics(ip, route)
    
    #Handle input
    if flask.request.method == "POST":
        reviewStars = flask.request.form.get("rating")
        reviewComment = flask.request.form.get("review")

        #Clean up review whitespace
        reviewComment = reviewComment.strip()
        reviewId = flask.request.form.get("reviewId")
        inputValidation = checkInput(reviewComment, False, True)
        if (inputValidation != True):
            flask.flash("Input should not contain special characters, try entering again")
            return flask.redirect(flask.url_for("reviewItem", itemId={itemId}))
        app.logger.info("Review Made %s", reviewId)
        app.logger.info("Rating %s  Text %s", reviewStars, reviewComment)

        if reviewId:
            #Update an existing oe
            app.logger.info("Update Existing")

            theSQL = f"""
            UPDATE review
            SET stars = {reviewStars},
                review = '{reviewComment}'
            WHERE
                id = {reviewId}"""

            app.logger.debug("%s", theSQL)
            write_db(theSQL)

            flask.flash("Review Updated")
            
        else:
            app.logger.info("New Review")

            theSQL = f"""
            INSERT INTO review (userId, productId, stars, review)
            VALUES ({currentUser}, {itemId}, {reviewStars}, '{reviewComment}');
            """

            app.logger.info("%s", theSQL)
            write_db(theSQL)

            flask.flash("Review Made")

    #Otherwise get the review
    theQry = f"SELECT * FROM product WHERE id = {itemId};"
    item = query_db(theQry, one=True)
    
    theQry = f"SELECT * FROM review WHERE userID = {currentUser} AND productID = {itemId};"
    review = query_db(theQry, one=True)
    app.logger.debug("Review Exists %s", review)

    return flask.render_template("reviewItem.html",
                                 item = item,
                                 review = review,
                                 )

# ---------------------------------------
#
# BASKET AND PAYMEN
#
# ------------------------------------------

@app.route("/user/terms", methods=['GET'])
def terms():
    ip = flask.request.remote_addr
    route = '/user/terms'
    logAnalytics(ip, route)
    return flask.render_template("terms.html")

@app.route("/admin/users", methods=["GET"])
def users():
    ip = flask.request.remote_addr
    route = '/admin/users'
    logAnalytics(ip, route)
    if not flask.session["admin"]:
        flask.flash("You need to be logged in as an admin to access that page.")
        return flask.redirect(flask.url_for("index"))

    sql = "SELECT * FROM user"
    users = query_db(sql)
    return flask.render_template("users.html", users = users)

@app.route("/admin/add", methods=['GET', 'POST'])
def add():
    ip = flask.request.remote_addr
    route = '/admin/add'
    logAnalytics(ip, route)
    if not flask.session["admin"]:
        flask.flash("You need to be logged in as an admin to access that page.")
        return flask.redirect(flask.url_for("index"))
    if flask.request.method == 'POST':
        name = flask.request.form.get('name')
        description = flask.request.form.get('description')
        price = flask.request.form.get('price')
        image = flask.request.form.get('image')
        valid_list = [name, description, price, image]

        for element in valid_list:
            inputValidation = checkInput(element, False, True)
            if (inputValidation != True):
                flask.flash("Input should not contain special characters, try again.")
                return flask.redirect(flask.url_for("add"))
        
        sql = f"INSERT INTO product(id, name, description, price, image) VALUES (NULL, ?, ?, ?, ?);"
        query = write_db(sql, (name, description, price, image))
        flask.flash("Book added.")
    return flask.render_template("add_book.html")

@app.route("/basket", methods=["GET","POST"])
def basket():
    ip = flask.request.remote_addr
    route = '/basket'
    logAnalytics(ip, route)

    #Check for user
    if not flask.session["user"]:
        flask.flash("You need to be logged in")
        return flask.redirect(flask.url_for("index"))


    theBasket = []
    #Otherwise we need to work out the Basket
    #Get it from the session
    sessionBasket = flask.session.get("basket", None)
    if not sessionBasket:
        flask.flash("No items in basket")
        return flask.redirect(flask.url_for("index"))

    totalPrice = 0
    for key in sessionBasket:
        theQry = f"SELECT * FROM product WHERE id = {key}"
        theItem =  query_db(theQry, one=True)
        quantity = int(sessionBasket[key])
        thePrice = theItem["price"] * quantity
        totalPrice += thePrice
        theBasket.append([theItem, quantity, thePrice])
    
        
    return flask.render_template("basket.html",
                                 basket = theBasket,
                                 total=totalPrice)

@app.route("/basket/payment", methods=["GET", "POST"])
def pay():
    """
    Fake paymeent.

    YOU DO NOT NEED TO IMPLEMENT PAYMENT
    """
    ip = flask.request.remote_addr
    route = "/basket/payment"
    logAnalytics(ip, route)
    
    if not flask.session["user"]:
        flask.flash("You need to be logged in")
        return flask.redirect(flask.url_for("index"))

    #Get the total cost
    cost = flask.request.form.get("total")


    
    #Fetch USer ID from Sssion
    theQry = "Select * FROM User WHERE id = {0}".format(flask.session["user"])
    theUser = query_db(theQry, one=True)

    #Add products to the user
    sessionBasket = flask.session.get("basket", None)

    theDate = datetime.utcnow()
    for key in sessionBasket:

        #As we should have a trustworthy key in the basket.
        theQry = "INSERT INTO PURCHASE (userID, productID, date) VALUES ({0},{1},'{2}')".format(theUser['id'],
                                                                                              key,
                                                                                              theDate)
                                                                                              
        app.logger.debug(theQry)
        write_db(theQry)

    #Clear the Session
    flask.session.pop("basket", None)
    
    return flask.render_template("pay.html",
                                 total=cost)



# ---------------------------
# HELPER FUNCTIONS
# ---------------------------


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

    You are free to ignore scurity implications of this
    """
    init_db()
    return "Done"

