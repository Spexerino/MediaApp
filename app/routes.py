from flask import Blueprint, render_template, send_from_directory, abort, request, Response, current_app
import os
import cv2
import math
from app.models import Camera


main = Blueprint('main', __name__)

@main.app_context_processor
def inject_cameras():
    cameras = Camera.query.order_by(Camera.name).all()
    return dict(nav_cameras=cameras)

# a simple page that says hello
@main.route('/',defaults={'year':None, 'month':None, 'day':None,'filename':None})
@main.route('/<year>',defaults={'month':None, 'day':None,'filename':None})
@main.route('/<year>/<month>',defaults={'day':None,'filename':None})
@main.route('/<year>/<month>/<day>',defaults={'filename':None})
@main.route('/<year>/<month>/<day>/<filename>')
def home(year,month,day,filename):
    
    if filename == None:
        if day == None:
            dir_list = get_dir_list(year,month,day)
            return render_template("home.html",dir_list=dir_list,year=year,month=month,day=day)
        else:
            per_page = 9
            dir_list = get_dir_list(year,month,day)
            page = request.args.get('page', 1, type=int)
            start = (page - 1) * per_page
            end = start + per_page
            videos = dir_list[start:end]
            total = len(dir_list)
            return render_template("home.html",dir_list=videos,page=page,
                           total_pages=math.ceil(total / per_page),year=year,month=month,day=day)
    else:
        return render_template("video.html",year=year,month=month,day=day,filename=filename)
    

@main.route('/videos/<int:year>/<int:month>/<int:day>/<path:filename>')
def serve_video_by_date(year, month, day, filename):
    abs_path = os.path.abspath(current_app.config['EXTERNAL_MEDIA_ROOT'])
    folder = os.path.join(
        abs_path,
        str(year),
        f"{month:02d}",
        f"{day:02d}"
    )
    print(folder)
    try:
        return send_from_directory(folder, filename)
    except FileNotFoundError:
        abort(404)

def get_dir_list(year,month,day):

        if year is None:
            path=current_app.config['EXTERNAL_MEDIA_ROOT']
        elif month is None:
            path=current_app.config['EXTERNAL_MEDIA_ROOT']+'/' +year
        elif day is None:
            path=current_app.config['EXTERNAL_MEDIA_ROOT']+'/'+year+"/"+month
        else: 
            path=current_app.config['EXTERNAL_MEDIA_ROOT']+'/'+year+"/"+month+"/"+day
        
        dir_list = os.listdir(path)
        if day != None:
            dir_list = sorted([x for x in dir_list if not(x.startswith('.')) and x.endswith('.mp4')])
        else:
            dir_list = sorted([x for x in dir_list if not(x.startswith('.'))])

        query = request.args.get("search", "").lower()
        
        if query:
            filtered_dirs = [d for d in dir_list if query in d.lower()]
        else:
            filtered_dirs = dir_list
    
        return filtered_dirs
        

def gen_frames(rtsp_url):
    
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    while True:
        success, frame = cap.read()
        if not success:
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@main.route('/camera_feed/<name>')

def camera_feed(name):
    from app.models import Camera
    camera = Camera.query.filter_by(name=name).first()
    if not camera:
        abort(404)
    return Response(gen_frames(camera.get_rtsp_url()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@main.route('/stream/<name>')

def stream(name):
    return render_template('stream.html',name=name)
