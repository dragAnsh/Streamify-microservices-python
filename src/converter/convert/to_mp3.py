import pika, os
from bson.objectid import ObjectId
import tempfile, json
import moviepy.editor

def start(message, fs_videos, fs_mp3s, channel):
    message = json.loads(message)

    # create a temporary file
    tf = tempfile.NamedTemporaryFile()

    # fetch the video file from mongodb
    try:
        out = fs_videos.get(ObjectId(message["video_fid"]))
    except:
        return "Error fetching message from Videos MongoDB"
    
    # write contents of out to tf
    tf.write(out.read())

    # now convert the file to audio using moviepy module
    audio = moviepy.editor.VideoFileClip(tf.name).audio
    tf.close()

    # now save this audio inside a file
    tf_path = tempfile.gettempdir() + f"/{message['video_fid']}.mp3"
    audio.write_audiofile(tf_path)

    # save the audio file in mongodb
    f = open(tf_path, "rb")
    data = f.read()
    try:
        fid = fs_mp3s.put(data)
    except:
        return "Error while putting mp3 file to mongodb"
    f.close()
    os.remove(tf_path)
    
    message["mp3_fid"] = str(fid)

    # publish a message to mp3 queue
    try:
        channel.basic_publish(
            exchange="",
            routing_key=os.environ.get("MP3_QUEUE"),
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            )
        )
    except Exception as err:
        print(err)
        fs_mp3s.delete(fid)
        return "Error while publishing message to mp3 queue"
    
    
