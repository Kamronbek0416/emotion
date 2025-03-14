from flask import render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, Result, db
from .utils import sanitize_filename, convert_numpy, normalize_emotions
import os
import uuid
import cv2
from deepface import DeepFace
from PIL import Image
import io
import json
import numpy as np
import pytz


def register_routes(app):
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            if not username or not password or not confirm_password:
                flash('Все поля обязательны для заполнения.', 'danger')
                return redirect(url_for('register'))

            if len(password) < 6 or not any(char.isdigit() for char in password) or not any(char.isalpha() for char in password):
                flash('Пароль должен быть длиной минимум 6 символов, содержать буквы и цифры.', 'danger')
                return redirect(url_for('register'))

            if password != confirm_password:
                flash('Пароли не совпадают. Попробуйте снова.', 'danger')
                return redirect(url_for('register'))

            if User.query.filter_by(username=username).first():
                flash('Пользователь с таким именем уже существует.', 'danger')
                return redirect(url_for('register'))

            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            flash('Вы успешно зарегистрировались! Теперь войдите.', 'success')
            return redirect(url_for('login'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                login_user(user)
                flash('Вы успешно вошли!', 'success')
                return redirect(url_for('home'))

            flash('Неверные данные для входа. Проверьте имя пользователя или пароль.', 'danger')

        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Вы вышли из системы.', 'success')
        return redirect(url_for('login'))

    @app.route('/')
    @login_required
    def home():
        return render_template('base.html', title="Welcome")

    @app.route('/image_analysis')
    @login_required
    def image_analysis():
        return render_template('image_analysis.html', title="Image Analysis")

    @app.route('/real_time_analysis')
    @login_required
    def real_time_analysis():
        return render_template('real_time_analysis.html', title="Real-time Analysis")

    @app.route('/analyze', methods=['POST'])
    @login_required
    def analyze():
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        file = request.files['image']
        file_name = sanitize_filename(str(uuid.uuid4()) + "_" + file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)

        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        file.save(file_path)

        try:
            results = DeepFace.analyze(file_path, actions=['emotion'], enforce_detection=False)
            if not isinstance(results, list):
                results = [results]

            img = cv2.imread(file_path)
            all_emotions = []

            for result in results:
                region = result.get("region")
                if region:
                    x, y, w, h = region["x"], region["y"], region["w"], region["h"]
                    emotion_dict = result["emotion"]

                    normalized_emotions = normalize_emotions(emotion_dict)
                    emotion = max(normalized_emotions, key=normalized_emotions.get)
                    confidence = normalized_emotions[emotion]

                    all_emotions.append({
                        "region": region,
                        "dominant_emotion": emotion,
                        "confidence": confidence,
                        "emotions": normalized_emotions
                    })

                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    label = f"{emotion} ({confidence:.1f}%)"
                    cv2.putText(img, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            result_image_path = os.path.join(app.config['RESULTS_FOLDER'], file_name)
            if not os.path.exists(app.config['RESULTS_FOLDER']):
                os.makedirs(app.config['RESULTS_FOLDER'])
            cv2.imwrite(result_image_path, img)

            results_serializable = convert_numpy(all_emotions)

            return jsonify({
                "results": results_serializable,
                "result_image_url": f"/results/{file_name}",
                "file_path": file_path
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            # Удаляем временный файл после анализа, если он не будет сохранен
            if os.path.exists(file_path):
                pass  # Оставляем файл, чтобы использовать в /save_result

    @app.route('/save_result', methods=['POST'])
    @login_required
    def save_result():
        try:
            data = request.get_json()
            if not data or 'results' not in data:
                return jsonify({"success": False, "error": "No results provided"}), 400

            for result in data['results']:
                result_record = Result(
                    user_id=current_user.id,
                    image_path=data['file_path'],  # Используем путь к оригинальному файлу
                    dominant_emotion=result['dominant_emotion'],
                    confidence=result['confidence'],
                    emotions=json.dumps(convert_numpy(result['emotions']))
                )
                db.session.add(result_record)

            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/analyze_realtime', methods=['POST'])
    @login_required
    def analyze_realtime():
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        file = request.files['image']

        try:
            image = Image.open(io.BytesIO(file.read()))
            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)

            if not isinstance(results, list):
                results = [results]

            if not results:
                return jsonify({"error": "No result from DeepFace"}), 400

            all_emotions = []
            for result in results:
                region = result.get("region")
                if region:
                    x, y, w, h = region["x"], region["y"], region["w"], region["h"]
                    emotion_dict = result["emotion"]

                    normalized_emotions = normalize_emotions(emotion_dict)
                    dominant_emotion = max(normalized_emotions, key=normalized_emotions.get)
                    confidence = round(normalized_emotions[dominant_emotion], 2)

                    all_emotions.append({
                        "region": region,
                        "dominant_emotion": dominant_emotion,
                        "confidence": confidence,
                        "emotions": normalized_emotions
                    })

            results_serializable = convert_numpy(all_emotions)

            return jsonify({
                "results": results_serializable
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/history')
    @login_required
    def history():
        user_id = current_user.id
        results = Result.query.filter_by(user_id=user_id).all()

        # Задаем локальный часовой пояс (например, Asia/Tashkent для UTC+5)
        local_tz = pytz.timezone('Asia/Tashkent')

        for result in results:
            if isinstance(result.emotions, str):
                result.emotions = json.loads(result.emotions)
            # Преобразуем время из UTC в локальный часовой пояс
            if result.timestamp:
                utc_time = result.timestamp.replace(tzinfo=pytz.UTC)  # Указываем, что время в UTC
                local_time = utc_time.astimezone(local_tz)  # Преобразуем в локальное время
                result.timestamp = local_time  # Обновляем объект

        return render_template('history.html', results=results)
    @app.route('/delete_result/<int:result_id>', methods=['POST'])
    @login_required
    def delete_result(result_id):
        try:
            result = Result.query.get_or_404(result_id)
            if result.user_id != current_user.id:
                return jsonify({"success": False, "error": "Unauthorized"}), 403

            # Удаляем файлы с диска
            upload_file_path = result.image_path
            result_file_name = os.path.basename(upload_file_path)
            result_file_path = os.path.join(app.config['RESULTS_FOLDER'], result_file_name)

            if os.path.exists(upload_file_path):
                os.remove(upload_file_path)
            if os.path.exists(result_file_path):
                os.remove(result_file_path)

            # Удаляем запись из базы данных
            db.session.delete(result)
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 500
    @app.route('/results/<path:filename>')
    def serve_result_image(filename):
        return send_file(os.path.join(app.config['RESULTS_FOLDER'], filename))