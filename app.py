from flask import Flask, flash, get_flashed_messages, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import sqlite3
from flask_session import Session
from logger_config import setup_logger
import os
import time
import json

from helper import login_required
app = Flask(__name__)
setup_logger(app)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

def get_db_connection():
    conn = sqlite3.connect("finance.db")
    conn.row_factory = sqlite3.Row
    return conn


# secret key use later
app.secret_key = "MY_NAME_IS_KHAN"

@app.route("/")

def index():
    return render_template("index.html")

# @app.route("/login", methods=["GET", "POST"])
# def login():
#     """Log user in"""
    
#     if request.method == "POST":
#         email = request.form.get("email")
#         password = request.form.get("password")

#         session.clear()

#         if not email:
#             flash("Email required")
#             return redirect("/login")

#         if not password:
#             flash("Password required")
#             return redirect("/login")

       
#         conn = get_db_connection()
#         user = conn.execute(
#             "SELECT * FROM users WHERE email = ?", (email,)
#         ).fetchone()
#         conn.close()

    
#         if user is None or user["password"] != password:
#             flash("Invalid credentials")
#             return redirect("/login")
        
#         session["user_id"] = user["id"]
#         session["user_name"] = user["name"]
#         session["role"] = user["role"]

#         # Redirect by role
#         role =user["role"].lower()
#         if role == "employee":
#             return redirect("/employee/dashboard")
#         elif role == "manager":
#             return redirect("/manager/dashboard")
#         else:
#             return redirect("/admin/dashboard")

#     return render_template("login.html")
        
# @app.route("/logout")
# def logout():
#     """Log user out"""

#     # Forget any user_id
#     session.clear()

#     # Redirect user to login form
#     return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        session.clear()

        if not email:
            flash("Email required")
            return redirect("/login")

        if not password:
            flash("Password required")
            return redirect("/login")

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        conn.close()

        # ✅ FIXED password check + logging
        if user is None or user["password"] != password:
            app.logger.warning(
                "Login failed",
                extra={"extra_data": {"email": email}}
            )
            flash("Invalid credentials")
            return redirect("/login")

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["role"] = user["role"]

        app.logger.info(
            "Login success",
            extra={"extra_data": {"user_id": user["id"], "role": user["role"]}}
        )

        role = user["role"].lower()
        if role == "employee":
            return redirect("/employee/dashboard")
        elif role == "manager":
            return redirect("/manager/dashboard")
        else:
            return redirect("/admin/dashboard")

    return render_template("login.html")


# 🚪 LOGOUT
@app.route("/logout")
def logout():
    app.logger.info(
        "User logged out",
        extra={"extra_data": {"user_id": session.get("user_id")}}
    )
    session.clear()
    return redirect("/login")


@app.route("/employee/dashboard")
def dashboard():
    """display employee to create transaction,view"""

    user_id= session.get("user_id")

    conn = get_db_connection()
    total_txn = conn.execute(
        "Select count(*) from transactions where user_id = ?",(user_id,)).fetchone()[0]
    
    pending_count = conn.execute(
        "select count(*) from transactions where user_id = ? AND status = 'pending'",
        (user_id,)).fetchone()[0]
    
    approved_count = conn.execute("Select count(*) from transactions where user_id = ? AND status = 'approved'",
        (user_id,)).fetchone()[0]
    
    transactions = conn.execute("""SELECT t.id, t.amount, t.status, u.email FROM transactions t JOIN users u ON t.user_id = u.id WHERE t.user_id = ? ORDER BY t.created_at DESC  LIMIT 5
    """, (user_id,)).fetchall()
    conn.close()

    return render_template(
    "employee/dashboard.html",
    total_txn=total_txn,
    pending_count=pending_count,
    approved_count=approved_count,
    transactions=transactions
)


UPLOAD_FOLDER = "static/uploads"

# @login_required
# @app.route("/employee/create_transaction", methods=["GET", "POST"])
# @login_required
# def create_transaction():
#     conn = get_db_connection()

#     if request.method == "POST":
#         user_id = session.get("user_id")
#         amount = request.form.get("amount")
#         txn_type = request.form.get("type")
#         category = request.form.get("category")
#         description = request.form.get("description")
#         customer_id = request.form.get("customer_id")

#         #  income and validation by getting the customer id from html

