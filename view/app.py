from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import re
import os
import uuid
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-this")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "recipes.db")

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 허용값 설정
ALLOWED_CATEGORIES = ["한식", "중식", "일식", "양식", "디저트", "기타"]
ALLOWED_DIFFICULTIES = ["쉬움", "보통", "어려움"]

REPORT_REASONS = [
    "부적절한 내용",
    "허위 정보",
    "저작권 문제",
    "욕설/비방",
    "광고/스팸",
    "기타"
]

REPORT_STATUS = [
    "접수",
    "처리중",
    "처리완료"
]


# =========================
# DB 연결
# =========================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    return conn, cursor


# =========================
# 한국 시간
# =========================
def get_kst_time():
    return datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")


# =========================
# 입력값 검증 / 인젝션 방어
# =========================
def clean_text(value, max_length=1000, allow_newline=True):
    if value is None:
        return ""

    value = str(value)
    value = value.replace("\x00", "")
    value = value.strip()

    if not allow_newline:
        value = value.replace("\n", " ").replace("\r", " ")

    if len(value) > max_length:
        value = value[:max_length]

    return value


def validate_email(email):
    email = clean_text(email, max_length=100, allow_newline=False)
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    if not re.match(pattern, email):
        return None

    return email


def validate_password(password):
    if password is None:
        return False

    if len(password) < 4 or len(password) > 50:
        return False

    return True


def validate_category(category):
    category = clean_text(category, max_length=20, allow_newline=False)

    if category not in ALLOWED_CATEGORIES:
        return "기타"

    return category


def validate_filter_category(category):
    category = clean_text(category, max_length=20, allow_newline=False)

    if category not in ALLOWED_CATEGORIES:
        return ""

    return category


def validate_difficulty(difficulty):
    difficulty = clean_text(difficulty, max_length=20, allow_newline=False)

    if difficulty not in ALLOWED_DIFFICULTIES:
        return "보통"

    return difficulty


def validate_filter_difficulty(difficulty):
    difficulty = clean_text(difficulty, max_length=20, allow_newline=False)

    if difficulty not in ALLOWED_DIFFICULTIES:
        return ""

    return difficulty


def validate_cooking_time(value):
    try:
        value = int(value)
    except (ValueError, TypeError):
        value = 1

    if value < 1:
        value = 1

    if value > 360:
        value = 360

    return value


def validate_report_reason(reason):
    reason = clean_text(reason, max_length=30, allow_newline=False)

    if reason not in REPORT_REASONS:
        return "기타"

    return reason


def validate_report_status(status):
    status = clean_text(status, max_length=20, allow_newline=False)

    if status not in REPORT_STATUS:
        return "접수"

    return status


def escape_like_keyword(keyword):
    keyword = clean_text(keyword, max_length=100, allow_newline=False)

    keyword = keyword.replace("\\", "\\\\")
    keyword = keyword.replace("%", "\\%")
    keyword = keyword.replace("_", "\\_")

    return keyword


# =========================
# 이미지 업로드 관련 함수
# =========================
def allowed_image_file(filename):
    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()
    return extension in ALLOWED_IMAGE_EXTENSIONS


def save_recipe_image(file):
    if not file:
        return None

    if file.filename == "":
        return None

    if not allowed_image_file(file.filename):
        return None

    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit(".", 1)[1].lower()

    unique_filename = f"{uuid.uuid4().hex}.{extension}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)

    file.save(save_path)

    return unique_filename


def delete_recipe_image_file(filename):
    if not filename:
        return

    image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    if os.path.exists(image_path):
        os.remove(image_path)


