from flask import Flask, request, jsonify, send_file
from pytube import YouTube
import re
import os
import tempfile
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Create downloads directory if it doesn't exist
DOWNLOAD_DIR = os.path.join(tempfile.gettempdir(), "yt_downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def sanitize_filename(title):
    # Ensures a secure, filesystem-safe filename
    return secure_filename(title)

def is_valid_youtube_url(url):
    # Accepts standard YouTube watch URLs and youtu.be shortened links
    pattern = r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]+"
    return re.match(pattern, url) is not None

def download_video(url, resolution):
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4', resolution=resolution).first()

        if not stream:
            return False, None, "Video with the specified resolution not found."

        sanitized_title = sanitize_filename(yt.title)
        filename = f"{sanitized_title}_{resolution}.mp4"
        file_path = os.path.join(DOWNLOAD_DIR, filename)
        stream.download(output_path=DOWNLOAD_DIR, filename=filename)
        return True, file_path, None
    except Exception as e:
        return False, None, str(e)

def get_video_info(url):
    try:
        yt = YouTube(url)
        video_info = {
            "title": yt.title,
            "author": yt.author,
            "length": yt.length,
            "views": yt.views,
            "description": yt.description,
            "publish_date": yt.publish_date.strftime("%Y-%m-%d") if yt.publish_date else None,
            "resolutions": [stream.resolution for stream in yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()]
        }
        return video_info, None
    except Exception as e:
        return None, str(e)

@app.route('/download/<resolution>', methods=['POST'])
def download_by_resolution(resolution):
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "Missing 'url' parameter in the request body."}), 400

    if not is_valid_youtube_url(url):
        return jsonify({"error": "Invalid YouTube URL."}), 400

    success, file_path, error_message = download_video(url, resolution)

    if success and file_path and os.path.exists(file_path):
        try:
            response = send_file(
                file_path,
                as_attachment=True,
                download_name=os.path.basename(file_path),
                mimetype='video/mp4'
            )
            # Clean up file after sending
            @response.call_on_close
            def remove_file():
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting file: {e}")
            return response
        except Exception as e:
            return jsonify({"error": f"Failed to send file: {str(e)}"}), 500
    else:
        return jsonify({"error": error_message or "Unknown error occurred."}), 500

@app.route('/video_info', methods=['POST'])
def video_info():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "Missing 'url' parameter in the request body."}), 400

    if not is_valid_youtube_url(url):
        return jsonify({"error": "Invalid YouTube URL."}), 400

    info, error_message = get_video_info(url)

    if info:
        return jsonify(info), 200
    else:
        return jsonify({"error": error_message or "Unable to fetch video info."}), 500

if __name__ == '__main__':
    app.run(debug=True)
