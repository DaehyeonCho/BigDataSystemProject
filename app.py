from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/nutrient"
mongo = PyMongo(app)

############## 에너지, 탄수화물, 단백질, 지방에 대한 데이터가 문자형인 경우 삭제
mongo.db.collection1.delete_many({"$or": [{"단백질(g)": {"$type": "string"}}, {"탄수화물(g)": {"$type": "string"}},
                                          {"지방(g)": {"$type": "string"}}, {"에너지(kcal)": {"$type": "string"}}]})

foodList = []  # 섭취목록이 저장됨
gender = "male"  # 성별, 기본값은 남성
recommend = "탄수화물"  # 추천할 성분, 기본값 탄수화물
servings = 0  # 몇 인분

############## 인덱스 추가
mongo.db.collection1.create_index([("식품명", 1), ("에너지(kcal)", 1)])

# 대현님이 사용하실 변수들(라우트 함수 내에서 global 키워드 붙여서 전역변수로 사용)
curCarb = 0  # 현재까지의 탄수화물 섭취량
curProtein = 0  # 현재까지의 단백질 섭취량
curFat = 0  # 현재까지의 지방 섭취량
curKcal = 0  # 현재까지의 칼로리

recCarbMan = 275  # 남자 권장 탄수화물 섭취량
recProteinMan = 73  # 남자 권장 단백질 섭취량
recFatMan = 77  # 남자 권장 지방 섭취량
recKcalMan = 2600  # 남자 권장 섭취 칼로리

recCarbWoman = 205  # 여자 권장 탄수화물 섭취량
recProteinWoman = 60  # 여자 권장 단백질 섭취량
recFatWoman = 65  # 여자 권장 지방 섭취량
recKcalWoman = 2100  # 여자 권장 섭취 칼로리

date = datetime.now().strftime('%Y-%m-%d')  # 현재의 날짜를 저장
TodayFood = mongo.db.collection2.find({"섭취일": date},
                                      {"_id": 0, "식품명": 1, "섭취량(인분)": 1, "탄수화물(g)": 1, "단백질(g)": 1, "지방(g)": 1,
                                       "에너지(kcal)": 1})

# 오늘 현재까지 섭취한 영양분 계산(서버 새로 켜질 때 mongodb에서 받아옴)
for food in TodayFood:
    # mongoDB에서 음식 정보 가져오기
    # collection2에 컬렉션 이름 입력(새로 저장된 collection)
    foodList.append(food.get("식품명"))  # index.html에 출력시켜줄 foodList에 식품명 저장
    # 음식 정보 추출해서 cur 변수에 저장
    carbo = food.get("탄수화물(g)")
    protein = food.get("단백질(g)")
    fat = food.get("지방(g)")
    kcal = food.get("에너지(kcal)")

    curCarb += carbo * food.get("섭취량(인분)")
    curProtein += protein * food.get("섭취량(인분)")
    curFat += fat * food.get("섭취량(인분)")
    curKcal += kcal * food.get("섭취량(인분)")

lack = []  # 권장 섭취량 대비 부족한 성분, str, "탄수화물"/"단백질"/"지방"


def lackfound():
    global lack
    lack = []  # 음식 들어올 때 확인하고, 확인할 때마다 초기화
    if gender == "male":
        if (recCarbMan - curCarb) > 0:
            lack.append("탄수화물")
        if (recProteinMan - curProtein) > 0:
            lack.append("단백질")
        if (recFatMan - curFat) > 0:
            lack.append("지방")
        if (recKcalMan - curKcal) > 0:
            lack.append("에너지")
    else:
        if (recCarbWoman - curCarb) > 0:
            lack.append("탄수화물")
        if (recProteinWoman - curProtein) > 0:
            lack.append("단백질")
        if (recFatWoman - curFat) > 0:
            lack.append("지방")
        if (recKcalWoman - curKcal) > 0:
            lack.append("에너지")


###

lackStr = ""  # 템플릿에 전달할 문자열

for nutrient in lack:
    lackStr += f"{nutrient} "

lackStr += "영양소가 부족합니다."


#

def Week():  # 현재 주차의 월~일까지의 날짜 str list 반환
    now = datetime.now()
    start_of_week = now - timedelta(days=now.weekday())  # 현재 주의 월요일 날짜 계산
    end_of_week = start_of_week + timedelta(days=6)  # 현재 주의 일요일 날짜 계산
    Week_array = []  # 해당 주차의 날짜 반환용
    # 월요일부터 일요일까지의 날짜 출력
    current_date = start_of_week
    while current_date <= end_of_week:
        Week_array.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    return Week_array


def insert_collection(find_food, servings):  # 찾은 음식과 인분 수 넣으면
    global curFat, curKcal, curCarb, curProtein
    date = datetime.now().strftime('%Y-%m-%d')  # 현재의 날짜를 저장
    new_data = {"식품명": find_food["식품명"], "섭취일": date, "섭취량(인분)": servings, "탄수화물(g)": find_food["탄수화물(g)"],
                "단백질(g)": find_food["단백질(g)"], "지방(g)": find_food["지방(g)"], "에너지(kcal)": find_food["에너지(kcal)"]}
    mongo.db.collection2.insert_one(new_data)  # 음식 저장하는 collection2에 데이터 추가
    carbo = find_food.get("탄수화물(g)")
    protein = find_food.get("단백질(g)")
    fat = find_food.get("지방(g)")
    kcal = find_food.get("에너지(kcal)")

    curCarb += carbo * servings
    curProtein += protein * servings
    curFat += fat * servings
    curKcal += kcal * servings