# =========================
# DB 초기화
# =========================
def init_db():
    conn, cursor = get_db()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    try:
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username
            ON users(username)
        """)
    except sqlite3.IntegrityError:
        print("이미 중복된 닉네임이 있어서 username UNIQUE 인덱스를 만들 수 없습니다.")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT,
            ingredients TEXT NOT NULL,
            instructions TEXT NOT NULL,
            cooking_time INTEGER,
            difficulty TEXT,
            created_at TEXT,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("PRAGMA table_info(recipes)")
    recipe_columns = [column[1] for column in cursor.fetchall()]

    if "user_id" not in recipe_columns:
        cursor.execute("ALTER TABLE recipes ADD COLUMN user_id INTEGER")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recipe_id) REFERENCES recipes(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipe_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TEXT,
            UNIQUE(recipe_id, user_id),
            FOREIGN KEY (recipe_id) REFERENCES recipes(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipe_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL UNIQUE,
            image_filename TEXT NOT NULL,
            created_at TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipes(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipe_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            reporter_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            detail TEXT NOT NULL,
            status TEXT DEFAULT '접수',
            created_at TEXT,
            handled_at TEXT,
            UNIQUE(recipe_id, reporter_id),
            FOREIGN KEY (recipe_id) REFERENCES recipes(id),
            FOREIGN KEY (reporter_id) REFERENCES users(id)
        )
    """)

    cursor.execute("SELECT * FROM users WHERE email = ?", ("admin@example.com",))
    admin = cursor.fetchone()

    if not admin:
        admin_password = generate_password_hash("admin1234")

        cursor.execute("""
            INSERT INTO users (username, email, password, role)
            VALUES (?, ?, ?, ?)
        """, ("관리자", "admin@example.com", admin_password, "admin"))

    conn.commit()
    conn.close()


# =========================
# 현재 로그인 사용자
# =========================
def get_current_user():
    if "user_id" not in session:
        return None

    conn, cursor = get_db()

    user = cursor.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    return user


# =========================
# 로그인 필수
# =========================
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


# =========================
# 관리자 필수
# =========================
def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            return redirect(url_for("index"))

        return func(*args, **kwargs)
    return wrapper


# =========================
# 재료 비교 함수 개선 버전
# =========================
STOP_WORDS = {
    "약간", "조금", "적당량", "취향껏", "한줌", "한 줌",
    "소량", "대량", "필요시", "선택", "선택사항",
    "넣기", "넣어주세요", "준비", "사용"
}

COMMON_INGREDIENTS = [
    "돼지고기", "소고기", "닭고기", "오리고기",
    "다진마늘", "마늘", "양파", "대파", "쪽파", "파",
    "김치", "두부", "감자", "당근", "애호박", "호박",
    "버섯", "표고버섯", "새송이버섯", "팽이버섯",
    "고추", "청양고추", "홍고추", "계란", "달걀",
    "밥", "면", "라면", "우동면", "소면", "스파게티면",
    "떡", "어묵", "참치", "햄", "스팸", "베이컨",
    "새우", "오징어", "고등어", "연어", "조개", "바지락",
    "멸치", "다시마", "콩나물", "숙주", "시금치",
    "상추", "깻잎", "배추", "양배추", "무", "오이",
    "토마토", "치즈", "우유", "버터", "생크림",
    "밀가루", "부침가루", "튀김가루", "빵가루",
    "고추장", "된장", "간장", "국간장", "소금", "설탕",
    "후추", "고춧가루", "참기름", "들기름", "식용유",
    "올리브유", "식초", "맛술", "미림", "올리고당",
    "꿀", "물엿", "깨", "통깨", "참깨",
    "마요네즈", "케첩", "굴소스", "돈까스소스",
    "토마토소스", "카레가루", "카레", "물", "육수"
]


def normalize_ingredient(text):
    if not text:
        return ""

    text = str(text).lower().strip()
    text = re.sub(r"\([^)]*\)", " ", text)

    text = re.sub(
        r"\d+(\.\d+)?\s*(g|kg|ml|l|개|큰술|작은술|컵|스푼|장|쪽|알|봉|캔|팩|줌|꼬집|그램|리터|모|t|tsp|tbsp)",
        " ",
        text
    )

    text = re.sub(r"[^가-힣a-zA-Z0-9\s]", " ", text)

    for word in STOP_WORDS:
        text = text.replace(word, " ")

    text = re.sub(r"\s+", "", text)

    return text


