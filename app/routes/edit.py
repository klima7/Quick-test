from flask import render_template, flash, redirect, url_for, request, session
from flask_login import login_required, current_user
from app import app
from app.models import *


# @app.route('/edit/structure/<action>/<param>', methods=['GET', 'POST'])
def quiz_edit_structure(action, param, test_obj, img_url=None):
    print('quiz edit', test_obj)
    if action == 'add_question' and param in ['0', '1', '2']:
        question = Question(type=int(param), question='', points=1.0, data=None, nr=len(test_obj.questions), image=[])

        if param in ['0', '1']:
            question.data = {'all': [''], 'correct': [] if param == '0' else -1}

        test_obj.questions.append(question)
        db.session.add(question)
        db.session.add(test_obj)
        db.session.commit()
        # return redirect('/edit/' + str(test_obj.id) + '/' + str(len(test_obj.questions)))
        return redirect(f'/edit/{test_obj.id}/{str(len(test_obj.questions))}')
    elif action == 'remove_question':
        print('Removing question')
        index = int(param) - 1

        # To na dole nie działa, i pytania nie są usuwane z bazy danych.
        # Question.query.filter_by(id=test_obj.questions[index].id).delete()
        del test_obj.questions[index]
        db.session.add(test_obj)
        db.session.commit()
        return redirect(f'/edit/{test_obj.id}/{index}')
    elif action == 'remove_image':
        print('param', param)
        spit = param.split(';')
        param = {'image_index': int(spit[1]), 'question_number': int(spit[0])}
        image_i = param['image_index']
        question = test_obj.questions[param['question_number']]
        if image_i >= len(question.image):
            flash('Błędny indeks zdjęcia.', 'error')
        else:
            new_list = [i + '' for i in question.image]
            del new_list[image_i]
            question.image = new_list

            db.session.add(question)
            db.session.add(test_obj)
            db.session.commit()

        return redirect(f'/edit/{test_obj.id}/{param["question_number"]}')
    elif action == 'add_image':
        if img_url is None:
            flash('Brak url nowego zdjęcia', 'error')
        else:
            question = test_obj.questions[int(param)]
            new_list = [i + '' for i in question.image]
            new_list.append(img_url)
            question.image = new_list

            db.session.add(question)
            db.session.add(test_obj)
            db.session.commit()

        return redirect(f'/edit/{test_obj.id}/{int(param)}')
        # return redirect(f'/edit/{test_obj.id}/1')


def update_test_question(form, test_obj):
    print(form)
    question_index = form.get('question_index')
    index = int(question_index) - 1
    question_type = form.get('question_type')

    title = form.get('title')
    points = form.get('points')
    question_content = form.get('question')

    print('index', index, 'rest', title, points, question_content)

    test_obj.title = title
    question = test_obj.questions[index]
    question.points = float(points)
    question.question = question_content

    if question_type in ['0', '1']:
        answers = form.getlist('anwser_text')
        correct_answers = form.getlist('answer')

        question.data = {}
        question.data['all'] = answers
        question.data['correct'] = [ int(i) for i in correct_answers ]
        if question_type == '1' and len(question.data['correct']) == 1:
            question.data['correct'] = question.data['correct'][0]
        print('updated data ', question.data)
    db.session.add(test_obj)
    db.session.add(question)
    db.session.commit()
    db.session.flush()


@app.route('/edit/')
@login_required
def quiz_edit_new():
    teacher = current_user
    test = Test(title="Nowy test")
    teacher.tests.append(test)
    db.session.add(test)
    db.session.commit()
    session['editing_id'] = test.id
    return redirect(url_for('quiz_edit', test_id=test.id))

@app.route('/edit/<int:test_id>')
@app.route('/edit/<int:test_id>/<int:number>', methods=['POST', 'GET'])
@app.route('/edit/<int:test_id>/-1/<action>/<param>', methods=['GET', 'POST'])
@login_required
def quiz_edit(test_id=None, number=None, action=None, param=None):
    test = Test.query.filter_by(id=test_id).first()
    print(test_id, test)

    if test is None:
        flash('Nieznany test', 'error')
        return redirect(url_for('manage'))

    editable = session.get('editing_id')
    if not editable:
        return redirect(url_for('test_preview', test_id=test.id))

    if len(request.form) > 0 and 'new_img_url' not in request.form:
        update_test_question(request.form, test)

    if action is not None and param is not None and editable:
        return quiz_edit_structure(action, param, test, img_url=request.form.get('new_img_url'))

    if number is None:
        return redirect(f'/edit/{test_id}/1')

    number -= 1
    questions = test.questions

    if number < 0 or number >= len(questions):
        number = 0

    question = questions[number] if number < len(questions) else None
    return render_template('test_edit.html', test_params=test, question=question, number_of_questions=len(test.questions), current_index=number + 1)