#################################################
# 부족한 영양소 함유한 음식 상위 5개 출력
# aggregate 쿼리는 pipeline 리스트 안에 작성
def recommend_food(lack):
    recommend_result = {}
    nutdic = {"단백질": "단백질(g)", "탄수화물": "탄수화물(g)", "지방": "지방(g)", "에너지": "에너지(kcal)"}
    for item in lack:
        pipeline = [
            {"$project": {"_id": 0, "식품명": 1}},
            {"$sort": {nutdic[item]: -1}},
            {"$limit": 5}
        ]
        result = mongo.db.collection2.aggregate(pipeline)
        recommend_result[item] = [doc["식품명"] for doc in result]
    return recommend_result

# 출력값 예시 : {'탄수화물': ['닭꼬치', '도미구이', '꿩불고기', '닭갈비', '더덕구이'], '단백질': ['닭꼬치', '도미구이', '꿩불고기', '닭갈비', '더덕구이']}

# 지난 7일간 각 영양소별로 일일마다 섭취한 양의 비율 원그래프로 그리는 함수
def nutrient_pie_chart():
    # 오늘 날짜 계산
    today = datetime.now()

    # 7일 전 날짜 계산
    seven_days_ago = today - timedelta(days=7)

    today_str = today.strftime('%Y-%m-%d')
    seven_days_ago_str = seven_days_ago.strftime('%Y-%m-%d')

    # 날짜별 영양소 섭취량 조회
    pipeline = [
        {"$match": {"섭취일": {"$gte": seven_days_ago_str, "$lte": today_str}}},
        {"$group": {
            "_id": "$섭취일",
            "total_carbohydrate": {"$sum": "$탄수화물(g)"},
            "total_protein": {"$sum": "$단백질(g)"},
            "total_fat": {"$sum": "$지방(g)"},
            "total_kcal": {"$sum": "$에너지(kcal)"}
        }}
    ]

    result = mongo.db.collection2.aggregate(pipeline)
    data = list(result)

    # 날짜별 영양소 섭취량 총합 계산
    dates = ['2023-06-11', '2023-06-10', '2023-06-09', '2023-06-08', '2023-06-07', '2023-06-06', '2023-06-05']
    carbohydrate_totals = [10, 11, 13, 14, 20, 19, 21]
    protein_totals = [20, 21, 23, 32, 28, 26, 34]
    fat_totals = [2, 4, 9, 11, 3, 7, 14]
    kcal_totals = [2100, 2300, 2211, 2321, 2400, 2500, 2345]

    for item in data:
        graph_date = item["_id"]
        total_carbohydrate = item["total_carbohydrate"]
        total_protein = item["total_protein"]
        total_fat = item["total_fat"]
        total_kcal = item["total_kcal"]

        dates.append(graph_date)
        carbohydrate_totals.append(total_carbohydrate)
        protein_totals.append(total_protein)
        fat_totals.append(total_fat)
        kcal_totals.append(total_kcal)

    # 원 그래프 그리기
    labels = dates
    colors = ["#FFA500", "#FFD700", "#FFA07A", "#FF6347", "#FF8C00", "#FF4500", "#FF7F50"]

    fig, axes = plt.subplots(2, 2)  # 2x2 서브플롯 생성

    # 탄수화물 그래프
    axes[0, 0].pie(carbohydrate_totals, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    axes[0, 0].set_title("Carbohydrate Intake Ratio")

    # 단백질 그래프
    axes[0, 1].pie(protein_totals, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    axes[0, 1].set_title("Protein Intake Ratio")

    # 지방 그래프
    axes[1, 0].pie(fat_totals, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    axes[1, 0].set_title("Fat Intake Ratio")

    # 에너지 그래프
    axes[1, 1].pie(kcal_totals, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    axes[1, 1].set_title("Energy Intake Ratio")

    plt.tight_layout()
    plt.show()
###################################################################
@app.route('/')
def index():
    return render_template('index.html', foodList=foodList, gender_selected=gender, recommend_selected=recommend,
                           lackStr=lackStr)


# 식품명, 섭취량 읽어오기


@app.route('/list', methods=['POST'])
def getFoodList(food="None"):
    global servings
    food = request.form.get('food')
    find_food = mongo.db.collection1.aggregate(
        [{"$match": {"식품명": {"$regex": "^" + food}}}, {"$sort": {"에너지(kcal)": 1}}, {
            "$project": {"_id": 0, "식품명": 1, "탄수화물(g)": 1, "단백질(g)": 1, "지방(g)": 1, "에너지(kcal)": 1, "1회제공량": 1,
                         "내용량_단위": 1}}, {"$limit": 1}])
    find_food_list = list(find_food)
    if not find_food_list:
        return redirect(url_for('index'))
    foodList.append(find_food_list[0]["식품명"])
    servings = int(request.form.get('servings'))
    insert_collection(find_food_list[0], servings)
    return redirect(url_for('index'))


# 성별 읽어오기

@app.route('/gender', methods=['POST'])
def getGender():
    global gender
    if request.method == 'POST':
        gender = request.form.get('gender')
    return redirect(url_for('index'))


# 검색할 성분 읽어오기
@app.route('/recommend', methods=['POST'])
def getRecommendWord():
    global recommend
    if request.method == 'POST':
        recommend = request.form.get('recommend')
        return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=False, port=5500)
