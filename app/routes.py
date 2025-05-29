from flask import Blueprint, render_template, send_from_directory, abort, request
import os

main = Blueprint('main', __name__)

# a simple page that says hello
@main.route('/',defaults={'year':None, 'month':None, 'day':None,'filename':None})
@main.route('/<year>',defaults={'month':None, 'day':None,'filename':None})
@main.route('/<year>/<month>',defaults={'day':None,'filename':None})
@main.route('/<year>/<month>/<day>',defaults={'filename':None})
@main.route('/<year>/<month>/<day>/<filename>')
def home(year,month,day,filename):
    if filename == None:
        dir_list = get_dir_list(year,month,day)
        return render_template("home.html",dir_list=dir_list,year=year,month=month,day=day)
    else:
        return render_template("video.html",year=year,month=month,day=day,filename=filename)

EXTERNAL_MEDIA_ROOT = os.path.abspath("/Volumes/video")

@main.route('/videos/<int:year>/<int:month>/<int:day>/<path:filename>')
def serve_video_by_date(year, month, day, filename):
    folder = os.path.join(
        EXTERNAL_MEDIA_ROOT,
        str(year),
        f"{month:02d}",
        f"{day:02d}"
    )
    try:
        return send_from_directory(folder, filename)
    except FileNotFoundError:
        abort(404)

def get_dir_list(year,month,day):

        if year is None:
            path="/Volumes/video/"
        elif month is None:
            path="/Volumes/video/"+year
        elif day is None:
            path="/Volumes/video/"+year+"/"+month
        else: 
            path="/Volumes/video/"+year+"/"+month+"/"+day
        
        dir_list = os.listdir(path)
        if day != None:
            dir_list = [x for x in dir_list if not(x.startswith('.')) and x.endswith('.mp4')]
        else:
            dir_list = [x for x in dir_list if not(x.startswith('.'))]

        query = request.args.get("search", "").lower()
        
        if query:
            filtered_dirs = [d for d in dir_list if query in d.lower()]
        else:
            filtered_dirs = dir_list

        print(filtered_dirs)
    
        return filtered_dirs
