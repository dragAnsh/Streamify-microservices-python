import pika, gridfs, sys, os
from pymongo import MongoClient
from convert import to_mp3


def main():
    client = MongoClient(host="host.minikube.internal", port=27017)
    db_videos = client.videos
    db_mp3s = client.mp3s

    # gridfs
    fs_videos = gridfs.GridFS(db_videos)
    fs_mp3s = gridfs.GridFS(db_mp3s)

    # rabbitmq connection and channel
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
    channel = connection.channel()

    # callback function
    def callback(ch, method, properties, body):
        err = to_mp3.start(body, fs_videos, fs_mp3s, ch)
        if err:
            ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    # subscribe to the video queue
    channel.basic_consume(
        queue=os.environ.get("VIDEO_QUEUE"),
        on_message_callback=callback
    )

    # start consuming messages
    print("Waiting for messages! Press CTRL+C to stop consuming messages")
    channel.start_consuming()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)