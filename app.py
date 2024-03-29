import os
import re
import json
from datetime import datetime
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
    session,
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = "your_secret_key"  # Change this to your secret key
# baseaddress
basedir = os.path.abspath(os.path.dirname(__file__))
# database
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{os.path.join(basedir, 'db.sqlite')}"
)
# app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:root@localhost/personalblog"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

if not os.path.exists("uploads"):
    os.makedirs("uploads")
app.config["UPLOAD_FOLDER"] = "uploads"  # Directory to store uploaded images
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # Maximum file size (2MB)
ALLOWED_EXTENSIONS = {"jpeg", "jpg", "gif", "png", "svg"}
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(Authors).get(int(user_id))


@login_manager.unauthorized_handler
def unauthorized_callback():
    session["next_url"] = request.url
    flash("You must be logged in to access this page.", "error")
    return redirect(url_for("signin"))


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


class Authors(UserMixin, db.Model):
    __tablename__ = "authors"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(200), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.Text(), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    articles = db.relationship("Articles", backref="author", lazy=True)

    def __repr__(self):
        return "<Authors %r>" % self.username


class Profile(db.Model):
    __tablename__ = "profiles"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(
        db.Integer, db.ForeignKey("authors.id"), unique=True, nullable=False
    )
    bio = db.Column(db.Text())
    image = db.Column(db.String(255))
    linkedin = db.Column(db.String(255))
    twitter = db.Column(db.String(255))
    facebook = db.Column(db.String(255))
    instagram = db.Column(db.String(255))
    email = db.Column(db.String(255))
    other_link = db.Column(db.String(255))

    author = db.relationship("Authors", backref="profile", uselist=False)

    def __repr__(self):
        return f"<Profile of {self.author.name}>"


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(120), nullable=False)
    articles = db.relationship("Articles", backref="category", lazy=True)

    def __repr__(self):
        return "<Category %r>" % self.name


class Articles(db.Model):
    __tablename__ = "articles"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(120), nullable=False, unique=True)
    content = db.Column(db.Text(), nullable=False)
    is_published = db.Column(db.Boolean, nullable=False, default=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("authors.id"), nullable=False)
    images = db.relationship("ArticleImages", backref="article", lazy=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.generate_slug()

    def generate_slug(self):
        base_slug = self.title.replace(" ", "-").lower()
        slug = base_slug
        counter = 1
        while Articles.query.filter_by(slug=slug).first() is not None:
            slug = f"{base_slug}-{counter}"
            counter += 1
        self.slug = slug

    def __repr__(self):
        return f"<Articles {self.title}>"


class ArticleImages(db.Model):
    __tablename__ = "articleimages"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey("articles.id"), nullable=False)

    def __repr__(self):
        return f"<ArticleImages {self.filename}>"


def read_config():
    try:
        with open("config.json") as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        print("Config file not found.")
        return {}
        # Handle this case, perhaps by creating a default configuration
    except json.decoder.JSONDecodeError:
        print("Error decoding JSON in config file.")
        # Handle this case, perhaps by providing a default configuration or fixing the JSON file
        return {}


@app.route("/", methods=["GET"], endpoint="index")
def index():
    articles_per_page = 10
    page = request.args.get("page", 1, type=int)
    articles = Articles.query.filter_by(is_published=True).paginate(
        page=page, per_page=articles_per_page
    )

    return render_template("index.html", details=read_config(), articles=articles)


@app.route("/article/<article_slug>/", endpoint="article")
def article(article_slug):
    article = Articles.query.filter_by(slug=article_slug).first_or_404()
    return render_template("article.html", details=read_config(), article=article)


@app.route("/categories", endpoint="categories")
def categories():
    categories = Category.query.all()
    return render_template(
        "categories.html", details=read_config(), categories=categories
    )


@app.route("/category/<category_slug>/", endpoint="category")
def category(category_slug):
    articles_per_page = 10
    page = request.args.get("page", 1, type=int)
    category = Category.query.filter_by(slug=category_slug).first_or_404()
    articles = Articles.query.filter_by(category=category, is_published=True).paginate(
        page=page, per_page=articles_per_page
    )
    return render_template(
        "category.html",
        details=read_config(),
        category=category,
        articles=articles,
    )


