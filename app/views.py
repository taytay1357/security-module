from .meta import *



@app.route("/")
def index():
    """
    Main Page
    """

    return flask.render_template("index.html")



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
