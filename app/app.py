from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import InputRequired
from wtforms import DateField
import datetime
import time
import psycopg2
import logging
from opentelemetry import trace
from opentelemetry.trace.status import StatusCode
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test123'  # Ensure you have a secret key for CSRF protection

# Resource configuration for tracing
resource = Resource(attributes={
    "service.name": "Wylies-MacBook-Air",
    "os-version": 14.1,
    "cluster": "A",
    "datacentre": "us-east-1a"
})

# Configure the OTLP exporter
otlp_exporter = OTLPSpanExporter(
    endpoint="localhost:4317",  # Endpoint of the Otel Collector
    insecure=True  # Use TLS in production environments
)

# Set up OpenTelemetry Tracer Provider with OTLP exporter
provider = TracerProvider(resource=resource)
otlp_processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(otlp_processor)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer("my.tracer.name")

#Adding logging to debug issue: 
logging.basicConfig(level=logging.DEBUG)

class ExerciseForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    pushups = IntegerField('Pushups', validators=[InputRequired()])
    pull_ups = IntegerField('Pull-ups', validators=[InputRequired()])
    exercise_date = DateField('Exercise Date', validators=[InputRequired()], format='%Y-%m-%d')
    submit = SubmitField('Submit')

@app.route("/", methods=['GET', 'POST'])

@tracer.start_as_current_span("submit_workout")
def home():
    with tracer.start_as_current_span("home_route") as span:
        form = ExerciseForm()
        span.set_attribute("form_loaded", True)

        if form.validate_on_submit():
            with tracer.start_as_current_span("form_submission") as submission_span:
                submission_span.set_attribute("username", form.username.data)
                submission_span.set_attribute("pushups", form.pushups.data)
                submission_span.set_attribute("pull_ups", form.pull_ups.data)
                user_id, totals = handle_form_submission(form)
                return redirect(url_for('display_results', **totals))

        return render_template('form.html', form=form)

def handle_form_submission(form):
    with tracer.start_as_current_span("database_interaction") as db_span:
        conn = psycopg2.connect(database="exercise", user="wyliebrown", password="test123", host="localhost", port="5432")
        cur = conn.cursor()
        try:
            # Attempt to insert user or get existing user_id
            cur.execute(
                "INSERT INTO Users (username) VALUES (%s) ON CONFLICT (username) DO NOTHING RETURNING user_id;",
                (form.username.data,)
            )
            user_id_row = cur.fetchone()
            if user_id_row:
                user_id = user_id_row[0]
            else:
                # Fetch user_id for existing username
                cur.execute("SELECT user_id FROM Users WHERE username = %s;", (form.username.data,))
                user_id = cur.fetchone()[0]

            # Insert exercise data
            cur.execute(
                "INSERT INTO Exercises (user_id, pushups, pull_ups, exercise_date) VALUES (%s, %s, %s, %s)",
                (user_id, form.pushups.data, form.pull_ups.data, form.exercise_date.data)
            )

            # Calculate totals
            today = datetime.date.today()
            week_start = today - datetime.timedelta(days=today.weekday())
            month_start = today.replace(day=1)
            year_start = today.replace(month=1, day=1)

            # Fetch weekly totals
            cur.execute("""
                SELECT SUM(pushups), SUM(pull_ups)
                FROM Exercises
                WHERE user_id = %s AND exercise_date >= %s
            """, (user_id, week_start))
            weekly_totals = cur.fetchone()

            # Fetch monthly totals
            cur.execute("""
                SELECT SUM(pushups), SUM(pull_ups)
                FROM Exercises
                WHERE user_id = %s AND exercise_date >= %s
            """, (user_id, month_start))
            monthly_totals = cur.fetchone()

            # Fetch yearly totals
            cur.execute("""
                SELECT SUM(pushups), SUM(pull_ups)
                FROM Exercises
                WHERE user_id = %s AND exercise_date >= %s
            """, (user_id, year_start))
            yearly_totals = cur.fetchone()

            # Commit and close the connection
            conn.commit()

            # Return aggregated totals
            return user_id, {
                "weekly_pushups": weekly_totals[0] or 0,
                "weekly_pullups": weekly_totals[1] or 0,
                "monthly_pushups": monthly_totals[0] or 0,
                "monthly_pullups": monthly_totals[1] or 0,
                "yearly_pushups": yearly_totals[0] or 0,
                "yearly_pullups": yearly_totals[1] or 0,
            }
        except Exception as e:
            db_span.record_exception(e)
            db_span.set_status(StatusCode.ERROR, str(e))
            raise
        finally:
            cur.close()
            conn.close()

@app.route("/results")
def display_results():
    with tracer.start_as_current_span("display_results") as results_span:
        data = {key: request.args.get(key, type=int) for key in ['weekly_pushups', 'weekly_pullups', 'monthly_pushups', 'monthly_pullups', 'yearly_pushups', 'yearly_pullups']}
        results_span.add_event("results_displayed", attributes=data)
        return render_template('results.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)