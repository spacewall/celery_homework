import nanoid
from flask import Flask, jsonify, request, send_from_directory
from flask.views import MethodView
from flask_pymongo import PyMongo

from celery_app import celery_app, get_task, upscaler, APP_NAME, MONGO_DSN

flask_app = Flask(APP_NAME)
mongo = PyMongo(flask_app, MONGO_DSN)
celery_app.conf.update(flask_app.config)


class ContextTask(celery_app.Task):
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)
        

celery_app.Task = ContextTask


class UpscaleView(MethodView):
    def get(self, task_id: str):
        task = get_task(task_id)
        status = task.status
        task_states = ("FAILURE", "SUCCESS")
        if status in task_states:
            return jsonify({"status": status, "result": task.result, "file": ...})
        
        else:
            return jsonify({"status": status, "result": task.result})

    def post(self):
        image_id = self.save_image("new_image")
        task = upscaler.delay(image_id)

        return jsonify({"task_id": task.id})

    def save_image(self, file_name: str) -> str:
        image = request.files.get(file_name)

        return str(mongo.save_file(f"{nanoid.generate()}_{image.filename}", image))
    

# class FileView(MethodView):
#     def get(self):


upscale_view = UpscaleView.as_view("upscale")
flask_app.add_url_rule("/tasks/<string:task_id>", view_func=upscale_view, methods=["GET"])
flask_app.add_url_rule("/upscale", view_func=upscale_view, methods=["POST"])

if __name__ == '__main__':
    flask_app.run()
