# V3 failure-analysis handoff

## Full raw predictions (local)

benchmarks/preds_v3/adcdnet/ (512), adcdnet_1024/, adcdnet_2048/, trufor/. Each model/configuration covers 3,000 images. ADCD files are original-size NPY forgery probabilities. TruFor NPZ contains map, confidence and native detection score.

## Transfer bundle (created after validation)

v3_failure_analysis_maps.zip at the project root: 100 distinct receipt pairs, 200 images, 800 raw prediction files across four neural configurations, matching images and both masks, source and prepared annotations, a prediction manifest and SHA256 hashes. The selection spans all five compression variants (20 pairs each). The ZIP stays local until uploaded; it is too large for ordinary Git files.

## Team-accessible visualization alternative

The runner uses --vis 200 --vis-authentic 200. Panels contain original | GT | probability heatmap. IDs are paired across labels. Complete local views are in results_v3_realistic/{official_mask,diff_mask}/vis/{ext_adcdnet,ext_adcdnet_1024,ext_adcdnet_2048,ext_trufor}. Baseline views are also generated.

After validation, the pipeline publishes 100 distinct authentic/tampered receipt pairs per neural configuration to:
https://github.com/dogtoro/six_seven/tree/dam/six_seven/benchmarks/results_v3_realistic/official_mask/vis

Publication is confirmed by v3_published.json with a verified remote commit. Before that file exists, the URL is a planned handoff path. Raw arrays stay in the local ZIP; the shared GitHub PNGs are probability heatmap panels, satisfying option (b). The metadata contains original/forged text, forgery method, source boxes and JPEG settings where provided by the generator.
