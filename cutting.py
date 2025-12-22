import onnx
onnx.utils.extract_model('lamp.onnx',
                         'lamp_cutted_5s.onnx',
                         ['images'],
                         ['conv2d_57',
                          'conv2d_58',
                          'conv2d_59'] )