-- 0002_seed_reference_data.sql
-- Idempotent seed data for the 12 dissertation specimens and 5 standard mathematical fractals.

INSERT INTO specimens (
    id, name, category, fractal_dimension, r_squared, complexity_class,
    interpretation, notes, display_order, image_url, box_sizes, box_counts
) VALUES
(
    'spc_guava', 'Guava', 'leaf',
    1.8110, 0.9976, 'High',
    'High complexity — dense leaf structure with irregular venation',
    'Fresh guava leaf specimen, analyzed using full-mask mode with Otsu threshold',
    1, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_lamiaceae', 'Lamiaceae', 'leaf',
    1.9493, 0.9999, 'Near space-filling',
    'Highest leaf complexity in the dataset — extensive branching and surface texture',
    'Lamiaceae family specimen showing near space-filling behavior',
    2, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_mango', 'Mango', 'leaf',
    1.7599, 0.9953, 'Complex',
    'Complex leaf structure with moderate irregularity and clear venation',
    NULL,
    3, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_monoon', 'Monoon Longifolium', 'leaf',
    1.7505, 0.9961, 'Complex',
    'Complex elongated leaf pattern with smooth boundary but textured interior',
    NULL,
    4, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_peepal', 'Peepal', 'leaf',
    1.8043, 0.9977, 'High',
    'High complexity — broad leaf with fine venation network',
    NULL,
    5, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_maple', 'Maple', 'leaf',
    1.5061, 0.9815, 'Complex',
    'Lower score due to noisy background in original image — demonstrates preprocessing sensitivity',
    'R² is noticeably lower due to background artifacts',
    6, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_akondo', 'Akondo', 'leaf',
    1.8727, 0.9988, 'High',
    'High complexity — densely textured leaf surface with irregular edge',
    NULL,
    7, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_coast1', 'Coastline 1', 'coastline',
    1.7613, 0.9991, 'Complex',
    'Complex coastline with moderate irregularity and some smooth sections',
    NULL,
    8, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_coast2', 'Coastline 2', 'coastline',
    1.9141, 0.9999, 'Highly irregular',
    'Highly irregular coastline boundary with deep indentations',
    NULL,
    9, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_coast3', 'Coastline 3', 'coastline',
    1.9626, 1.0000, 'Near space-filling',
    'Highest coastline complexity — near space-filling boundary with maximum irregularity',
    'R² = 1.0000 indicates near-perfect linear fit in log-log space',
    10, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_coast4', 'Coastline 4', 'coastline',
    1.7108, 0.9996, 'Complex',
    'Lower coastline complexity — smoother boundary sections reduce overall D',
    NULL,
    11, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_coast5', 'Coastline 5', 'coastline',
    1.9531, 1.0000, 'Highly irregular',
    'Highly irregular coastline with complex indentations and fjord-like structures',
    NULL,
    12, '', '{4,8,16,32,64,128,256}', '{}'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO standard_fractals (
    id, name, theoretical_dimension, max_iterations, description, formula, display_order
) VALUES
(
    'cantor_set', 'Cantor Set',
    0.6309, 8,
    'Created by repeatedly removing the middle third of line segments',
    'D = log(2) / log(3) ≈ 0.6309',
    1
),
(
    'koch_curve', 'Koch Curve',
    1.2619, 7,
    'Each line segment is replaced by four segments of one-third length',
    'D = log(4) / log(3) ≈ 1.2619',
    2
),
(
    'koch_snowflake', 'Koch Snowflake',
    1.2619, 7,
    'Three Koch curves forming a closed snowflake boundary',
    'D = log(4) / log(3) ≈ 1.2619',
    3
),
(
    'sierpinski_triangle', 'Sierpiński Triangle',
    1.5850, 8,
    'Equilateral triangle subdivided recursively, removing central triangle',
    'D = log(3) / log(2) ≈ 1.5850',
    4
),
(
    'sierpinski_carpet', 'Sierpiński Carpet',
    1.8928, 6,
    'Square subdivided into 9 equal squares, removing center square recursively',
    'D = log(8) / log(3) ≈ 1.8928',
    5
)
ON CONFLICT (id) DO NOTHING;
