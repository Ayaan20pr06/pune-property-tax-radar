// Pune-only building proxy extraction. In Earth Engine, import
// data/raw/pune_wards/GeoData/pune-admin-wards.geojson as `wards`.
// The GeoJSON's `name` property is retained; ward_id is parsed from it.
var source = ee.ImageCollection('GOOGLE/Research/open-buildings-temporal/v1');
function mosaic(year) {
  return source.filterDate(year + '-01-01', (year + 1) + '-01-01').mosaic();
}
var left = mosaic(2018);
var right = mosaic(2019);
var presence = left.select('building_presence').add(right.select('building_presence')).divide(2);
var height = left.select('building_height').add(right.select('building_height')).divide(2);
var builtArea = presence.multiply(ee.Image.pixelArea()).rename('built_area_m2');
var volume = presence.multiply(height).multiply(ee.Image.pixelArea()).rename('volume_m3');
var measures = builtArea.addBands(volume);
var result = measures.reduceRegions({
  collection: wards,
  reducer: ee.Reducer.sum(),
  scale: 4,
  tileScale: 16
}).map(function(feature) {
  var name = ee.String(feature.get('name'));
  return feature.set({
    ward_id: name.slice(11, 13),
    ward_name: name,
    built_area_m2: feature.get('built_area_m2'),
    volume_m3: feature.get('volume_m3')
  });
});
Export.table.toDrive({
  collection: result,
  description: 'pune_2018_2019_ward_buildings',
  fileFormat: 'CSV',
  selectors: ['ward_id', 'ward_name', 'built_area_m2', 'volume_m3']
});
