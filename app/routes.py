from flask import Blueprint, render_template, send_from_directory, abort, request, Response, current_app
import os
import cv2
import math
from app.models import Camera, Folder, File, db
from pathlib import Path
from sqlalchemy import and_

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
    folder_path = os.path.join(abs_path, str(year), f"{month:02d}", f"{day:02d}")

    # Optional DB verification
    folder = Folder.query.filter_by(year=year, month=month, day=day).first()
    if not folder:
        abort(404)

    file = File.query.filter_by(folder_id=folder.id, filename=filename).first()
    if not file:
        abort(404)

    try:
        return send_from_directory(folder_path, filename)
    except FileNotFoundError:
        abort(404)


def get_dir_list(year, month, day):
    query = request.args.get("search", "").lower()

    if year is None:
        # Return list of years
        years = db.session.query(Folder.year).distinct().order_by(Folder.year).all()
        items = [str(y[0]) for y in years]

    elif month is None:
        # Return list of months in that year
        months = db.session.query(Folder.month).filter_by(year=int(year)).distinct().order_by(Folder.month).all()
        items = [f"{m[0]:02d}" for m in months]

    elif day is None:
        # Return list of days in that year/month
        days = db.session.query(Folder.day).filter_by(
            year=int(year), month=int(month)
        ).distinct().order_by(Folder.day).all()
        items = [f"{d[0]:02d}" for d in days]

    else:
        # Return filenames in the day folder
        folder = Folder.query.filter_by(
            year=int(year), month=int(month), day=int(day)
        ).first()

        if not folder:
            return []

        files_query = File.query.filter(File.folder_id == folder.id,~File.filename.like('%.jpg')).order_by(File.filename)

        if query:
            files_query = files_query.filter(File.filename.ilike(f"%{query}%"))

        items = [f.filename for f in files_query.all()]

    # Apply search to folders/years/months/days as well
    if query and day is None:
        items = [i for i in items if query in i.lower()]

    return items

        

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