def split_ingredient_text(text):
    if not text:
        return []

    text = str(text).lower()
    text = re.sub(r"\([^)]*\)", " ", text)

    text = re.sub(
        r"\d+(\.\d+)?\s*(g|kg|ml|l|개|큰술|작은술|컵|스푼|장|쪽|알|봉|캔|팩|줌|꼬집|그램|리터|모|t|tsp|tbsp)",
        " ",
        text
    )

    text = re.sub(r"[,，/\n\r]+", ",", text)

    result = []
    chunks = [chunk.strip() for chunk in text.split(",") if chunk.strip()]

    for chunk in chunks:
        found = []

        for ingredient in sorted(COMMON_INGREDIENTS, key=len, reverse=True):
            normalized_common = normalize_ingredient(ingredient)
            normalized_chunk = normalize_ingredient(chunk)

            if normalized_common and normalized_common in normalized_chunk:
                found.append(ingredient)
                chunk = chunk.replace(ingredient, " ")

        if found:
            result.extend(found)

            leftovers = re.split(r"\s+", chunk.strip())

            for leftover in leftovers:
                normalized_leftover = normalize_ingredient(leftover)

                if len(normalized_leftover) >= 2:
                    result.append(leftover)

        else:
            words = re.split(r"\s+", chunk.strip())

            for word in words:
                normalized_word = normalize_ingredient(word)

                if len(normalized_word) >= 2:
                    result.append(word)

    unique_result = []
    seen = set()

    for item in result:
        normalized_item = normalize_ingredient(item)

        if normalized_item and normalized_item not in seen:
            seen.add(normalized_item)
            unique_result.append(item.strip())

    return unique_result


def parse_ingredients(text):
    return split_ingredient_text(text)


def is_ingredient_match(recipe_ingredient, my_ingredient):
    recipe_ingredient = normalize_ingredient(recipe_ingredient)
    my_ingredient = normalize_ingredient(my_ingredient)

    if not recipe_ingredient or not my_ingredient:
        return False

    if recipe_ingredient == my_ingredient:
        return True

    if recipe_ingredient in my_ingredient:
        return True

    if my_ingredient in recipe_ingredient:
        return True

    return False


def calculate_ingredient_match(recipe_ingredients_text, my_ingredients_text):
    recipe_ingredients = parse_ingredients(recipe_ingredients_text)
    my_ingredients = parse_ingredients(my_ingredients_text)

    total_count = len(recipe_ingredients)
    matched_count = 0

    if total_count == 0:
        return 0, 0, 0

    for recipe_ingredient in recipe_ingredients:
        for my_ingredient in my_ingredients:
            if is_ingredient_match(recipe_ingredient, my_ingredient):
                matched_count += 1
                break

    match_percent = int((matched_count / total_count) * 100)

    return match_percent, matched_count, total_count


# =========================
# 메인 페이지
# =========================
@app.route("/")
def index():
    keyword = clean_text(
        request.args.get("keyword", ""),
        max_length=100,
        allow_newline=False
    )

    category = validate_filter_category(request.args.get("category", ""))
    difficulty = validate_filter_difficulty(request.args.get("difficulty", ""))

    max_time = request.args.get("max_time", "360")
    max_time_int = validate_cooking_time(max_time)
    max_time = str(max_time_int)

    my_ingredients = clean_text(
        request.args.get("my_ingredients", ""),
        max_length=2000,
        allow_newline=True
    )

    available_filter = clean_text(
        request.args.get("available_filter", ""),
        max_length=10,
        allow_newline=False
    )

    query = """
        SELECT
            recipes.*,
            users.username,
            (
                SELECT COUNT(*)
                FROM recipe_recommendations
                WHERE recipe_recommendations.recipe_id = recipes.id
            ) AS recommend_count
        FROM recipes
        LEFT JOIN users ON recipes.user_id = users.id
        WHERE 1=1
    """

    params = []

    if keyword:
        keyword_parts = parse_ingredients(keyword)

        if not keyword_parts:
            keyword_parts = [keyword]

        for part in keyword_parts:
            safe_keyword = escape_like_keyword(part)
            search_keyword = f"%{safe_keyword}%"

            query += """
                AND (
                    recipes.title LIKE ? ESCAPE '\\'
                    OR recipes.ingredients LIKE ? ESCAPE '\\'
                    OR recipes.instructions LIKE ? ESCAPE '\\'
                )
            """

            params.extend([search_keyword, search_keyword, search_keyword])

    if category:
        query += " AND recipes.category = ?"
        params.append(category)

    if difficulty:
        query += " AND recipes.difficulty = ?"
        params.append(difficulty)

    query += " AND recipes.cooking_time <= ?"
    params.append(max_time_int)

    query += " ORDER BY recipes.id DESC"

    conn, cursor = get_db()
    recipes = cursor.execute(query, params).fetchall()
    conn.close()

    filtered_recipes = []
    match_info = {}

    for recipe in recipes:
        match_percent, matched_count, total_count = calculate_ingredient_match(
            recipe[3],
            my_ingredients
        )

        match_info[recipe[0]] = {
            "percent": match_percent,
            "matched_count": matched_count,
            "total_count": total_count
        }

        if available_filter == "on" and my_ingredients:
            if match_percent >= 70:
                filtered_recipes.append(recipe)
        else:
            filtered_recipes.append(recipe)

    current_user = get_current_user()

    return render_template(
        "index.html",
        recipes=filtered_recipes,
        keyword=keyword,
        category=category,
        difficulty=difficulty,
        max_time=max_time,
        my_ingredients=my_ingredients,
        available_filter=available_filter,
        match_info=match_info,
        current_user=current_user
    )


