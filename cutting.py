import onnx
onnx.utils.extract_model('yolov5s.onnx',
                         'yolov5s_surgeon_v2.onnx',
                         ['images'],
                         ['conv2d_57',
                          'conv2d_58',
                          'conv2d_59'] )