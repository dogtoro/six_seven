# Validated OCR acceleration

V3 preparation uses the same PP-OCRv5_server_det weights, thresholds and mask construction on GPU. Paddle GPU 3.3.1 (CUDA 12.6) and cuDNN 9.9.0.52 are installed under .ocr_gpu_runtime; the primary conda environment is unchanged. Ten examples spanning both labels, four forgery methods and two cached templates produced masks byte-identical to the CPU cache. Mean warmed-up detection time is approximately 0.095 seconds versus measured CPU examples of 10-16 seconds. This is OCR detector timing, not an estimate for the full benchmark.

The CLI accepts --ocr-device gpu:0 --paddle-runtime <absolute runtime directory> --cpu-threads 1. GPU library paths are changed only inside the preparation subprocess; ADCD/TruFor use the existing Torch installation. Existing OCR cache is reused. The runtime folder and its binary dependencies are not committed to Git.

To reproduce the local GPU runtime from the project directory, using the same Python version/architecture:

    python -m pip install --target .ocr_gpu_runtime --no-deps paddlepaddle-gpu==3.3.1 --index-url https://www.paddlepaddle.org.cn/packages/stable/cu126/
    python -m pip install --target .ocr_gpu_runtime --upgrade --no-deps nvidia-cudnn-cu12==9.9.0.52

The base environment must already contain the documented PaddleOCR dependencies; these commands only add the isolated GPU runtime. See https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/module_usage/text_detection.en.md for device parameters. Validation: ocr_acceleration_validation.json.
