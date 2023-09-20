import pika, json


def upload(f, fs, channel, access):
    try:
        # we will try to put the file in mongodb
        fid = fs.put(f) # if file is succesfully put then it returns a file_id object
    except Exception as err:
        return f"Internal Server Error DB\n{err}", 500

    # now as file is succesfully put inside MongoDB we can create a message and publish it to the queue
    message = {
        "video_fid": str(fid),
        "mp3_fid": None,
        "username": access["username"]
    }

    try:
        channel.basic_publish(
            exchange="",
            routing_key="video",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            )
        )
    except Exception as err:
        fs.delete(fid)
        return f"Internal Server Error Q\n{err}", 500