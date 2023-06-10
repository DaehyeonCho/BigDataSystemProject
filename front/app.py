import base64
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, Response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
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

graphMode = "today"


def drawTodayGraph():
    g = 0

    if gender == "male":
        g = 0
    else:
        g = 1

    words = ["carbo", "protein", "fat", "kcal"]
    # value1 = [curCarb, curProtein, curFat, curKcal]
    # value2 = [recCarb[g], recProtein[g], recFat[g], recKcal[g]]

    # 그래프 테스트용 데이터
    value1 = [130, 57, 30, 1200]
    value2 = [205, 60, 65, 2100]
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


@app.route('/graph', methods=['POST'])
def getGraph():
    global graphMode
    graphMode = request.form.get('graphMode')
    return redirect(url_for('index'))


# 현재까지 섭취한 영양분 계산
for food in foodList:

    # mongoDB에서 음식 정보 가져오기
    # collection에 컬렉션 이름 입력
    food_info = mongo.db.col_3.find_one(
        {"name": foodList}, {"탄수화물(g)": 1, "단백질(g)": 1, "지방(g)": 1, "에너지(kcal)": 1})

    # 음식 정보 추출해서 cur 변수에 저장
    if food_info:
        carbo = food_info.get("탄수화물(g)")
        protein = food_info.get("단백질(g)")
        fat = food_info.get("지방(g)")
        kcal = food_info.get("에너지(kcal)")

        curCarb += carbo * servings
        curProtein += protein * servings
        curFat += fat * servings
        curKcal += kcal * servings
        print(curCarb)

lack = []  # 권장 섭취량 대비 부족한 성분, str, "탄수화물"/"단백질"/"지방"

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

#

# 단순 성분별 내림차순


def getRecFoodList(recKeyWord):
    print(recKeyWord)
    global recList
    recList.clear()
    recKeyWord += "(g)"
    pipelines = [{'$sort': {recKeyWord: -1}}, {'$limit': 5},
                 {'$project': {"식품명": 1, "에너지(kcal)": 1, recKeyWord: 1, '_id': 0}}]
    # 1g미만 수정 필요
    result = mongo.db.col_3.aggregate(pipelines)

    for food in result:
        foodDict = {"식품명": food["식품명"],
                    "성분": str(food[recKeyWord]), "열량": str(food["에너지(kcal)"])}
        recList.append(foodDict)


@app.route('/')
def index():

    if graphMode == "today":
        image_data = drawTodayGraph()
    else:
        image_data = drawTodayGraph()
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
        "graph": "data:image/png;base64," + image_data
    }

    return render_template('index.html', params=params)


@app.route('/search', methods=['POST'])
def searchFoodList():
    global foodName, foodDict
    foodName = request.form.get('food')
    pipelines = [{"$match": {"식품명": {"$regex": "^"+foodName}}}, {"$sort": {"에너지(kcal)": 1}}, {
        "$project": {"_id": 0, "식품명": 1, "에너지(kcal)": 1, "1회제공량": 1, "내용량_단위": 1}}, {"$limit": 10}]

    result = mongo.db.col_3.aggregate(pipelines)

    for food in result:
        foodDict = {"식품명": food["식품명"],
                    "1회제공량": str(food["1회제공량"]), "단위": food["내용량_단위"]}
        foodOptions.append(foodDict)

    return redirect(url_for('index'))


@app.route('/list', methods=['POST'])
def getFoodList(food="None"):
    global servings, foodName
    foodName = request.form.get('foodName')
    print(foodName)
    foodList.append(foodName)
    servings = request.form.get('servings')
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


if __name__ == "__main__":
    app.run(debug=False, port=5500)
