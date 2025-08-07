import logging
from flask import Flask, request, jsonify
from app.utility.worker import start_worker, queue
from app.handlers import webhook_handlers

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Start background worker thread
start_worker()


@app.route("/webhook", methods=["POST"])
def webhook():
    mode = request.form.get("mode")
    challenge = request.form.get("challenge")
    if mode == "subscribe" and challenge:
        return challenge, 200

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    logging.info(f"Received webhook: {data}")

    object_type = data.get("object")
    handler = webhook_handlers.get(object_type)
    if handler:
        queue.put((handler, data))
        logging.info(f"Queued handler for object type: {object_type}")
        return jsonify({"status": "queued"}), 200
    else:
        logging.warning(f"No handler for object type: {object_type}")
        return jsonify({"error": f"No handler for object type: {object_type}"}), 400


@app.route("/job/create", methods=["POST"])
def create_job():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    logging.info(f"Received create_job request: {data}")
    handler = webhook_handlers.get("CreateJob")
    if handler:
        queue.put((handler, data))
        logging.info("Queued create_job handler")
        return jsonify({"status": "job queued"}), 200
    else:
        logging.warning("No handler for create_job")
        return jsonify({"error": "No handler for create_job"}), 400


if __name__ == "__main__":
    app.run(debug=True)
