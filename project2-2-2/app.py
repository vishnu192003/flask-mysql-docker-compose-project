from flask import Flask, render_template, redirect, url_for, request, abort

from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect

from decimal import Decimal, InvalidOperation

import MySQLdb
import os


app = Flask(__name__)


# ----------------------------------
# Application Configuration
# ----------------------------------

app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST", "db")

app.config["MYSQL_USER"] = os.environ["MYSQL_USER"]

app.config["MYSQL_PASSWORD"] = os.environ["MYSQL_PASSWORD"]

app.config["MYSQL_DB"] = os.getenv("MYSQL_DB", "eedb")

app.config["MYSQL_PORT"] = int(os.getenv("MYSQL_PORT", "3306"))


app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Enable when serving through HTTPS
app.config["SESSION_COOKIE_SECURE"] = True


# ----------------------------------
# Initialize MySQL and CSRF
# ----------------------------------

mysql = MySQL(app)

csrf = CSRFProtect(app)


# ----------------------------------
# Home Page
# ----------------------------------


@app.get("/")
def index():
    return render_template("index.html")


# ----------------------------------
# Add Employee Form
# ----------------------------------


@app.get("/add")
def regEmployee():
    return render_template("reg.html")


# ----------------------------------
# Save Employee
# ----------------------------------


@app.post("/reg")
def saveEmployee():
    try:
        eid = int(request.form["eid"])

        ename = request.form["ename"].strip()

        esal = Decimal(request.form["esal"])

        eaddr = request.form["eaddr"].strip()

        if eid <= 0 or not ename or not eaddr or not esal.is_finite() or esal < 0:
            abort(400, description="Invalid employee data")

    except (ValueError, InvalidOperation):
        abort(400, description="Invalid employee data")

    cursor = mysql.connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO employee
            (eid, ename, esal, eaddr)
            VALUES (%s, %s, %s, %s)
            """,
            (eid, ename, esal, eaddr),
        )

        mysql.connection.commit()

    except MySQLdb.Error:
        mysql.connection.rollback()

        app.logger.exception("Employee insertion failed")

        abort(500)

    finally:
        cursor.close()

    return redirect(url_for("viewEmployee"))


# ----------------------------------
# View Employees
# ----------------------------------


@app.get("/view")
def viewEmployee():
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("SELECT eid, ename, esal, eaddr FROM employee")

        employees = cursor.fetchall()

    finally:
        cursor.close()

    return render_template("view.html", employee=employees)


# ----------------------------------
# Delete Employee
# ----------------------------------


@app.post("/delete/<int:eid>")
def deleteEmployee(eid):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("DELETE FROM employee WHERE eid=%s", (eid,))

        mysql.connection.commit()

    except MySQLdb.Error:
        mysql.connection.rollback()

        app.logger.exception("Employee deletion failed")

        abort(500)

    finally:
        cursor.close()

    return redirect(url_for("viewEmployee"))


# ----------------------------------
# Edit Employee
# ----------------------------------


@app.get("/edit/<int:eid>")
def editEmployee(eid):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute(
            """
            SELECT eid, ename, esal, eaddr
            FROM employee
            WHERE eid=%s
            """,
            (eid,),
        )

        employee = cursor.fetchone()

    finally:
        cursor.close()

    if employee is None:
        abort(404)

    return render_template("edit.html", emp=employee)


# ----------------------------------
# Update Employee
# ----------------------------------


@app.post("/update/<int:eid>")
def updateEmployee(eid):
    try:
        ename = request.form["ename"].strip()

        esal = Decimal(request.form["esal"])

        eaddr = request.form["eaddr"].strip()

        if not ename or not eaddr or not esal.is_finite() or esal < 0:
            abort(400, description="Invalid employee data")

    except InvalidOperation:
        abort(400, description="Invalid salary")

    cursor = mysql.connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE employee
            SET ename=%s,
                esal=%s,
                eaddr=%s
            WHERE eid=%s
            """,
            (ename, esal, eaddr, eid),
        )

        mysql.connection.commit()

    except MySQLdb.Error:
        mysql.connection.rollback()

        app.logger.exception("Employee update failed")

        abort(500)

    finally:
        cursor.close()

    return redirect(url_for("viewEmployee"))


# ----------------------------------
# Health Check
# ----------------------------------


@app.get("/health")
def health():
    return {"status": "ok"}, 200
