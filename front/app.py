import datetime
import base64
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, Response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from datetime import datetime, timedelta
from flask_pymongo import PyMongo
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/nutrient"
mongo = PyMongo(app)

foodList = []  # 섭취목록이 저장됨
foodName = ""  # 가장 최근 입력된 음식 이름
gender = "male"  # 성별, 기본값은 남성
recKeyWord = "탄수화물"  # 추천할 성분, 기본값 탄수화물
recList = []
servings = 0  # 몇 인분
foodOptions = []

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

recCarb = [recCarbMan, recCarbWoman]
recProtein = [recProteinMan, recProteinWoman]
recFat = [recFatMan, recFatWoman]
recKcal = [recKcalMan, recKcalWoman]

recommend_result = {}

lack = []  # 권장 섭취량 대비 부족한 성분, str, "탄수화물"/"단백질"/"지방"
lackStr = ""  # 템플릿에 전달할 문자열

graphMode = "today"

mongo.db.collection1.delete_many({"$or": [{"단백질(g)": {"$type": "string"}}, {"탄수화물(g)": {"$type": "string"}},
                                          {"지방(g)": {"$type": "string"}}, {"에너지(kcal)": {"$type": "string"}}]})

date = datetime.now().strftime('%Y-%m-%d')  # 현재의 날짜를 저장
TodayFood = mongo.db.collection2.find({"섭취일": date},
                                      {"_id": 0, "식품명": 1, "섭취량(인분)": 1, "탄수화물(g)": 1, "단백질(g)": 1, "지방(g)": 1,
                                       "에너지(kcal)": 1})

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

# 부족한 영양소 함유한 음식 상위 5개 출력
# aggregate 쿼리는 pipeline 리스트 안에 작성
def recommend_food(lack):
    global recommend_result
    nutdic = {"단백질": "단백질(g)", "탄수화물": "탄수화물(g)",
              "지방": "지방(g)", "에너지": "에너지(kcal)"}
    for item in lack:
        pipelines = [{"$match": {'1회제공량': {"$lte": 100}}},
                     {'$sort': {nutdic[item]: -1}},
                     {'$limit': 5},
                     {'$project': {"식품명": 1, "에너지(kcal)": 1, recKeyWord: 1, '_id': 0}}]

        result = mongo.db.collection1.aggregate(pipelines)
        recommend_result[item] = [doc["식품명"] for doc in result]
    print(recommend_result)
# 출력값 예시 : {'탄수화물': ['닭꼬치', '도미구이', '꿩불고기', '닭갈비', '더덕구이'], '단백질': ['닭꼬치', '도미구이', '꿩불고기', '닭갈비', '더덕구이']}


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

    recommend_food(lack)


###
lackfound()
if len(lack):
    for nutrient in lack:
        lackStr += f"{nutrient}, "

    lackStr += "영양소가 부족합니다."


def getRecFoodList(recKeyWord):
    print(recKeyWord)
    global recList
    recList.clear()
    recKeyWord += "(g)"

    pipelines = [{"$match":{'1회제공량':{"$lte":100}}},
                 {'$sort': {recKeyWord: -1}},
                 {'$limit': 5},
                 {'$project': {"식품명": 1, "에너지(kcal)": 1, recKeyWord: 1, '_id': 0}}]
    result = mongo.db.collection1.aggregate(pipelines)

    for food in result:
        foodDict = {"식품명": food["식품명"],
                    "성분": str(food[recKeyWord]), "열량": str(food["에너지(kcal)"])}
        recList.append(foodDict)


