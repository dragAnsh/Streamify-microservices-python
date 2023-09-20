import os, gridfs, pika, json
from flask import Flask, request, send_file
from bson.objectid import ObjectId
from flask_pymongo import PyMongo
from auth_svc import access
from auth import validate
from storage import util
from signup_svc import user

server = Flask(__name__)

# create a mongo client and gridfs object
mongo_video = PyMongo(server, uri = "mongodb://host.minikube.internal:27017/videos")
mongo_mp3 = PyMongo(server, uri = "mongodb://host.minikube.internal:27017/mp3s")

fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)

# create a connection for rabbitmq
connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq")) # here "rabbitmq" will resolve to the host name where rabbitmq is hosted
channel = connection.channel()


@server.route("/signup", methods=["POST"])
def signup():
    token, err = user.register(request)
    if err:
        return err
    else:
        return token


@server.route("/login", methods=["POST"])
def login():
    token, err = access.login(request)

    if not err:
        return token, 200
    else:
        return err


@server.route("/upload", methods=["POST"])
def upload():
    access, err = validate.token(request)

    if err:
        return err
    
    access = json.loads(access)
    if access["admin"]:
        if len(request.files) > 1 or len(request.files) < 1:
            return "exactly 1 file required", 400
        
        for _, f in request.files.items():
            err = util.upload(f, fs_videos, channel, access)

            if err:
                return err
            
        return "success!", 200

    return "not authorized", 401


@server.route("/download", methods=["GET"])
def download():
    access, err = validate.token(request)

    if err:
        return err

    access = json.loads(access)

    if access["admin"]:
        fid_string = request.args.get("fid")

        if not fid_string:
            return "File ID is required", 400

        try:
            out = fs_mp3s.get(ObjectId(fid_string))
        except Exception as err:
            return f"Internal Server Error While Fetching MP3:\n {err}", 500
        
        try:
            return send_file(out, download_name=f"{fid_string}.mp3")
        except:
            return "Internal Server Error While Sending MP3", 500
        
    return "Not Authorized", 401


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)