from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/nutrient"
mongo = PyMongo(app)

foodList = []  # 섭취목록이 저장됨
gender = "male"  # 성별, 기본값은 남성
recommend = "탄수화물"  # 추천할 성분, 기본값 탄수화물
servings = 0  # 몇 인분

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

# 현재까지 섭취한 영양분 계산
for food in foodList:

    # mongoDB에서 음식 정보 가져오기
    # collection에 컬렉션 이름 입력
    food_info = mongo.db.collection.find_one({"name": foodList}, {"탄수화물(g)": 1, "단백질(g)": 1, "지방(g)": 1, "에너지(kcal)": 1})

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


@app.route('/')
def index():
    return render_template('index.html', foodList=foodList, gender_selected=gender, recommend_selected=recommend, lackStr=lackStr)

# 식품명, 섭취량 읽어오기


@app.route('/list', methods=['POST'])
def getFoodList(food="None"):
    global servings
    foodList.append(request.form.get('food'))
    servings = request.form.get('servings')
    print(servings)
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
    global recommend
    if request.method == 'POST':
        recommend = request.form.get('recommend')
        return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=False, port=5500)