# =========================
# 회원가입
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = clean_text(
            request.form.get("username", ""),
            max_length=30,
            allow_newline=False
        )

        email = validate_email(request.form.get("email", ""))

        password = request.form.get("password", "")
        password_check = request.form.get("password_check", "")

        if not username:
            return render_template("register.html", error="닉네임을 입력해주세요.")

        if not email:
            return render_template("register.html", error="올바른 이메일 형식이 아닙니다.")

        if not validate_password(password):
            return render_template("register.html", error="비밀번호는 4자 이상 50자 이하로 입력해주세요.")

        if password != password_check:
            return render_template("register.html", error="비밀번호가 일치하지 않습니다.")

        conn, cursor = get_db()

        existing_username = cursor.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if existing_username:
            conn.close()
            return render_template("register.html", error="이미 사용 중인 닉네임입니다.")

        existing_user = cursor.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing_user:
            conn.close()
            return render_template("register.html", error="이미 사용 중인 이메일입니다.")

        hashed_password = generate_password_hash(password)

        try:
            cursor.execute("""
                INSERT INTO users (username, email, password, role)
                VALUES (?, ?, ?, ?)
            """, (username, email, hashed_password, "user"))

            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return render_template("register.html", error="이미 사용 중인 닉네임 또는 이메일입니다.")

        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================
# 로그인
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = validate_email(request.form.get("email", ""))
        password = request.form.get("password", "")

        if not email or not password:
            return render_template("login.html", error="이메일 또는 비밀번호가 올바르지 않습니다.")

        conn, cursor = get_db()

        user = cursor.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if not user:
            return render_template("login.html", error="이메일 또는 비밀번호가 올바르지 않습니다.")

        if not check_password_hash(user[3], password):
            return render_template("login.html", error="이메일 또는 비밀번호가 올바르지 않습니다.")

        session.clear()
        session["user_id"] = user[0]
        session["username"] = user[1]
        session["role"] = user[4]

        return redirect(url_for("index"))

    return render_template("login.html")


# =========================
# 로그아웃
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# =========================
# 내 레시피
# =========================
@app.route("/my-recipes")
@login_required
def my_recipes():
    conn, cursor = get_db()

    recipes = cursor.execute("""
        SELECT
            recipes.*,
            users.username,
            (
                SELECT COUNT(*)
                FROM recipe_recommendations
                WHERE recipe_recommendations.recipe_id = recipes.id
            ) AS recommend_count
        FROM recipes
        LEFT JOIN users ON recipes.user_id = users.id
        WHERE recipes.user_id = ?
        ORDER BY recipes.id DESC
    """, (session["user_id"],)).fetchall()

    conn.close()

    current_user = get_current_user()

    return render_template(
        "my_recipes.html",
        recipes=recipes,
        current_user=current_user
    )


