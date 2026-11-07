# V3 resolution ablation

| mask          |   max_size | label   |    n |   images_downscaled |   pixel_F1_at_0_5 |   pixel_IoU_at_0_5 |   det_AUC |   mean_image_max_probability |   mean_pixel_probability |   mean_predicted_positive_fraction |   fraction_images_max_ge_0_5 |
|:--------------|-----------:|:--------|-----:|--------------------:|------------------:|-------------------:|----------:|-----------------------------:|-------------------------:|-----------------------------------:|-----------------------------:|
| official_mask |        512 | all     | 3000 |                3000 |          0.026527 |           0.016941 |  0.561884 |                     0.451118 |                 0.090233 |                           9.7e-05  |                     0.193667 |
| official_mask |       1024 | all     | 3000 |                 448 |          0.137346 |           0.099967 |  0.683364 |                     0.523045 |                 0.083486 |                           0.000543 |                     0.437667 |
| official_mask |       2048 | all     | 3000 |                   0 |          0.150175 |           0.109482 |  0.700248 |                     0.518446 |                 0.082838 |                           0.00048  |                     0.426333 |

The earlier approximately 0.44 statistic is the mean of each image's maximum probability. Mean pixel probability and predicted-positive fraction are reported separately. All caps use the same 3,000 V3 image IDs, weights, OCR masks, inference precision and evaluation thresholds. max-size is a downscaling cap; it does not upscale inputs. images_downscaled identifies how many inputs each cap affects.

A probability increase alone does not establish better localization: compare pixel F1/IoU and detection AUC alongside the probabilities. These results quantify resolution sensitivity on V3; they do not prove a single cause of the original V2 behavior or establish calibration on an independent validation set. Class-specific rows are in the CSV.
