function renderVegaChart(chart, json_data_url, dom_id) {
  var vlSpec = {
    $schema: 'https://vega.github.io/schema/vega-lite/v5.json',
    title: chart.title,
    width: 'container',
    view: {stroke: null},
    config: {
      background: '#00000000',
      arc: {
        innerRadius: 50
      },
      line: {
        point: true
      }
    },
    data: {
      url: json_data_url,
      format: {'type': 'json'}
    },
    ...chart.display
  };
  vegaEmbed(dom_id, vlSpec);
}