def drawTodayGraph():
    g = 0

    if gender == "male":
        g = 0
    else:
        g = 1

    words = ["carbo", "protein", "fat", "kcal"]
    value1 = [curCarb, curProtein, curFat, curKcal]
    value2 = [recCarb[g], recProtein[g], recFat[g], recKcal[g]]

    # 그래프 테스트용 데이터
    # value1 = [130, 57, 30, 1200]
    # value2 = [205, 60, 65, 2100]
    df = pd.DataFrame({'cur': value1, 'rec': value2}, index=words)

    fig, ax = plt.subplots(figsize=(12, 6))
    index = np.arange(4)
    bar1 = plt.bar(index - 0.15, df['cur'], 0.3,
                   alpha=0.4, color='blue', label="intake")
    bar2 = plt.bar(index + 0.15, df['rec'], 0.3,
                   alpha=0.4, color='purple', label="recommend")

    # 막대 안에 값을 표시
    for i, rect in enumerate(bar1):
        height = rect.get_height()
        plt.text(rect.get_x() + rect.get_width() / 2,
                 height, value1[i], ha='center', va='bottom')

    for i, rect in enumerate(bar2):
        height = rect.get_height()
        plt.text(rect.get_x() + rect.get_width() / 2,
                 height, value2[i], ha='center', va='bottom')

    plt.xticks(np.arange(0, 4, 1), words)
    plt.xlabel('nutrients', size=13)
    plt.legend()

    canvas = FigureCanvas(fig)
    png_output = BytesIO()
    canvas.print_png(png_output)
    png_output.seek(0)
    png_as_string = base64.b64encode(png_output.getvalue()).decode()

    return png_as_string


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
    lackfound()

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
        {"$match": {"섭취일": {"$gte": seven_days_ago_str, "$lt": today_str}}},
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
    dates = []
    carbohydrate_totals = []
    protein_totals = []
    fat_totals = []
    kcal_totals = []

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

    # dates = ['2023-06-04', '2023-06-05', '2023-06-06',
    #          '2023-06-07', '2023-06-08', '2023-06-09', '2023-06-10']
    # carbohydrate_totals = [12, 13, 21, 32, 10, 9, 29]
    # protein_totals = [11, 10, 20, 18, 9, 30, 17]
    # fat_totals = [9, 8, 10, 19, 4, 14, 21]
    # kcal_totals = [2100, 2400, 2323, 2200, 2199, 2345, 2321]

    # 원 그래프 그리기
    labels = dates
    colors = ["#FFA500", "#FFD700", "#FFA07A",
              "#FF6347", "#FF8C00", "#FF4500", "#FF7F50"]

    fig, axes = plt.subplots(2, 2)  # 2x2 서브플롯 생성

    # 탄수화물 그래프
    axes[0, 0].pie(carbohydrate_totals, labels=labels,
                   colors=colors, autopct='%1.1f%%', startangle=90)
    axes[0, 0].set_title("Carbohydrate Intake Ratio")

    # 단백질 그래프
    axes[0, 1].pie(protein_totals, labels=labels, colors=colors,
                   autopct='%1.1f%%', startangle=90)
    axes[0, 1].set_title("Protein Intake Ratio")

    # 지방 그래프
    axes[1, 0].pie(fat_totals, labels=labels, colors=colors,
                   autopct='%1.1f%%', startangle=90)
    axes[1, 0].set_title("Fat Intake Ratio")

    # 에너지 그래프
    axes[1, 1].pie(kcal_totals, labels=labels, colors=colors,
                   autopct='%1.1f%%', startangle=90)
    axes[1, 1].set_title("Energy Intake Ratio")

    plt.tight_layout()

    canvas = FigureCanvas(fig)
    png_output = BytesIO()
    canvas.print_png(png_output)
    png_output.seek(0)
    png_as_string = base64.b64encode(png_output.getvalue()).decode()

    return png_as_string


@app.route('/')
def index():

    if graphMode == "today":
        image_data = drawTodayGraph()
    else:
        image_data = nutrient_pie_chart()
        # 추후 주간 그래프 그리는 함수 호출로 수정

    params = {
        "foodList": foodList,
        "gender_selected": gender,
        "recommend_selected": recKeyWord,
        "graphMode_selected": graphMode,
        "lackStr": lackStr,
        "curCarb": str(curCarb),
        "curProtein": str(curProtein),
        "curFat": str(curFat),
        "curKcal": str(curKcal),
        "recList": recList,
        "recKeyWord": recKeyWord+"(g)",
        "foodOptions": foodOptions,
        "graph": "data:image/png;base64," + image_data,
        "lackStr": lackStr,
        "recommend_result": recommend_result
    }

    return render_template('index.html', params=params)


@app.route('/search', methods=['POST'])
def searchFoodList():
    global foodName, foodDict

    foodName = request.form.get('food')
    print(foodName)
    pipelines = [{"$match": {"식품명": {"$regex": "^"+foodName}}},
                 {"$sort": {"에너지(kcal)": 1}},
                 {"$project": {"_id": 0, "식품명": 1,
                               "에너지(kcal)": 1, "1회제공량": 1, "내용량_단위": 1}},
                 {"$limit": 10}]
    result = mongo.db.collection1.aggregate(pipelines)

    for food in result:
        foodDict = {"식품명": food["식품명"],
                    "1회제공량": str(food["1회제공량"]), "단위": food["내용량_단위"]}
        foodOptions.append(foodDict)

    return redirect(url_for('index'))


@app.route('/list', methods=['POST'])
def getFoodList(food="None"):
    global servings, foodName, foodList
    foodName = request.form.get('foodName')
    servings = int(request.form.get('servings'))
    foodList.append(foodName)
    find_food = mongo.db.collection1.find_one({"식품명": foodName},
                                        {"_id": 0, "식품명": 1, "탄수화물(g)": 1, "단백질(g)": 1, "지방(g)": 1, "에너지(kcal)": 1, "1회제공량": 1, "내용량_단위": 1})

    insert_collection(find_food, servings)

    return redirect(url_for('index'))


# 성별 읽어오기

@app.route('/gender', methods=['POST'])
def getGender():
    global gender
    if request.method == 'POST':
        gender = request.form.get('gender')
    print(gender)
    print(foodList)
    return redirect(url_for('index'))

# 검색할 성분 읽어오기


@app.route('/recommend', methods=['POST'])
def getRecommendWord():
    global recKeyWord
    if request.method == 'POST':
        recKeyWord = request.form.get('recommend')
        getRecFoodList(recKeyWord=recKeyWord)
        return redirect(url_for('index'))


@app.route('/graph', methods=['POST'])
def getGraph():
    global graphMode
    graphMode = request.form.get('graphMode')
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=False, port=5500)
