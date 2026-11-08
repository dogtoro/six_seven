# ask_dam (1).md acceptance — V3-only scope

The user cancelled old V1/V2 runs and requested the feedback on V3 instead: 300 pairs, 3,000 images/configuration. Literal V2 paths and 5,000-image counts no longer apply. Initial results were verified and published in dam commit f2be654.

| Task | Verified V3 deliverable |
|---|---|
| T1 | ExternalMaps.predict returns (map, native_score); --score native, map-max fallback, score_source column; all 3,000 TruFor rows use native scores; per-compression AUC in both summaries. |
| T2 | ELA/random detection metrics N/A in summarize(); pixel metrics retained. |
| T3 | All 3,000 predictions at each ADCD cap (512/1024/2048), both GT evaluations, resolution_comparison.csv and RESOLUTION_REPORT.md. The report separates image-max means from pixel means. |
| T4 | Option b: --vis 200 --vis-authentic 200 with paired IDs. At least 100 distinct authentic/tampered receipt pairs/configuration are shared on dam; see PREDS_LOCATION.md. Full raw-map upload is cancelled and unnecessary for this accepted alternative. |
| T5 | TextShield missing dependencies/checkpoint documented in benchmarks/README.md. CAFTB search links are documented; a public reproduction exists, so the blanket no-public-weights claim was withdrawn. No original-author checkpoint was verified or CAFTB performance fabricated. |
| T6 | Root README/handoff updated; markdown force-added to Git. |
| T7 | V3 generated, audited and evaluated with native TruFor scoring; both results_v3_realistic mask folders published. All three ADCD caps are provided rather than only a chosen cap. |

The team can perform false-positive/localization analysis with the published paired panels and full quantitative tables. Higher-resolution V3 results do not prove the sole cause of earlier V2 failure. Optional grayscale testing and TextShield execution were not performed.
