import os
import shutil
import tempfile
from django.conf import settings
from django.core.files import File
from ultralytics import YOLO

model=YOLO(os.path.join(settings.BASE_DIR,'train_model','best.pt'))

def analyze_clinical_image(image):
    temp_input=None; temp_results=None
    try:
        suffix=os.path.splitext(image.imagen.name)[1] or '.jpg'
        with tempfile.NamedTemporaryFile(delete=False,suffix=suffix) as temporary:
            image.imagen.open('rb')
            try: shutil.copyfileobj(image.imagen,temporary)
            finally: image.imagen.close()
            temp_input=temporary.name
        temp_results=tempfile.mkdtemp(prefix='yolo_results_')
        results=model.predict(temp_input,save=True,project=temp_results,name='pred')
        save_dir=str(results[0].save_dir)
        supported_outputs=('.jpg','.jpeg','.png','.webp','.gif','.bmp','.tif','.tiff')
        output=next((os.path.join(save_dir,name) for name in os.listdir(save_dir) if name.lower().endswith(supported_outputs)),None)
        if not output or not os.path.exists(output): raise FileNotFoundError(f'No se encontró la imagen procesada en {save_dir}')
        with open(output,'rb') as result_file: image.resultados.save(os.path.basename(output),File(result_file),save=True)
        return [{'clase':model.names[int(cls)],'confianza':float(results[0].boxes.conf[index]),'coordenadas':results[0].boxes.xyxy[index].tolist()} for index,cls in enumerate(results[0].boxes.cls)]
    finally:
        if temp_input and os.path.exists(temp_input): os.remove(temp_input)
        if temp_results and os.path.exists(temp_results): shutil.rmtree(temp_results,ignore_errors=True)
