from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='User')  # 'User' or 'Admin'


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    project = db.relationship('Project', backref=db.backref('tasks', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Assigning tasks to users
    user = db.relationship('User', backref=db.backref('tasks', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        role = request.form.get('role', 'User')

        user = User(username=username, email=email, password=password, role=role)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash(f'Welcome {user.username}, you are logged in as {user.role}', 'success')

            # Redirect based on role
            if user.role == 'Admin':
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('user_dashboard'))  # Redirect standard users to their own dashboard

        else:
            flash('Login failed. Check your email and password', 'danger')

    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'Admin':
        tasks = Task.query
    else:
         tasks = Task.query.filter_by(user_id=current_user.id).all()
    projects = Project.query.all()

    # Get filter values from request
    priority_filter = request.args.get('priority')
    status_filter = request.args.get('status')
    project_filter = request.args.get('project_id')

    # Apply filters if they are selected
    if priority_filter:
        tasks = tasks.filter_by(priority=priority_filter)

    if status_filter:
        tasks = tasks.filter_by(status=status_filter)

    if project_filter:
        tasks = tasks.filter_by(project_id=project_filter)

    tasks = tasks.all()  
    return render_template('dashboard.html', tasks=tasks, projects=projects)

@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    projects = Project.query.all()
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']
        priority = request.form['priority']
        status = request.form['status']
        project_id = request.form['project_id']
        

        task = Task(
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            status=status,
            project_id=project_id,
            user_id=current_user.id  
        )
        db.session.add(task)
        db.session.commit()
        flash('Task added successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_task.html', projects=projects)


@app.route('/delete_task/<int:id>')
@login_required
def delete_task(id):
    task = db.session.get(Task, id)

    if current_user.role != 'Admin' and task.user_id != current_user.id:
        flash('Unauthorized action!', 'danger')
        return redirect(url_for('dashboard'))

    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/edit_task/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_task(id):
    task = Task.query.get(id)
    projects = Project.query.all()

    if not task:
        flash('Task not found!', 'danger')
        return redirect(url_for('dashboard'))

    # Ensure that only the task owner or an admin can edit the task
    if current_user.role != 'Admin' and task.user_id != current_user.id:
        flash('Unauthorized action!', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form['description']
        task.due_date = request.form['due_date']
        task.priority = request.form['priority']
        task.status = request.form['status']
        task.project_id = request.form['project_id']

        db.session.commit()
        flash('Task updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_task.html', task=task, projects=projects)

@app.route('/user_dashboard')
@login_required
def user_dashboard():
    if current_user.role != 'User':
        return redirect(url_for('dashboard'))  # Only standard users should access this

    # Corrected: Filter tasks based on user_id instead of project_id
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    
    return render_template('user_dashboard.html', tasks=tasks)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
