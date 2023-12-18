from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import time
import sys
import os
import urllib.request
import uvicorn
import threading



from predict import load_model,predict 

class MatriceModel:

    def __init__(self, action_id, port):
        self.action_id = None
        self.model_path = ''
        self.model = None
        self.last_no_inference_time = -1
        self.shutdown_on_idle_threshold = 3000
        self.app = FastAPI()
        self.ip = self.get_ip()
        self.run_shutdown_checker()
        
        @self.app.post("/inference/")
        async def serve_inference(image: UploadFile = File(...)):
            image_data = await image.read()
            results, ok = self.inference(image_data)

            if ok:
                return JSONResponse(content=jsonable_encoder({"status": 1, "message": "Request success", "result": results}))
            else:
                return JSONResponse(content=jsonable_encoder({"status": 0, "message": "Some error occurred"}), status_code=500)


    def run_api(self, host="0.0.0.0", port=80):
        uvicorn.run(self.app, host=host, port=port)


    def get_ip(self):
        external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
        print(f"YOUR PUBLIC IP IS: {external_ip}")
        return external_ip


    def inference(self, image):
        if self.model_path == '':
            self.model_path = self.download_model()

        if self.model is None:
            self.model = load_model(self.model_path)

        self.last_no_inference_time = -1

        try:
            results = predict(self.model, image)
            print("Successfully ran inference")
            return results, True
        except Exception as e:
            print(f"ERROR: {e}")
            return None, False


    def trigger_shutdown_if_needed(self):
        if self.last_no_inference_time == -1:
            self.last_no_inference_time = time.time()
        else:
            elapsed_time = time.time() - self.last_no_inference_time
            if elapsed_time > int(self.shutdown_on_idle_threshold):
                try:
                    print('Shutting down due to idle time exceeding the threshold.')
                    os.system('shutdown now')
                except:
                    print("Unable to process shutdown")
                sys.exit(1)
            else:
                print('Time since last inference:', elapsed_time)
                print('Time left to shutdown:', int(self.shutdown_on_idle_threshold) - elapsed_time)


    def shutdown_checker(self):
        while True:
            self.trigger_shutdown_if_needed()
            time.sleep(60)


    def run_shutdown_checker(self):
        t1 = threading.Thread(target=self.shutdown_checker, args=())
        t1.setDaemon(True)
        t1.start()


    def download_model(self):
        return "test"

    def update_deployment_info(self):
        ip = self.ip
        port = self.port

x=MatriceModel("",8000)
x.run_api()
