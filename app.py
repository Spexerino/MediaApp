import os
import cv2
from flask import Flask, render_template, request, send_from_directory, abort, Response

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass


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

    # a simple page that says hello
    @app.route('/',defaults={'year':None, 'month':None, 'day':None,'filename':None})
    @app.route('/<year>',defaults={'month':None, 'day':None,'filename':None})
    @app.route('/<year>/<month>',defaults={'day':None,'filename':None})
    @app.route('/<year>/<month>/<day>',defaults={'filename':None})
    @app.route('/<year>/<month>/<day>/<filename>')
    def home(year,month,day,filename):
        if filename == None:
            dir_list = get_dir_list(year,month,day)
            return render_template("home.html",dir_list=dir_list,year=year,month=month,day=day)
        else:
            return render_template("video.html",year=year,month=month,day=day,filename=filename)
    
    EXTERNAL_MEDIA_ROOT = os.path.abspath("/Volumes/video")

    @app.route('/videos/<int:year>/<int:month>/<int:day>/<path:filename>')
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

    return app