@app.route("/author/<username>/", endpoint="author")
def author(username):
    author = Authors.query.filter_by(username=username).first_or_404()
    profile = Profile.query.filter_by(author_id=author.id).first()
    articles_per_page = 10
    page = request.args.get("page", 1, type=int)
    articles = Articles.query.filter_by(author=author, is_published=True).paginate(
        page=page, per_page=articles_per_page
    )
    return render_template(
        "author.html", details=read_config(), profile=profile, articles=articles
    )


@app.route("/about/", endpoint="about")
def about():
    return render_template("about.html", details=read_config())


@app.route("/contact", endpoint="contact")
def contact():
    return render_template("contact.html", details=read_config())


@app.route("/<post_slug>/images/<filename>", methods=["GET"], endpoint="uploaded_image")
def uploaded_image(post_slug, filename):
    # Construct the path to the image based on the post slug and filename
    image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    return send_from_directory(
        os.path.dirname(image_path), os.path.basename(image_path)
    )


# AUTHENTICATION
def validate_username(username):
    pattern = r"^[a-zA-Z0-9_.-]{3,}$"
    return bool(re.match(pattern, username))


@app.route("/signup", endpoint="signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        try:
            name = request.form.get("name")
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")
            cnf_password = request.form.get("cnf_password")
            # Check that all fields are filled in
            if (
                not name
                or not username
                or not email
                or not password
                or not cnf_password
            ):
                flash("Please fill in all required fields.", "error")
                return redirect(url_for("signup"))
            # Validate the username
            if not validate_username(username):
                flash(
                    "Invalid username. Username must be at least 3 characters long and can contain letters, numbers, underscore (_), hyphen (-), and dot (.)",
                    "error",
                )
                return redirect(url_for("signup"))
            # Check that passwords match
            if password != cnf_password:
                flash("Passwords do not match.", "error")
                return redirect(url_for("signup"))
            # Check that the email is valid
            if "@" not in email or "." not in email:
                flash("Invalid email address.", "error")
                return redirect(url_for("signup"))
            # Check that the email is not already in use
            if Authors.query.filter_by(email=email).first():
                flash("Email already in use.", "error")
                return redirect(url_for("signup"))
            # Check that the username is not already in use
            if Authors.query.filter_by(username=username).first():
                flash("Username already in use.", "error")
                return redirect(url_for("signup"))
            # Generate Hash for the password
            password = generate_password_hash(password)
            # Create a new user with the provided details
            new_author = Authors(
                name=name, email=email, password=password, username=username
            )
            db.session.add(new_author)
            db.session.commit()
            # Create a profile for the new user
            new_profile = Profile(author_id=new_author.id)
            db.session.add(new_profile)
            db.session.commit()
            flash("Account created successfully.", "success")
            return redirect(url_for("signin"))
        except Exception as e:
            flash("Something went  wrong! Please try again.", "error")
            print(e)
            return redirect(url_for("signup"))

    return render_template("admin/signup.html", details=read_config())


@app.route("/signin", endpoint="signin", methods=["GET", "POST"])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        try:
            email = request.form.get("email")
            password = request.form.get("password")

            if not email or not password:
                flash("Please fill in all required fields.", "error")
                return redirect(url_for("signin"))

            author = Authors.query.filter_by(email=email).first()

            if author and check_password_hash(author.password, password):
                # Login user
                login_user(author, force=True)
                flash("Logged in successfully.", "success")
                next_url = session.pop("next_url", None)
                if next_url:
                    return redirect(next_url)
                else:
                    return redirect(url_for("profile"))

            else:
                flash("Invalid email or password.", "error")
                return redirect(url_for("signin"))
        except Exception as e:
            flash("Something went wrong! Please try again.", "error")
            print(e)
            return redirect(url_for("signin"))
    return render_template("admin/signin.html", details=read_config())


@app.route("/profile/edit/", endpoint="edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    author = current_user
    profile = Profile.query.filter_by(author_id=author.id).first()
    if request.method == "POST":
        try:
            name = request.form.get("name")
            username = request.form.get("username")
            email = request.form.get("email")
            linkedin = request.form.get("linkedin")
            twitter = request.form.get("twitter")
            facebook = request.form.get("facebook")
            instagram = request.form.get("instagram")
            other_link = request.form.get("other_link")
            bio = request.form.get("bio")
            image = request.files.get("image")

            if not name:
                flash("Name is required.", "error")
                return redirect(url_for("edit-profile"))

            if not username:
                flash("Username is required.", "error")
                return redirect(url_for("edit-profile"))

            # Validate the username
            if not validate_username(username):
                flash(
                    "Invalid username. Username must be at least 3 characters long and can contain letters, numbers, underscore (_), hyphen (-), and dot (.)",
                    "error",
                )
                return redirect(url_for("edit-profile"))

            # Validate Email Address
            if email and ("@" not in email or "." not in email):
                flash("Invalid email address.", "error")
                return redirect(url_for("edit-profile"))

            # Validate Linkedin URL
            if linkedin and not re.match(
                r"^(https?:\/\/)?(www\.)?linkedin\.com\/.*$", linkedin
            ):
                flash("Invalid linkedin profile url.", "error")
                return redirect(url_for("edit-profile"))

            # Validate Twitter URL
            if twitter and not re.match(
                r"^(https?:\/\/)?(www\.)?twitter\.com\/.*$", twitter
            ):
                flash("Invalid twitter profile url.", "error")
                return redirect(url_for("edit-profile"))

            # Validate Facebook URL
            if facebook and not re.match(
                r"^(https?:\/\/)?(www\.)?facebook\.com\/.*$", facebook
            ):
                flash("Invalid facebook profile url.", "error")
                return redirect(url_for("edit-profile"))

            # Validate Instagram URL
            if instagram and not re.match(
                r"^(https?:\/\/)?(www\.)?instagram\.com\/.*$", instagram
            ):
                flash("Invalid instagram profile url.", "error")
                return redirect(url_for("edit-profile"))

            # Validate Other URL
            if other_link and not re.match(r"^(https?:\/\/)?(www\.)?.*$", other_link):
                flash("Invalid other profile url.", "error")
                return redirect(url_for("edit-profile"))

            # Validate BIO
            if bio and len(bio) > 500:
                flash("Bio should not exceed 500 characters.", "error")
                return redirect(url_for("edit-profile"))

            # Check that the username is not already in use
            existing_author = Authors.query.filter(
                Authors.username == username, Authors.id != author.id
            ).first()
            if existing_author:
                flash("Username already in use.", "error")
                return redirect(url_for("edit-profile"))

            # Validate Image
            filename = profile.image
            if image:
                if not allowed_file(image.filename):
                    flash("Invalid image file format.", "error")
                    return redirect(url_for("edit-profile"))
                if image.content_length > app.config["MAX_CONTENT_LENGTH"]:
                    flash("Image file size should not exceed 2MB.", "error")
                    return redirect(url_for("edit-profile"))
                filename = secure_filename(
                    f"{username[:20]}_{name[:20]}_{datetime.now().timestamp()}_{image.filename}"
                )
                image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                # Delete old image
                if profile.image:
                    os.remove(os.path.join(app.config["UPLOAD_FOLDER"], profile.image))

            profile.email = email
            profile.linkedin = linkedin
            profile.twitter = twitter
            profile.facebook = facebook
            profile.instagram = instagram
            profile.other_link = other_link
            profile.bio = bio
            profile.image = filename
            db.session.commit()

            author = Authors.query.filter_by(id=author.id).first()
            author.name = name
            author.username = username
            db.session.commit()

            flash("Profile updated successfully.", "success")
            return redirect(url_for("profile"))

        except Exception as e:
            db.session.rollback()
            flash("Something went wrong! Please try again.", "error")
            print(e)
            return redirect(url_for("edit-profile"))
    return render_template(
        "admin/edit-profile.html", details=read_config(), profile=profile
    )


@app.route("/logout", endpoint="logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for("index"))


# ADMINISTRATION
@app.route("/profile/", endpoint="profile", methods=["GET"])
@login_required
def author():
    current_user_id = current_user.id
    profile = Profile.query.filter_by(author_id=current_user_id).first()
    articles_per_page = 10
    page = request.args.get("page", 1, type=int)

    articles = Articles.query.filter_by(author_id=current_user_id).paginate(
        page=page, per_page=articles_per_page
    )
    return render_template(
        "admin/profile.html", details=read_config(), profile=profile, articles=articles
    )


@app.route(
    "/profile/create-article", endpoint="create-article", methods=["GET", "POST"]
)
@login_required
def create_article():
    categories = Category.query.all()
    if request.method == "POST":
        try:
            title = request.form.get("title")
            content = request.form.get("content")
            images = request.files.getlist("images")
            category_slug = request.form.get("category")
            is_published = request.form.get("is_published")

            if not title or not content or not category_slug or not is_published:
                flash("Please fill in all required fields.", "error")
                return redirect(url_for("create-article"))

            if is_published not in ["0", "1", 1, 0]:
                flash("Please select a valid status for publication.", "error")
                return redirect(url_for("create-article"))

            category = Category.query.filter_by(slug=category_slug).first()
            if not category:
                flash("Please fill in all required fields.", "error")
                return redirect(url_for("create-article"))

            # Save the images and get their filenames
            image_filenames = []
            for i, image in enumerate(images, start=1):
                if image.filename == "":
                    flash("One of the selected images has no filename.", "error")
                    return redirect(url_for("create-article"))
                if not allowed_file(image.filename):
                    flash(
                        "One of the selected images has an invalid file format.",
                        "error",
                    )
                    return redirect(url_for("create-article"))
                if image.content_length > app.config["MAX_CONTENT_LENGTH"]:
                    flash(
                        "One of the selected images exceeds the maximum file size of 2MB.",
                        "error",
                    )
                    return redirect(url_for("create-article"))

            for i, image in enumerate(images, start=1):
                filename = secure_filename(
                    f"{title}_{i}_{datetime.now().timestamp()}_{image.filename}"
                )
                image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                image_filenames.append(filename)

            is_published = True if (is_published == "1" or is_published == 1) else False

            # Create a new blog post
            author_id = current_user.id
            new_post = Articles(
                title=title,
                content=content,
                category=category,
                author_id=author_id,
                is_published=is_published,
            )
            db.session.add(new_post)
            db.session.commit()

            # Associate images with the blog post
            for filename in image_filenames:
                new_image = ArticleImages(filename=filename, article_id=new_post.id)
                db.session.add(new_image)

            db.session.commit()

            flash("Article created successfully.", "success")
            return redirect(url_for("profile"))

        except Exception as e:
            flash("An error occurred while creating the article.", "error")
            print(e)
            return redirect(url_for("create-article"))

    return render_template(
        "admin/create-post.html", details=read_config(), categories=categories
    )


@app.route(
    "/profile/edit-article/<article_slug>/",
    endpoint="edit-article",
    methods=["GET", "POST"],
)
@login_required
def edit_article(article_slug):
    author_id = current_user.id
    article = Articles.query.filter_by(
        slug=article_slug, author_id=author_id
    ).first_or_404()
    categories = Category.query.all()
    if request.method == "POST":
        try:
            title = request.form.get("title")
            content = request.form.get("content")
            images = request.files.getlist("images")
            category_slug = request.form.get("category")
            is_published = request.form.get("is_published")

            if not title or not content or not category_slug or not is_published:
                flash("Please fill in all required fields.", "error")
                return redirect(url_for("edit-article", article_slug=article.slug))

            if is_published not in ["0", "1", 1, 0]:
                flash("Please select a valid status for publication.", "error")
                return redirect(url_for("edit-article", article_slug=article.slug))

            category = Category.query.filter_by(slug=category_slug).first()
            if not category:
                flash("Please fill in all required fields.", "error")
                return redirect(url_for("edit-article", article_slug=article.slug))

            image_filenames = []
            if not (len(images) == 0 or images[0].filename == ""):
                # Save the images and get their filenames
                for i, image in enumerate(images, start=1):
                    if image.filename == "":
                        flash("One of the selected images has no filename.", "error")
                        return redirect(
                            url_for("edit-article", article_slug=article.slug)
                        )
                    if not allowed_file(image.filename):
                        flash(
                            "One of the selected images has an invalid file format.",
                            "error",
                        )
                        return redirect(
                            url_for("edit-article", article_slug=article.slug)
                        )
                    if image.content_length > app.config["MAX_CONTENT_LENGTH"]:
                        flash(
                            "One of the selected images exceeds the maximum file size of 2MB.",
                            "error",
                        )
                        return redirect(
                            url_for("edit-article", article_slug=article.slug)
                        )

                for i, image in enumerate(images, start=1):
                    filename = secure_filename(
                        f"{title}_{i}_{datetime.now().timestamp()}_{image.filename}"
                    )
                    image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                    image_filenames.append(filename)

                # delete old images

                for old_image in article.images:
                    os.remove(
                        os.path.join(app.config["UPLOAD_FOLDER"], old_image.filename)
                    )
                db.session.query(ArticleImages).filter(
                    ArticleImages.article_id == article.id
                ).delete()
                db.session.commit()

            is_published = True if (is_published == "1" or is_published == 1) else False

            article.title = title
            article.content = content
            article.category = category
            article.is_published = is_published
            db.session.commit()

            # Associate images with the blog post
            for filename in image_filenames:
                new_image = ArticleImages(filename=filename, article_id=article.id)
                db.session.add(new_image)
            db.session.commit()

            flash("Article edited successfully.", "success")
            return redirect(url_for("profile"))

        except Exception as e:
            db.session.rollback()
            flash("An error occurred while editing the article.", "error")
            print(e)
            return redirect(url_for("edit-article", article_slug=article.slug))
    return render_template(
        "admin/edit-article.html",
        details=read_config(),
        article=article,
        categories=categories,
    )


@app.route(
    "/profile/delete-article/<article_slug>/",
    endpoint="delete-article",
    methods=["GET"],
)
def delete_article(article_slug):
    author_id = current_user.id
    try:
        article = Articles.query.filter_by(
            slug=article_slug, author_id=author_id
        ).first_or_404()
        # Delete the images associated with the article
        for image in article.images:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], image.filename))
        db.session.query(ArticleImages).filter(
            ArticleImages.article_id == article.id
        ).delete()
        db.session.delete(article)
        db.session.commit()
        flash("Article deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()  # Rollback the transaction
        flash(
            "An error occurred while deleting the article. Please try again later.",
            "error",
        )
        print(e)  # Print the error for debugging purposes
    return redirect(url_for("profile"))


@app.route(
    "/profile/publish/<article_slug>/",
    endpoint="publish-article",
    methods=["get", "post"],
)
@login_required
def publish_article(article_slug):
    author_id = current_user.id
    article = Articles.query.filter_by(
        slug=article_slug, author_id=author_id
    ).first_or_404()
    if request.method == "POST":
        try:
            slug = request.form.get("slug")
            if not slug:
                flash("Something went wrong! Please try again.", "error")
                return redirect(url_for("profile"))
            if slug != article_slug:
                flash("Something went wrong! Please try again.", "error")
                return redirect(url_for("profile"))

            # Toggle the publication status of the article
            if article.is_published:
                article.is_published = False
                flash("Article moved to drafts successfully.", "success")
            else:
                article.is_published = True
                flash("Article published successfully.", "success")
            db.session.commit()
            return redirect(url_for("profile"))
        except Exception as e:
            flash("An error occurred while publishing the article.", "error")
            print(e)
            return redirect(url_for("profile"))
    else:
        return redirect(url_for("profile"))


# ERRORS
@app.errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html", details=read_config()), 404


def create_categories():
    # Check if there are already categories in the table
    if Category.query.count() == 0:
        demo_categories = [
            {"title": "Animals", "slug": "animals"},
            {"title": "Art", "slug": "art"},
            {"title": "Books", "slug": "books"},
            {"title": "Business", "slug": "business"},
            {"title": "Education", "slug": "education"},
            {"title": "Environment", "slug": "environment"},
            {"title": "Fashion", "slug": "fashion"},
            {"title": "Finance", "slug": "finance"},
            {"title": "Fitness", "slug": "fitness"},
            {"title": "Food", "slug": "food"},
            {"title": "Gaming", "slug": "gaming"},
            {"title": "Health", "slug": "health"},
            {"title": "History", "slug": "history"},
            {"title": "Lifestyle", "slug": "lifestyle"},
            {"title": "Movies", "slug": "movies"},
            {"title": "Music", "slug": "music"},
            {"title": "Nature", "slug": "nature"},
            {"title": "News", "slug": "news"},
            {"title": "Pets", "slug": "pets"},
            {"title": "Politics", "slug": "politics"},
            {"title": "Science", "slug": "science"},
            {"title": "Sports", "slug": "sports"},
            {"title": "Technology", "slug": "technology"},
            {"title": "Travel", "slug": "travel"},
            {"title": "TV Shows", "slug": "tv-shows"},
            {"title": "Weather", "slug": "weather"},
            {"title": "World", "slug": "world"},
            {"title": "Writing", "slug": "writing"},
            {"title": "Other", "slug": "other"},
        ]
        for category_data in demo_categories:
            category = Category(**category_data)
            db.session.add(category)
        db.session.commit()


with app.app_context():
    db.create_all()
    create_categories()

if __name__ == "__main__":
    app.run(debug=True)
