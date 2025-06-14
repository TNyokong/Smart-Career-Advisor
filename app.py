from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/suggest', methods=["POST"])
def suggest():
    name =request.form['name']
    interests = request.form['interests']

    interests_lower = interests.lower()
    if 'network' in interests_lower:
        suggestion = "Network Engineer"
    elif 'code' in interests_lower or 'software' in interests_lower:
        suggestion = "Software Developer"
    elif 'ai' in interests_lower or 'data' in interests_lower:
        suggestion = "Machine Learning Engineer"
    else:
        suggestion = "IT Support Technician"

    return render_template("result.html", name=name, suggestion=suggestion)

if __name__ == '__main__':
    app.run(debug=True)