function renderVegaChart(el, chart, query_string, height_style = undefined) {
  const query = encodeURIComponent(chart.query)
  const spec = {
    $schema: 'https://vega.github.io/schema/vega-lite/v5.json',
    description: chart.title,
    width: 'container',
    height: height_style,
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
      url: `/${chart.db}.csv?sql=${query}&${query_string}`,
      format: {'type': 'csv'}
    },
    ...chart.display
  };

  vegaEmbed(el, spec);
}

async function renderMetricChart(el, chart, query_string) {
  const query = encodeURIComponent(chart.query)
  const results = await fetch(`/${chart.db}.json?sql=${query}&${query_string}&_shape=array`)
  const data = await results.json()
  const metric = data[0][chart.display.field]

  const prefix = chart.display.prefix || ''
  const suffix = chart.display.suffix || ''
  const text = `${prefix}${metric}${suffix}`

  const p = document.createElement('p')
  p.innerHTML = text
  p.style.fontSize = '2.2rem';
  p.style.fontWeight = '900';

  const wrapper = document.createElement('div')
  wrapper.appendChild(p)
  wrapper.style.width = '100%'
  wrapper.style.height = '100%'
  wrapper.style.display = 'flex'
  wrapper.style.flexDirection = 'column'
  wrapper.style.justifyContent = 'center'
  wrapper.style.alignItems = 'center'
  wrapper.style.overflow = 'hidden'
  wrapper.style.whiteSpace = 'nowrap'
  wrapper.style.textOverflow = 'ellipsis'

  document.querySelector(el).appendChild(wrapper)
}
