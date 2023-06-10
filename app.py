from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/nutrient"#db_name=nutrient
mongo = PyMongo(app)

############## 인덱스 추가(collection 이름 project)
mongo.db.collection.create_index([("식품명", 1),("에너지(kcal)", 1)])

foodList = []  # 섭취목록이 저장됨
gender = "male"  # 성별, 기본값은 남성
recommend = "탄수화물"  # 추천할 성분, 기본값 탄수화물
servings = 0  # 몇 인분

# 대현님이 사용하실 변수들(라우트 함수 내에서 global 키워드 붙여서 전역변수로 사용)
curCarb = 0  # 현재까지의 탄수화물 섭취량
curProtein = 0  # 현재까지의 단백질 섭취량
curFat = 0  # 현재까지의 지방 섭취량
curKcal = 0  # 현재까지의 칼로리

recCarb = 0  # 권장탄수화물 섭취량
recProtein = 0  # 권장 단백질 섭취량
recFat = 0  # 권장 지방 섭취량
recKcal = 0  # 권장 섭취 칼로리

lack = []  # 권장 섭취량 대비 부족한 성분, str, "탄수화물"/"단백질"/"지방"

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