# =========================
# 내가 추천한 레시피
# =========================
@app.route("/my-recommendations")
@login_required
def my_recommendations():
    conn, cursor = get_db()

    recipes = cursor.execute("""
        SELECT
            recipes.*,
            users.username,
            (
                SELECT COUNT(*)
                FROM recipe_recommendations AS rr_count
                WHERE rr_count.recipe_id = recipes.id
            ) AS recommend_count,
            recipe_recommendations.created_at AS recommended_at
        FROM recipe_recommendations
        JOIN recipes ON recipe_recommendations.recipe_id = recipes.id
        LEFT JOIN users ON recipes.user_id = users.id
        WHERE recipe_recommendations.user_id = ?
        ORDER BY recipe_recommendations.id DESC
    """, (session["user_id"],)).fetchall()

    conn.close()

    current_user = get_current_user()

    return render_template(
        "my_recommended_recipes.html",
        recipes=recipes,
        current_user=current_user
    )


# =========================
# 레시피 추가
# =========================
@app.route("/add", methods=["GET", "POST"])
@login_required
def add_recipe():
    if request.method == "POST":
        title = clean_text(
            request.form.get("title", ""),
            max_length=100,
            allow_newline=False
        )

        category = validate_category(request.form.get("category", "기타"))

        ingredients = clean_text(
            request.form.get("ingredients", ""),
            max_length=2000,
            allow_newline=True
        )

        instructions = clean_text(
            request.form.get("instructions", ""),
            max_length=5000,
            allow_newline=True
        )

        cooking_time = validate_cooking_time(request.form.get("cooking_time", "1"))
        difficulty = validate_difficulty(request.form.get("difficulty", "보통"))
        user_id = session["user_id"]

        if not title or not ingredients or not instructions:
            return render_template(
                "add.html",
                error="요리명, 재료, 조리 방법은 반드시 입력해야 합니다."
            )

        image_file = request.files.get("recipe_image")
        image_filename = save_recipe_image(image_file)

        now_kst = get_kst_time()

        conn, cursor = get_db()

        cursor.execute("""
            INSERT INTO recipes
                (title, category, ingredients, instructions, cooking_time, difficulty, created_at, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            category,
            ingredients,
            instructions,
            cooking_time,
            difficulty,
            now_kst,
            user_id
        ))

        recipe_id = cursor.lastrowid

        if image_filename:
            cursor.execute("""
                INSERT INTO recipe_images
                    (recipe_id, image_filename, created_at)
                VALUES (?, ?, ?)
            """, (
                recipe_id,
                image_filename,
                now_kst
            ))

        conn.commit()
        conn.close()

        return redirect(url_for("index"))

    return render_template("add.html")


# =========================
# 레시피 상세 보기
# =========================
@app.route("/recipe/<int:id>")
def detail_recipe(id):
    conn, cursor = get_db()

    recipe = cursor.execute("""
        SELECT recipes.*, users.username
        FROM recipes
        LEFT JOIN users ON recipes.user_id = users.id
        WHERE recipes.id = ?
    """, (id,)).fetchone()

    comments = cursor.execute("""
        SELECT comments.*, users.username
        FROM comments
        LEFT JOIN users ON comments.user_id = users.id
        WHERE comments.recipe_id = ?
        ORDER BY comments.id DESC
    """, (id,)).fetchall()

    recipe_image = cursor.execute("""
        SELECT *
        FROM recipe_images
        WHERE recipe_id = ?
    """, (id,)).fetchone()

    recommend_count = cursor.execute("""
        SELECT COUNT(*)
        FROM recipe_recommendations
        WHERE recipe_id = ?
    """, (id,)).fetchone()[0]

    already_recommended = False

    if "user_id" in session:
        existing_recommend = cursor.execute("""
            SELECT *
            FROM recipe_recommendations
            WHERE recipe_id = ? AND user_id = ?
        """, (id, session["user_id"])).fetchone()

        if existing_recommend:
            already_recommended = True

    conn.close()

    current_user = get_current_user()

    return render_template(
        "detail.html",
        recipe=recipe,
        comments=comments,
        recipe_image=recipe_image,
        current_user=current_user,
        recommend_count=recommend_count,
        already_recommended=already_recommended
    )


# =========================
# 신고하기
# =========================
@app.route("/recipe/<int:recipe_id>/report", methods=["GET", "POST"])
@login_required
def report_recipe(recipe_id):
    conn, cursor = get_db()

    recipe = cursor.execute("""
        SELECT recipes.*, users.username
        FROM recipes
        LEFT JOIN users ON recipes.user_id = users.id
        WHERE recipes.id = ?
    """, (recipe_id,)).fetchone()

    if not recipe:
        conn.close()
        return redirect(url_for("index"))

    current_user = get_current_user()

    if current_user and recipe[8] == current_user[0]:
        conn.close()
        return redirect(url_for("detail_recipe", id=recipe_id))

    existing_report = cursor.execute("""
        SELECT *
        FROM recipe_reports
        WHERE recipe_id = ? AND reporter_id = ?
    """, (recipe_id, session["user_id"])).fetchone()

    if request.method == "POST":
        if existing_report:
            conn.close()
            return render_template(
                "report_recipe.html",
                recipe=recipe,
                already_reported=True,
                error="이미 신고한 레시피입니다."
            )

        reason = validate_report_reason(request.form.get("reason", "기타"))

        detail = clean_text(
            request.form.get("detail", ""),
            max_length=1000,
            allow_newline=True
        )

        if not detail:
            conn.close()
            return render_template(
                "report_recipe.html",
                recipe=recipe,
                already_reported=False,
                error="신고 내용을 입력해주세요."
            )

        now_kst = get_kst_time()

        cursor.execute("""
            INSERT INTO recipe_reports
                (recipe_id, reporter_id, reason, detail, status, created_at, handled_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            recipe_id,
            session["user_id"],
            reason,
            detail,
            "접수",
            now_kst,
            None
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("detail_recipe", id=recipe_id))

    conn.close()

    return render_template(
        "report_recipe.html",
        recipe=recipe,
        already_reported=existing_report is not None
    )


# =========================
# 추천 / 추천 취소
# =========================
@app.route("/recipe/<int:recipe_id>/recommend", methods=["POST"])
@login_required
def recommend_recipe(recipe_id):
    conn, cursor = get_db()

    recipe = cursor.execute(
        "SELECT * FROM recipes WHERE id = ?",
        (recipe_id,)
    ).fetchone()

    if not recipe:
        conn.close()
        return redirect(url_for("index"))

    existing_recommend = cursor.execute("""
        SELECT *
        FROM recipe_recommendations
        WHERE recipe_id = ? AND user_id = ?
    """, (recipe_id, session["user_id"])).fetchone()

    if existing_recommend:
        cursor.execute("""
            DELETE FROM recipe_recommendations
            WHERE recipe_id = ? AND user_id = ?
        """, (recipe_id, session["user_id"]))

    else:
        now_kst = get_kst_time()

        cursor.execute("""
            INSERT INTO recipe_recommendations
                (recipe_id, user_id, created_at)
            VALUES (?, ?, ?)
        """, (recipe_id, session["user_id"], now_kst))

    conn.commit()
    conn.close()

    return redirect(url_for("detail_recipe", id=recipe_id))


# =========================
# 레시피 수정
# =========================
@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_recipe(id):
    conn, cursor = get_db()

    recipe = cursor.execute("""
        SELECT recipes.*, users.username
        FROM recipes
        LEFT JOIN users ON recipes.user_id = users.id
        WHERE recipes.id = ?
    """, (id,)).fetchone()

    if not recipe:
        conn.close()
        return redirect(url_for("index"))

    current_user = get_current_user()

    if current_user[4] != "admin" and recipe[8] != current_user[0]:
        conn.close()
        return redirect(url_for("detail_recipe", id=id))

    recipe_image = cursor.execute("""
        SELECT *
        FROM recipe_images
        WHERE recipe_id = ?
    """, (id,)).fetchone()

    if request.method == "POST":
        title = clean_text(
            request.form.get("title", ""),
            max_length=100,
            allow_newline=False
        )

        category = validate_category(request.form.get("category", "기타"))

        ingredients = clean_text(
            request.form.get("ingredients", ""),
            max_length=2000,
            allow_newline=True
        )

        instructions = clean_text(
            request.form.get("instructions", ""),
            max_length=5000,
            allow_newline=True
        )

        cooking_time = validate_cooking_time(request.form.get("cooking_time", "1"))
        difficulty = validate_difficulty(request.form.get("difficulty", "보통"))

        if not title or not ingredients or not instructions:
            conn.close()
            return render_template(
                "edit.html",
                recipe=recipe,
                recipe_image=recipe_image,
                error="요리명, 재료, 조리 방법은 반드시 입력해야 합니다."
            )

        cursor.execute("""
            UPDATE recipes
            SET title = ?,
                category = ?,
                ingredients = ?,
                instructions = ?,
                cooking_time = ?,
                difficulty = ?
            WHERE id = ?
        """, (
            title,
            category,
            ingredients,
            instructions,
            cooking_time,
            difficulty,
            id
        ))

        image_file = request.files.get("recipe_image")
        new_image_filename = save_recipe_image(image_file)

        if new_image_filename:
            now_kst = get_kst_time()

            if recipe_image:
                old_image_filename = recipe_image[2]
                delete_recipe_image_file(old_image_filename)

                cursor.execute("""
                    UPDATE recipe_images
                    SET image_filename = ?,
                        created_at = ?
                    WHERE recipe_id = ?
                """, (
                    new_image_filename,
                    now_kst,
                    id
                ))

            else:
                cursor.execute("""
                    INSERT INTO recipe_images
                        (recipe_id, image_filename, created_at)
                    VALUES (?, ?, ?)
                """, (
                    id,
                    new_image_filename,
                    now_kst
                ))

        conn.commit()
        conn.close()

        return redirect(url_for("detail_recipe", id=id))

    conn.close()

    return render_template(
        "edit.html",
        recipe=recipe,
        recipe_image=recipe_image
    )


# =========================
# 레시피 삭제
# =========================
@app.route("/delete/<int:id>")
@login_required
def delete_recipe(id):
    conn, cursor = get_db()

    recipe = cursor.execute(
        "SELECT * FROM recipes WHERE id = ?",
        (id,)
    ).fetchone()

    if not recipe:
        conn.close()
        return redirect(url_for("index"))

    current_user = get_current_user()

    if current_user[4] != "admin" and recipe[8] != current_user[0]:
        conn.close()
        return redirect(url_for("detail_recipe", id=id))

    recipe_image = cursor.execute("""
        SELECT *
        FROM recipe_images
        WHERE recipe_id = ?
    """, (id,)).fetchone()

    if recipe_image:
        delete_recipe_image_file(recipe_image[2])

    cursor.execute("DELETE FROM recipe_images WHERE recipe_id = ?", (id,))
    cursor.execute("DELETE FROM comments WHERE recipe_id = ?", (id,))
    cursor.execute("DELETE FROM recipe_recommendations WHERE recipe_id = ?", (id,))
    cursor.execute("DELETE FROM recipe_reports WHERE recipe_id = ?", (id,))
    cursor.execute("DELETE FROM recipes WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


# =========================
# 댓글 추가
# =========================
@app.route("/comment/add/<int:recipe_id>", methods=["POST"])
@login_required
def add_comment(recipe_id):
    content = clean_text(
        request.form.get("content", ""),
        max_length=1000,
        allow_newline=True
    )

    conn, cursor = get_db()

    recipe = cursor.execute(
        "SELECT * FROM recipes WHERE id = ?",
        (recipe_id,)
    ).fetchone()

    if not recipe:
        conn.close()
        return redirect(url_for("index"))

    if content:
        now_kst = get_kst_time()

        cursor.execute("""
            INSERT INTO comments
                (recipe_id, user_id, content, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            recipe_id,
            session["user_id"],
            content,
            now_kst,
            now_kst
        ))

        conn.commit()

    conn.close()

    return redirect(url_for("detail_recipe", id=recipe_id))


# =========================
# 댓글 수정
# =========================
@app.route("/comment/edit/<int:comment_id>", methods=["GET", "POST"])
@login_required
def edit_comment(comment_id):
    conn, cursor = get_db()

    comment = cursor.execute("""
        SELECT comments.*, users.username
        FROM comments
        LEFT JOIN users ON comments.user_id = users.id
        WHERE comments.id = ?
    """, (comment_id,)).fetchone()

    if not comment:
        conn.close()
        return redirect(url_for("index"))

    current_user = get_current_user()

    if comment[2] != current_user[0]:
        recipe_id = comment[1]
        conn.close()
        return redirect(url_for("detail_recipe", id=recipe_id))

    if request.method == "POST":
        content = clean_text(
            request.form.get("content", ""),
            max_length=1000,
            allow_newline=True
        )

        if content:
            now_kst = get_kst_time()

            cursor.execute("""
                UPDATE comments
                SET content = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                content,
                now_kst,
                comment_id
            ))

            conn.commit()

        recipe_id = comment[1]
        conn.close()

        return redirect(url_for("detail_recipe", id=recipe_id))

    conn.close()

    return render_template("edit_comment.html", comment=comment)


# =========================
# 댓글 삭제
# =========================
@app.route("/comment/delete/<int:comment_id>")
@login_required
def delete_comment(comment_id):
    conn, cursor = get_db()

    comment = cursor.execute(
        "SELECT * FROM comments WHERE id = ?",
        (comment_id,)
    ).fetchone()

    if not comment:
        conn.close()
        return redirect(url_for("index"))

    current_user = get_current_user()

    recipe_id = comment[1]

    if current_user[4] != "admin" and comment[2] != current_user[0]:
        conn.close()
        return redirect(url_for("detail_recipe", id=recipe_id))

    cursor.execute("DELETE FROM comments WHERE id = ?", (comment_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("detail_recipe", id=recipe_id))


# =========================
# 관리자 페이지
# =========================
@app.route("/admin")
@admin_required
def admin_page():
    conn, cursor = get_db()

    users = cursor.execute("""
        SELECT id, username, email, role, created_at
        FROM users
        ORDER BY id DESC
    """).fetchall()

    recipes = cursor.execute("""
        SELECT
            recipes.*,
            users.username,
            (
                SELECT COUNT(*)
                FROM recipe_recommendations
                WHERE recipe_recommendations.recipe_id = recipes.id
            ) AS recommend_count
        FROM recipes
        LEFT JOIN users ON recipes.user_id = users.id
        ORDER BY recipes.id DESC
    """).fetchall()

    comments = cursor.execute("""
        SELECT comments.*, users.username, recipes.title
        FROM comments
        LEFT JOIN users ON comments.user_id = users.id
        LEFT JOIN recipes ON comments.recipe_id = recipes.id
        ORDER BY comments.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        users=users,
        recipes=recipes,
        comments=comments
    )


# =========================
# 관리자 신고 목록
# =========================
@app.route("/admin/reports")
@admin_required
def admin_reports():
    conn, cursor = get_db()

    reports = cursor.execute("""
        SELECT
            recipe_reports.*,
            recipes.title,
            reporter.username,
            writer.username
        FROM recipe_reports
        LEFT JOIN recipes ON recipe_reports.recipe_id = recipes.id
        LEFT JOIN users AS reporter ON recipe_reports.reporter_id = reporter.id
        LEFT JOIN users AS writer ON recipes.user_id = writer.id
        ORDER BY recipe_reports.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin_reports.html",
        reports=reports
    )


# =========================
# 관리자 신고 상태 변경
# =========================
@app.route("/admin/reports/<int:report_id>/status", methods=["POST"])
@admin_required
def update_report_status(report_id):
    status = validate_report_status(request.form.get("status", "접수"))
    now_kst = get_kst_time()

    conn, cursor = get_db()

    cursor.execute("""
        UPDATE recipe_reports
        SET status = ?,
            handled_at = ?
        WHERE id = ?
    """, (
        status,
        now_kst,
        report_id
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("admin_reports"))


init_db()

if __name__ == "__main__":
    app.run(debug=True)
