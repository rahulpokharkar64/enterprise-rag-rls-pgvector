# Chunking comparison (same 30 documents)

Parameters: size=800 chars, overlap=100 (fixed/recursive), min chunk=120, semantic percentile=85, semantic cap=1200.

| strategy   |   total_chunks |   avg |   min |   median |   max |   stdev |   overlap_avg |   heading_preserved_% |   starts_at_heading_% |   clean_end_% |   mid_word_cut_% |   split_code_fence_% |   tiny_chunks_% |   seconds |
|------------|----------------|-------|-------|----------|-------|---------|---------------|-----------------------|-----------------------|---------------|------------------|----------------------|-----------------|-----------|
| fixed      |            807 |   786 |   115 |      800 |   800 |      81 |            99 |                  96.3 |                   4.3 |           7.2 |             85.4 |                 11   |             0.2 |       1   |
| recursive  |           1035 |   547 |     3 |      600 |   800 |     205 |            11 |                  97.1 |                  44   |          87.2 |              0.5 |                  2.1 |             3.5 |       0.3 |
| markdown   |            933 |   588 |    17 |      713 |   802 |     223 |           110 |                 100   |                  50.1 |          69.3 |             16.5 |                  7.3 |             3   |       0.1 |
| semantic   |            807 |   686 |    87 |      634 |  5889 |     454 |             0 |                  61.8 |                  20.2 |          79.1 |             28.7 |                  4.7 |             0.6 |     327.7 |