#         if txn_type == "income":
#             status = "approved"

#             if not customer_id:
#                 flash("Customer required for income")
#                 return redirect("/employee/create_transaction")
#         else:
#             status = "pending"
#             customer_id = None

       
#         file = request.files.get("proof")
#         filename = None

#         if file and file.filename != "":
#             filename = f"{user_id}_{int(time.time())}_{secure_filename(file.filename)}"
#             filepath = os.path.join(UPLOAD_FOLDER, filename)
#             file.save(filepath)

        
       
#         conn.execute("""
#             INSERT INTO transactions 
#             (user_id, customer_id, amount, type, category, description, proof, status) 
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#         """, (user_id, customer_id, amount, txn_type, category, description, filename, status))

#         conn.commit()
       
#         flash("Transaction created successfully")
#         return redirect("/employee/dashboard")
#     customers = conn.execute("SELECT * FROM customers").fetchall()
#     conn.close()

#     return render_template("employee/create_transaction.html", customers = customers)

# 💰 CREATE TRANSACTION

@app.route("/employee/create_transaction", methods=["GET", "POST"])
@login_required
def create_transaction():
    conn = get_db_connection()

    if request.method == "POST":
        user_id = session.get("user_id")
        amount = request.form.get("amount")
        txn_type = request.form.get("type")
        category = request.form.get("category")
        description = request.form.get("description")
        customer_id = request.form.get("customer_id")

        if txn_type == "income":
            status = "approved"
            if not customer_id:
                conn.close()
                flash("Customer required")
                return redirect("/employee/create_transaction")
        else:
            status = "pending"
            customer_id = None

        file = request.files.get("proof")
        filename = None

        if file and file.filename:
            filename = f"{user_id}_{int(time.time())}_{secure_filename(file.filename)}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

        conn.execute("""
            INSERT INTO transactions 
            (user_id, customer_id, amount, type, category, description, proof, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, customer_id, amount, txn_type, category, description, filename, status))

        conn.commit()
        conn.close()

        # ✅ logging
        app.logger.info(
            "Transaction created",
            extra={"extra_data": {
                "user_id": user_id,
                "amount": amount,
                "type": txn_type,
                "status": status
            }}
        )

        flash("Transaction created")
        return redirect("/employee/dashboard")

    customers = conn.execute("SELECT * FROM customers").fetchall()
    conn.close()

    return render_template(
    "employee/create_transaction.html",
    customers=customers
)

@app.route("/employee/transactions")
def all_transactions():
    user_id = session.get("user_id")

    search = request.args.get("search", "")
    type_filter = request.args.get("type", "")
    page = request.args.get("page", 1, type=int)

    per_page = 10
    limit = per_page + 1
    offset = (page - 1) * per_page

    conn = get_db_connection()

    query = """
    SELECT transactions.*, users.email 
    FROM transactions 
    JOIN users ON transactions.user_id = users.id  
    WHERE transactions.user_id = ?
    """
    params = [user_id]

    # Search
    if search:
        query += " AND (transactions.category LIKE ? OR transactions.description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    #  Type Filter
    if type_filter:
        query += " AND LOWER(transactions.type) = ?"
        params.append(type_filter.lower())

    #  Pagination
    query += " ORDER BY transactions.created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    # params.extend([per_page, offset])

    transactions = conn.execute(query, params).fetchall()
    has_next = len(transactions) > per_page
    transactions = transactions[:per_page]
    
    # the above line cut the 11 bact to 10 so only 10 recodes wwill diplay and not 11
    conn.close()

    return render_template(
    "employee/transactions.html",
    transactions=transactions,
    page=page,
    has_next=has_next,
    search=search,
    type=type_filter
)

# admin

@app.route("/admin/dashboard")
def viewtransactions():

    search = request.args.get("search", "")
    type_filter = request.args.get("type", "")
    status_filter = request.args.get("status", "")
    page = request.args.get("page", 1, type=int)

    per_page = 10
    limit = per_page + 1
    offset = (page - 1) * per_page

    conn = get_db_connection()

    query = """
    SELECT 
        t.*, 
        u.name as user_name, 
        u.email as user_email,
        m.name AS manager_name 
    FROM transactions t 
    JOIN users u ON t.user_id = u.id  
    LEFT JOIN users m ON t.approved_by = m.id
    WHERE 1=1
    """
    params = []

    
    if search:
        query += """
        AND (u.name LIKE ? OR u.email LIKE ? OR t.category LIKE ? OR t.description LIKE ?) """
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])
    if type_filter:
        query += " AND LOWER(t.type) = ?"
        params.append(type_filter.lower())
    if status_filter:
        query += " AND LOWER(t.status) = ?"
        params.append(status_filter.lower())

    query += " ORDER BY t.created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    transactions = conn.execute(query, params).fetchall()
    has_next = len(transactions) > per_page
    transactions = transactions[:per_page]
    conn.close()

    return render_template(
    "admin/dashboard.html",
    transactions=transactions,
    page=page,
    search=search,
    has_next=has_next,
    type=type_filter,
    status=status_filter
)


@app.route("/admin/manage_users")
def manage_users():
    conn = get_db_connection()

    # Get all users with manager name 
    users = conn.execute(""" 
        SELECT u.*, m.name AS manager_name
        FROM users u
        LEFT JOIN users m ON u.manager_id = m.id
    """).fetchall()

    # Get only managers for dropdown
    managers = conn.execute("""
        SELECT id, name FROM users WHERE role = 'manager'
    """).fetchall()

    conn.close()

    return render_template(
    "admin/manage_users.html",
    users=users,
    managers=managers
)

@app.route("/create-user", methods=["POST"])
def create():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    role = request.form.get("role")
    manager_id = request.form.get("manager_id")

    conn = get_db_connection()

    if role == "employee":
        conn.execute("""
            INSERT INTO users (name, email, password, role, manager_id)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email, password, role, manager_id))

    else:
        conn.execute("""
            INSERT INTO users (name, email, password, role, manager_id)
            VALUES (?, ?, ?, ?, NULL)
        """, (name, email, password, role))

    conn.commit()
    conn.close()

    flash("User created successfully")

    return redirect("/admin/manage_users")

