from app import get_db, init_db

# DB 테이블 생성 보장
init_db()

recipes = [
    # =====================
    # 한식 5개
    # =====================
    {
        "title": "김치찌개",
        "category": "한식",
        "ingredients": "김치, 돼지고기, 두부, 대파, 마늘, 고춧가루, 간장, 물",
        "instructions": "1. 냄비에 돼지고기를 넣고 볶는다.\n2. 김치를 넣고 함께 볶는다.\n3. 물을 붓고 끓인다.\n4. 두부와 대파를 넣고 간을 맞춘다.",
        "cooking_time": 30,
        "difficulty": "쉬움"
    },
    {
        "title": "된장찌개",
        "category": "한식",
        "ingredients": "된장, 두부, 애호박, 감자, 양파, 대파, 청양고추, 물",
        "instructions": "1. 물에 된장을 풀어 끓인다.\n2. 감자, 애호박, 양파를 넣는다.\n3. 두부와 대파를 넣고 한 번 더 끓인다.\n4. 기호에 따라 청양고추를 넣는다.",
        "cooking_time": 25,
        "difficulty": "쉬움"
    },
    {
        "title": "불고기",
        "category": "한식",
        "ingredients": "소고기, 양파, 대파, 간장, 설탕, 다진마늘, 참기름, 후추",
        "instructions": "1. 소고기를 양념에 재운다.\n2. 팬에 양파와 대파를 넣고 볶는다.\n3. 재운 고기를 넣고 익을 때까지 볶는다.\n4. 참기름을 살짝 넣어 마무리한다.",
        "cooking_time": 35,
        "difficulty": "보통"
    },
    {
        "title": "비빔밥",
        "category": "한식",
        "ingredients": "밥, 계란, 당근, 시금치, 콩나물, 고추장, 참기름, 김가루",
        "instructions": "1. 채소를 각각 볶거나 데친다.\n2. 그릇에 밥을 담는다.\n3. 준비한 재료와 계란을 올린다.\n4. 고추장과 참기름을 넣고 비빈다.",
        "cooking_time": 40,
        "difficulty": "보통"
    },
    {
        "title": "계란찜",
        "category": "한식",
        "ingredients": "계란, 물, 소금, 대파, 참기름",
        "instructions": "1. 계란을 풀고 물과 소금을 넣는다.\n2. 체에 한 번 걸러 부드럽게 만든다.\n3. 약한 불에서 천천히 익힌다.\n4. 대파와 참기름을 올려 마무리한다.",
        "cooking_time": 15,
        "difficulty": "쉬움"
    },

    # =====================
    # 중식 5개
    # =====================
    {
        "title": "마파두부",
        "category": "중식",
        "ingredients": "두부, 돼지고기, 대파, 마늘, 고추기름, 된장, 고춧가루, 간장",
        "instructions": "1. 팬에 고추기름과 마늘을 넣고 볶는다.\n2. 돼지고기를 넣고 익힌다.\n3. 두부와 양념을 넣고 끓인다.\n4. 대파를 넣고 마무리한다.",
        "cooking_time": 25,
        "difficulty": "보통"
    },
    {
        "title": "볶음밥",
        "category": "중식",
        "ingredients": "밥, 계란, 대파, 당근, 햄, 식용유, 간장, 소금",
        "instructions": "1. 팬에 식용유를 두르고 대파를 볶는다.\n2. 계란을 넣고 스크램블한다.\n3. 밥과 채소, 햄을 넣고 볶는다.\n4. 간장과 소금으로 간한다.",
        "cooking_time": 20,
        "difficulty": "쉬움"
    },
    {
        "title": "탕수육",
        "category": "중식",
        "ingredients": "돼지고기, 전분가루, 계란, 식용유, 식초, 설탕, 간장, 양파, 당근",
        "instructions": "1. 돼지고기에 밑간을 한다.\n2. 전분 반죽을 묻혀 튀긴다.\n3. 식초, 설탕, 간장으로 소스를 만든다.\n4. 튀긴 고기에 소스를 곁들인다.",
        "cooking_time": 60,
        "difficulty": "어려움"
    },
    {
        "title": "짜장면",
        "category": "중식",
        "ingredients": "면, 춘장, 돼지고기, 양파, 양배추, 감자, 식용유, 물",
        "instructions": "1. 춘장을 기름에 볶는다.\n2. 돼지고기와 채소를 볶는다.\n3. 물을 넣고 끓인 뒤 춘장을 넣는다.\n4. 삶은 면 위에 소스를 올린다.",
        "cooking_time": 45,
        "difficulty": "보통"
    },
    {
        "title": "깐풍기",
        "category": "중식",
        "ingredients": "닭고기, 전분가루, 마늘, 대파, 고추, 간장, 식초, 설탕",
        "instructions": "1. 닭고기에 전분을 묻혀 튀긴다.\n2. 팬에 마늘, 대파, 고추를 볶는다.\n3. 간장, 식초, 설탕으로 소스를 만든다.\n4. 튀긴 닭고기를 소스에 버무린다.",
        "cooking_time": 50,
        "difficulty": "어려움"
    },

    # =====================
    # 일식 5개
    # =====================
    {
        "title": "돈카츠",
        "category": "일식",
        "ingredients": "돼지고기, 밀가루, 계란, 빵가루, 식용유, 돈까스소스, 소금, 후추",
        "instructions": "1. 돼지고기를 두드려 편다.\n2. 소금과 후추로 밑간한다.\n3. 밀가루, 계란, 빵가루 순서로 묻힌다.\n4. 기름에 노릇하게 튀긴다.",
        "cooking_time": 40,
        "difficulty": "보통"
    },
    {
        "title": "오야코동",
        "category": "일식",
        "ingredients": "밥, 닭고기, 계란, 양파, 간장, 설탕, 맛술, 물",
        "instructions": "1. 팬에 간장, 설탕, 맛술, 물을 넣고 끓인다.\n2. 양파와 닭고기를 넣고 익힌다.\n3. 계란을 풀어 넣는다.\n4. 밥 위에 올려 완성한다.",
        "cooking_time": 25,
        "difficulty": "쉬움"
    },
    {
        "title": "일본식 카레",
        "category": "일식",
        "ingredients": "카레가루, 감자, 당근, 양파, 돼지고기, 물, 밥",
        "instructions": "1. 돼지고기와 채소를 볶는다.\n2. 물을 붓고 재료가 익을 때까지 끓인다.\n3. 카레가루를 넣고 잘 풀어준다.\n4. 밥과 함께 담는다.",
        "cooking_time": 40,
        "difficulty": "쉬움"
    },
    {
        "title": "야키소바",
        "category": "일식",
        "ingredients": "면, 양배추, 돼지고기, 양파, 당근, 식용유, 간장, 돈까스소스",
        "instructions": "1. 팬에 돼지고기와 채소를 볶는다.\n2. 면을 넣고 함께 볶는다.\n3. 간장과 소스로 간한다.\n4. 골고루 섞어 완성한다.",
        "cooking_time": 30,
        "difficulty": "보통"
    },
    {
        "title": "미소시루",
        "category": "일식",
        "ingredients": "된장, 두부, 대파, 다시마, 물",
        "instructions": "1. 물에 다시마를 넣고 육수를 낸다.\n2. 된장을 풀어준다.\n3. 두부와 대파를 넣고 끓인다.\n4. 약한 불에서 마무리한다.",
        "cooking_time": 15,
        "difficulty": "쉬움"
    },

    # =====================
    # 양식 5개
    # =====================
    {
        "title": "토마토 파스타",
        "category": "양식",
        "ingredients": "스파게티면, 토마토소스, 마늘, 양파, 올리브유, 소금, 후추",
        "instructions": "1. 스파게티면을 삶는다.\n2. 팬에 올리브유와 마늘을 넣고 볶는다.\n3. 양파와 토마토소스를 넣고 끓인다.\n4. 면을 넣고 버무린다.",
        "cooking_time": 30,
        "difficulty": "쉬움"
    },
    {
        "title": "크림 파스타",
        "category": "양식",
        "ingredients": "스파게티면, 생크림, 우유, 마늘, 양파, 베이컨, 치즈, 후추",
        "instructions": "1. 면을 삶는다.\n2. 팬에 베이컨, 마늘, 양파를 볶는다.\n3. 생크림과 우유를 넣고 끓인다.\n4. 면과 치즈를 넣고 섞는다.",
        "cooking_time": 35,
        "difficulty": "보통"
    },
    {
        "title": "치킨 샐러드",
        "category": "양식",
        "ingredients": "닭고기, 상추, 토마토, 오이, 양파, 올리브유, 소금, 후추",
        "instructions": "1. 닭고기를 굽거나 삶는다.\n2. 채소를 먹기 좋게 자른다.\n3. 그릇에 채소와 닭고기를 담는다.\n4. 올리브유, 소금, 후추로 간한다.",
        "cooking_time": 20,
        "difficulty": "쉬움"
    },
    {
        "title": "오믈렛",
        "category": "양식",
        "ingredients": "계란, 우유, 버터, 치즈, 양파, 소금, 후추",
        "instructions": "1. 계란과 우유를 섞는다.\n2. 팬에 버터를 녹인다.\n3. 계란물을 붓고 약한 불에서 익힌다.\n4. 치즈와 양파를 넣고 접어 완성한다.",
        "cooking_time": 15,
        "difficulty": "쉬움"
    },
    {
        "title": "함박스테이크",
        "category": "양식",
        "ingredients": "소고기, 돼지고기, 양파, 빵가루, 계란, 소금, 후추, 돈까스소스",
        "instructions": "1. 고기와 양파, 빵가루, 계란을 섞는다.\n2. 둥글게 모양을 만든다.\n3. 팬에 앞뒤로 굽는다.\n4. 소스를 올려 마무리한다.",
        "cooking_time": 45,
        "difficulty": "보통"
    },

    # =====================
    # 디저트 5개
    # =====================
    {
        "title": "팬케이크",
        "category": "디저트",
        "ingredients": "밀가루, 계란, 우유, 설탕, 버터, 베이킹파우더, 꿀",
        "instructions": "1. 밀가루, 계란, 우유, 설탕을 섞는다.\n2. 팬에 버터를 녹인다.\n3. 반죽을 올려 앞뒤로 굽는다.\n4. 꿀을 뿌려 완성한다.",
        "cooking_time": 25,
        "difficulty": "쉬움"
    },
    {
        "title": "프렌치토스트",
        "category": "디저트",
        "ingredients": "식빵, 계란, 우유, 설탕, 버터, 꿀",
        "instructions": "1. 계란, 우유, 설탕을 섞는다.\n2. 식빵을 계란물에 적신다.\n3. 팬에 버터를 녹이고 굽는다.\n4. 꿀을 곁들인다.",
        "cooking_time": 20,
        "difficulty": "쉬움"
    },
    {
        "title": "초코 쿠키",
        "category": "디저트",
        "ingredients": "밀가루, 버터, 설탕, 계란, 초콜릿, 베이킹파우더",
        "instructions": "1. 버터와 설탕을 섞는다.\n2. 계란과 밀가루를 넣어 반죽한다.\n3. 초콜릿을 넣고 모양을 만든다.\n4. 오븐에서 구워 완성한다.",
        "cooking_time": 50,
        "difficulty": "보통"
    },
    {
        "title": "딸기 요거트",
        "category": "디저트",
        "ingredients": "딸기, 요거트, 꿀, 견과류",
        "instructions": "1. 딸기를 깨끗하게 씻는다.\n2. 그릇에 요거트를 담는다.\n3. 딸기와 견과류를 올린다.\n4. 꿀을 뿌려 완성한다.",
        "cooking_time": 10,
        "difficulty": "쉬움"
    },
    {
        "title": "바나나 스무디",
        "category": "디저트",
        "ingredients": "바나나, 우유, 꿀, 얼음",
        "instructions": "1. 바나나를 자른다.\n2. 믹서에 바나나, 우유, 꿀, 얼음을 넣는다.\n3. 부드럽게 갈아준다.\n4. 컵에 담아 완성한다.",
        "cooking_time": 10,
        "difficulty": "쉬움"
    },

    # =====================
    # 기타 5개
    # =====================
    {
        "title": "참치마요 주먹밥",
        "category": "기타",
        "ingredients": "밥, 참치, 마요네즈, 김가루, 소금, 참기름",
        "instructions": "1. 참치의 기름을 제거한다.\n2. 참치와 마요네즈를 섞는다.\n3. 밥에 소금, 참기름, 김가루를 섞는다.\n4. 속을 넣고 주먹밥 모양을 만든다.",
        "cooking_time": 15,
        "difficulty": "쉬움"
    },
    {
        "title": "계란 샌드위치",
        "category": "기타",
        "ingredients": "식빵, 계란, 마요네즈, 소금, 후추, 양상추",
        "instructions": "1. 계란을 삶아 으깬다.\n2. 마요네즈, 소금, 후추를 섞는다.\n3. 식빵에 양상추와 계란 속을 넣는다.\n4. 먹기 좋게 자른다.",
        "cooking_time": 20,
        "difficulty": "쉬움"
    },
    {
        "title": "김치볶음밥",
        "category": "기타",
        "ingredients": "밥, 김치, 햄, 대파, 계란, 고추장, 참기름",
        "instructions": "1. 김치와 햄을 잘게 자른다.\n2. 팬에 대파를 볶는다.\n3. 김치, 햄, 밥을 넣고 볶는다.\n4. 계란프라이를 올린다.",
        "cooking_time": 20,
        "difficulty": "쉬움"
    },
    {
        "title": "감자전",
        "category": "기타",
        "ingredients": "감자, 소금, 식용유, 간장",
        "instructions": "1. 감자를 갈아준다.\n2. 물기를 살짝 제거하고 소금을 넣는다.\n3. 팬에 식용유를 두르고 부친다.\n4. 간장과 함께 먹는다.",
        "cooking_time": 25,
        "difficulty": "보통"
    },
    {
        "title": "라면 계란죽",
        "category": "기타",
        "ingredients": "라면, 밥, 계란, 대파, 물",
        "instructions": "1. 물을 끓이고 라면을 넣는다.\n2. 밥을 넣고 함께 끓인다.\n3. 계란을 풀어 넣는다.\n4. 대파를 올려 마무리한다.",
        "cooking_time": 15,
        "difficulty": "쉬움"
    },
]


def seed_recipes():
    conn, cursor = get_db()

    admin = cursor.execute(
        "SELECT id FROM users WHERE email = ?",
        ("admin@example.com",)
    ).fetchone()

    if not admin:
        print("관리자 계정을 찾을 수 없습니다.")
        conn.close()
        return

    admin_id = admin[0]

    inserted_count = 0
    skipped_count = 0

    for recipe in recipes:
        existing_recipe = cursor.execute(
            "SELECT id FROM recipes WHERE title = ? AND category = ?",
            (recipe["title"], recipe["category"])
        ).fetchone()

        if existing_recipe:
            skipped_count += 1
            continue

        cursor.execute("""
            INSERT INTO recipes
                (title, category, ingredients, instructions, cooking_time, difficulty, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            recipe["title"],
            recipe["category"],
            recipe["ingredients"],
            recipe["instructions"],
            recipe["cooking_time"],
            recipe["difficulty"],
            admin_id
        ))

        inserted_count += 1

    conn.commit()
    conn.close()

    print(f"샘플 레시피 추가 완료: {inserted_count}개")
    print(f"이미 존재해서 건너뜀: {skipped_count}개")


if __name__ == "__main__":
    seed_recipes()
