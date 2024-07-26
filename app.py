import nanoid
from flask import Flask, abort, jsonify, make_response, request
from flask.views import MethodView
from flask_pymongo import PyMongo

from celery_app import celery_app, get_task, upscaler, APP_NAME, MONGO_DSN, get_fs, ObjectId

flask_app = Flask(APP_NAME)
mongo = PyMongo(flask_app, uri=MONGO_DSN)
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
            return jsonify({"status": status, "file": f"/processed/{task.result}"})
        
        else:
            return jsonify({"status": status})

    def post(self):
        image_id = self.save_image()
        task = upscaler.delay(image_id)

        return jsonify({"task_id": task.id})

    def save_image(self) -> str:
        image = request.files.get("image")

        return str(mongo.save_file(f"{nanoid.generate()}_{image.filename}", image))
    

@flask_app.route("/processed/<string:image_id>")
def get_image(image_id: str):
    try:
        files = get_fs()
        
        with files.get(ObjectId(image_id)) as file:
            format = f"{file.filename.split(".")[-1]}"
            response = make_response(file.read())
            response.headers.set("Content-Type", f"image/{format}")
            response.headers.set("Content-Disposition", "attachment", filename=file.name)

            return response
    
    except FileNotFoundError:
        abort(404)

upscale_view = UpscaleView.as_view("upscale")
flask_app.add_url_rule("/tasks/<string:task_id>", view_func=upscale_view, methods=["GET"])
flask_app.add_url_rule("/upscale", view_func=upscale_view, methods=["POST"])

if __name__ == '__main__':
    flask_app.run()
