// Run in https://code.earthengine.google.com after importing a same-year ward
// boundary FeatureCollection as `wards`. Set `ward_id` to its matching tax-roll key.
// Exports one feature row per ward: use it instead of a fabricated buildings.csv.
var wardId = 'ward_id';
var col = ee.ImageCollection('GOOGLE/Research/open-buildings-temporal/v1');
function yearImage(year) {
  return col.filterDate(year + '-01-01', (year + 1) + '-01-01').mosaic();
}
// For FY2017-18, average calendar 2017 and 2018 rather than use a single unstable height layer.
var a = yearImage(2017), b = yearImage(2018);
var height = a.select('building_height').add(b.select('building_height')).divide(2).rename('building_height');
var count = a.select('building_fractional_count').add(b.select('building_fractional_count')).divide(2).rename('building_count');
// Approximate volume: 4m-pixel area × fractional count × average height.
var volume = count.multiply(ee.Image.pixelArea()).multiply(height).rename('built_volume_m3');
var image = volume.addBands(count);
var stats = image.reduceRegions({collection: wards, reducer: ee.Reducer.sum(), scale: 4});
var out = stats.map(function(f) { return f.set({
  ward_id: f.get(wardId), built_volume_m3: f.get('built_volume_m3_sum'),
  building_count: f.get('building_count_sum'),
  // 16 = pixel area at the dataset's 4 m effective resolution.
  mean_height_m: ee.Number(f.get('built_volume_m3_sum')).divide(ee.Number(f.get('building_count_sum')).multiply(16)),
  median_footprint_m2: 0, recent_new_building_share: 0
}); });
Export.table.toDrive({collection: out, description: 'pune_2017_18_ward_features', fileFormat: 'CSV', selectors:['ward_id','built_volume_m3','building_count','mean_height_m','median_footprint_m2','recent_new_building_share']});
