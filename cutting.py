import onnx
onnx.utils.extract_model('yolov5m_bpla.onnx',
                         'yolov5m_bpla_cutted.onnx',
                         ['images'],
                         ['conv2d_57',
                          'conv2d_58',
                          'conv2d_59'] )