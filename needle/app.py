import flask

app = flask.Flask('needle')

@app.route('/')
def bees():
    raise ValueError("wtf be this")