# @app.route("/delete-user", methods=["POST"])
# def delete():
#     user_id = request.form.get("user_id")

#     conn = get_db_connection()

#     #Getting user role
#     user = conn.execute(
#         "SELECT role FROM users WHERE id = ?",
#         (user_id,)
#     ).fetchone()

#     #  user is a manager → check employees
#     if user and user["role"] == "manager":
#         employee_count = conn.execute(
#             "SELECT COUNT(*) as count FROM users WHERE manager_id = ?",
#             (user_id,)
#         ).fetchone()["count"]

#         # If manager has employees → block deletion
#         if employee_count > 0:
#             conn.close()
#             return "Cannot delete manager. Reassign employees first."

#     # normle delete if else to delete (employee/admin OR manager with no employees)
#     conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
#     conn.commit()
#     conn.close()

#     return redirect("/admin/manage_users")

@app.route("/delete-user", methods=["POST"])
def delete():
    user_id = request.form.get("user_id")

    conn = get_db_connection()

    try:
        # Getting user role
        user = conn.execute(
            "SELECT role FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        # ser not found
        if not user:
            app.logger.warning(
                "Delete failed - user not found",
                extra={"extra_data": {"user_id": user_id}}
            )
            flash("User not found")
            return redirect("/admin/manage_users")

        #  user is a manager → check employees
        if user["role"] == "manager":
            employee_count = conn.execute(
                "SELECT COUNT(*) as count FROM users WHERE manager_id = ?",
                (user_id,)
            ).fetchone()["count"]

            #  block deletion
            if employee_count > 0:
                app.logger.warning(
                    "Delete blocked - manager has employees",
                    extra={"extra_data": {
                        "manager_id": user_id,
                        "employee_count": employee_count
                    }}
                )
                flash("Cannot delete manager. Reassign employees first.")
                return redirect("/admin/manage_users")

        # ✅ delete user
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        flash("User deleted successfully")

        app.logger.warning(
            "User deleted",
            extra={"extra_data": {
                "deleted_user_id": user_id,
                "role": user["role"]
            }}
        )

    except Exception as e:
        app.logger.error(
            "User delete failed",
            extra={"extra_data": {
                "user_id": user_id,
                "error": str(e)
            }}
        )

    finally:
        conn.close()

    return redirect("/admin/manage_users")

# 🔁 REASSIGN MANAGER
@app.route("/reassign-delete-manager", methods=["POST"])
def reassign_delete_manager():
    old_manager_id = request.form.get("old_manager_id")
    new_manager_id = request.form.get("new_manager_id")

    conn = get_db_connection()

    conn.execute("""
        UPDATE users SET manager_id = ? WHERE manager_id = ?
    """, (new_manager_id, old_manager_id))

    conn.execute("DELETE FROM users WHERE id = ?", (old_manager_id,))
    conn.commit()
    conn.close()

    app.logger.info(
        "Manager reassigned",
        extra={"extra_data": {
            "old_manager": old_manager_id,
            "new_manager": new_manager_id
        }}
    )

    flash("Manager reassigned and deleted")

    return redirect("/admin/manage_users")


# @app.route("/admin/reassign-delete-manager", methods=["POST"])
# def reassign_delete_manager():
#     old_manager_id = request.form.get("old_manager_id")
#     new_manager_id = request.form.get("new_manager_id")

#     conn = get_db_connection()

#     #  Reassign employees
#     conn.execute("""
#         UPDATE users
#         SET manager_id = ?
#         WHERE manager_id = ?
#     """, (new_manager_id, old_manager_id))

#     # Delete old manager
#     conn.execute("DELETE FROM users WHERE id = ?", (old_manager_id,))

#     conn.commit()
#     conn.close()

#     return redirect("/admin/manage_users")



# @app.route("/delete-user", methods=["POST"])
# def delete():
#     user_id = request.form.get("user_id")

#     conn = get_db_connection()
#     conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
#     conn.commit()
#     conn.close()

#     return redirect("/admin/manage_users")

# @app.route("/admin/manage_users")
# def manage_users():

#     conn = get_db_connection()
#     users = conn.execute("SELECT * FROM users").fetchall()
#     conn.close()
#     return render_template("admin/manage_users.html", users=users)
# firt wala before adding manager feature

  
@app.route("/admin/reports")
def report():
    conn = get_db_connection()

    total_income = conn.execute(""" select COALESCE(SUM(amount), 0) from transactions where type = 'income' """).fetchone()[0]
    total_expense = conn.execute(""" select COALESCE(SUM(amount), 0) from transactions WHERE type = 'expense' """).fetchone()[0]
    employee_expense = conn.execute(""" select u.name AS name, COALESCE(SUM(t.amount), 0) AS expense from transactions t JOIN users u ON t.user_id = u.id WHERE t.type = 'expense' group BY t.user_id ORDER BY expense DESC
    """).fetchall()
    conn.close()

    return render_template(
    "admin/reports.html",
    totalIncome=total_income,
    totalExpense=total_expense,
    netSavings=total_income - total_expense,
    employees=employee_expense
)

# display logs
@app.route("/admin/logs")
def view_logs():
    # 🔐 Restrict access
    if session.get("role") != "admin":
        return redirect("/")

    logs = []
    log_file = "app.json"

    # ✅ Read logs safely
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            for line in f:
                try:
                    logs.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue  # skip bad lines

    # ✅ Latest logs first
    logs.reverse()

    # 🔍 Filters
    level = request.args.get("level", "").upper()
    search = request.args.get("search", "").lower()

    if level:
        logs = [log for log in logs if log.get("level") == level]

    if search:
        logs = [
            log for log in logs
            if search in json.dumps(log).lower()
        ]

    # 📄 Pagination
    page = request.args.get("page", 1, type=int)
    per_page = 20

    total = len(logs)
    start = (page - 1) * per_page
    end = start + per_page

    paginated_logs = logs[start:end]

    return render_template(
    "admin/logs.html",
    logs=paginated_logs,
    page=page,
    total=total,
    per_page=per_page,
    level=level,
    search=search
)

# manger
@app.route("/manager/dashboard")
def manager():
    conn = get_db_connection()
    manager_id = session.get("user_id")  # logged-in manager
    # upaded version
    transactions = conn.execute("""SELECT t.*,u.name as user_name FROM transactions t JOIN users u ON t.user_id = u.id   WHERE t.type = 'expense' AND t.status = 'pending' and u.manager_id = ?
        ORDER BY t.created_at DESC """,(manager_id,)).fetchall()
    conn.close()
    return render_template(
    "manager/dashboard.html",
    transactions=transactions
)

# @app.route("/manager/action", methods=["POST"])
# @login_required
# def manager_action():

#     transaction_id = request.form.get("transaction_id")
#     action = request.form.get("action")
#     manager_id = session.get("user_id")

#     if action == "approve":
#         status = "approved"
#     else:
#         status = "rejected"

#     conn = get_db_connection()
#     conn.execute(""" UPDATE transactions SET status = ?, approved_by = ? 
#         WHERE id = ?
#     """, (status, manager_id, transaction_id))
#     # also calculate whose manger id help in history

#     conn.commit()
#     return redirect("/manager/dashboard")

# 👨‍💼 MANAGER ACTION

@app.route("/manager/action", methods=["POST"])
@login_required
def manager_action():
    transaction_id = request.form.get("transaction_id")
    action = request.form.get("action")
    manager_id = session.get("user_id")

    status = "approved" if action == "approve" else "rejected"

    conn = get_db_connection()
    conn.execute("""
        UPDATE transactions SET status = ?, approved_by = ?
        WHERE id = ?
    """, (status, manager_id, transaction_id))
    conn.commit()
    conn.close()

    app.logger.info(
        "Manager action",
        extra={"extra_data": {
            "manager_id": manager_id,
            "transaction_id": transaction_id,
            "action": status
        }}
    )

    return redirect("/manager/dashboard")


@app.route("/manager/history")
def history():
    
    manager_id =session.get("user_id")
    conn = get_db_connection()
    
    rejected_c = conn.execute(""" select count(*) from transactions WHERE status = 'rejected' and approved_by = ? """, (manager_id,)).fetchone()[0]
    approved_c = conn.execute(""" select count(*) from transactions WHERE status = 'approved' and approved_by = ? """, (manager_id,)).fetchone()[0]
    total_expense = conn.execute(""" select SUM(amount) from transactions WHERE status = 'approved' AND approved_by = ? """, (manager_id,)).fetchone()[0]
    transactions = conn.execute("""
        SELECT t.*,u.name AS employee_name FROM transactions t LEFT JOIN users u ON t.user_id = u.id WHERE t.approved_by = ? AND t.status IN ('approved', 'rejected') ORDER BY t.created_at DESC """, (manager_id,)).fetchall()
    conn.close()

    return render_template(
    "manager/history.html",
    approvedCount=approved_c,
    rejectedCount=rejected_c,
    totalExpense=total_expense,
    transactions=transactions
)



# @app.route("/test-db")
# def test_db():
#     conn = get_db_connection()
    
#     users = conn.execute("SELECT * FROM users").fetchall()

#     conn.commit()
#     conn.close()

#     return render_react_page(
#         "test-db",
#         "Test DB",
#         {"users": serialize_rows(users)},
#     )


# customers
@app.route("/admin/manage-customers")
@login_required
def customer():

   
    conn = get_db_connection()
    customers = conn.execute("SELECT * FROM customers").fetchall()
    conn.close()
    
    return render_template(
    "admin/manage-customers.html",
    customers=customers
)
    
@app.route("/create-customer",methods=["POST"])

def create_customer():
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    
    conn = get_db_connection()
    conn.execute("""
            INSERT INTO customers (name, email, phone)
            VALUES (?, ?, ?)""", (name, email, phone))
    conn.commit()
    conn.close()
    flash("Customer added successfully")
    return redirect("/admin/manage-customers")
     

@app.route("/delete-customer", methods=["POST"])

def delete_customer():
    customer_id = request.form.get("customer_id")

    conn = get_db_connection()
    conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()
    flash("Customer deleted successfully")

    return redirect("/admin/manage-customers")


@app.route("/admin/customer")
@login_required
def income_transactions():

    conn = get_db_connection()

    transactions = conn.execute("""
        SELECT t.*,c.name AS customer_name,u.name AS employee_name FROM transactions t LEFT JOIN customers c ON t.customer_id = c.id LEFT JOIN users u ON t.user_id = u.id 
        WHERE t.type = 'income' ORDER BY t.created_at DESC """).fetchall()
    conn.close()

    return render_template(
    "admin/customer.html",
    transactions=transactions
)

# create transaction, login, logout, delet user, manager action, reassign manager,

