import flask

app = flask.Flask('needle')

@app.route('/')
def bees():
    return "Hello, world!"
