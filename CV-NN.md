#  MAIX4 YOLO  dataset->inference

## Dataset

#### Установка CVAT
Адекватно работает свежий релиз CVAT (dev)
https://github.com/cvat-ai/cvat

Если Ubuntu 22, то надо установить новый docker-compose. Для этого:
```shell
sudo apt remove docker-compose docker-compose-v
sudo apt install -y ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
docker --version
docker compose version
```

Создание userа:
docker exec -it cvat_server bash -ic 'python3 ~/manage.py createsuperuser'

------------

#### Процесс


**1. Нарезка видео**

```
ffmpeg -i input.mp4 -vf fps=5 frames/frame_%06d.jpg
```

После нарезки импортируем в CVAT.

**2. Рамзетка датасета**

- В CVAT в проекте создаем таски с метками Train, Validation и можно Test. 
- После разметки экспорт в формате YOLO 1.1 

**3. Конвертация датасета в подходящий формат**

- Клонируем https://github.com/ankhafizov/CVAT2YOLO
- Ставим requirements.
```
python main_cvat2yolo.py --cvat test --mode manual --train_folder obj_Train_data --val_folder obj_Validation_data  --test_folder obj_Test_data --img_format jpg --output_folder my_dataset_yolov5
```

**4. Обучение**
```
git clone https://github.com/carrotFoxx/yolov5_AX650
```
- Добавляем конфиг датасета на примере data/lamp.yaml

```
python3 train.py --img 640 --batch 16 --epochs 1 --data lamp.yaml --weights yolov5s.pt --device cpu
```
- Экспорт
```
python3 export.py --weights lamp.pt --imgsz 640 --device=cpu --verbose --opset 11 --include 'onnx' --simplify
```
- Обрезаем сеть для квантования: редактируем cutting.py указав имя экспортированной сети 

По умолчанию указаны выходные векторы до объединения yolov5. На рис. ниже указан 
```
python3 cutting.py
```

**5. Квантование**

1. Подготваливаем инструменты согласно инструкции: https://pulsar2-docs.readthedocs.io/en/latest/user_guides_quick/quick_start_prepare.html
2. В каталог data/config кладем файл конфига:
```json
{
  "model_type": "ONNX",
  "npu_mode": "NPU1",
  "quant": {
    "input_configs": [
      {
        "tensor_name": "images",
        "calibration_dataset": "./dataset/your_dataset.tar",
        "calibration_size": -1,
        "calibration_mean": [0, 0, 0],
        "calibration_std": [255.0, 255.0, 255.0]
      }
    ],
    "calibration_method": "MinMax",
    "precision_analysis": true,
    "precision_analysis_method":"EndToEnd"
  },
  "input_processors": [
    {
      "tensor_name": "images",
      "tensor_format": "RGB",
      "src_format": "BGR",
      "src_dtype": "U8",
      "src_layout": "NHWC"
    }
  ],
  "output_processors": [
    {
      "tensor_name": "conv2d_57",
      "dst_perm": [0, 2, 3, 1]
    },    {
      "tensor_name": "conv2d_58",
      "dst_perm": [0, 2, 3, 1]
    },    {
      "tensor_name": "conv2d_59",
      "dst_perm": [0, 2, 3, 1]
    }
  ],
  "compiler": {
    "check": 2
  }
}
```
"calibration_dataset": "./dataset/your_dataset.tar" - редактируем под свой
3. В каталог data/dataset кладем архив tar с датасетом, на котором учили сеть
4. Заходим в контейнер 
```
sudo docker run -it --net host --rm -v $PWD:/data pulsar2:${version}
```
и запускаем квантование командой: 
```
pulsar2 build  --target_hardware AX650 --input model/your_model.onnx --output_dir output --config config/yolov5_config.json
```
5. В каталоге output будет находиться скомпилированная модель под инференс.