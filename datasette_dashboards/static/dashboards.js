function renderVegaChart(el, chart, query_string, full_height) {
  const query = encodeURIComponent(chart.query)
  let defaultSignals = [
    {
      'name': 'width',
      'init': 'isFinite(containerSize()[0]) ? containerSize()[0] : 200',
      'on': [
        {
          'update': 'isFinite(containerSize()[0]) ? containerSize()[0] : 200',
          'events': 'window:resize'
        }
      ]
    }
  ]
  if (full_height) {
    defaultSignals.push({
      'name': 'height',
      'init': 'isFinite(containerSize()[1]) ? containerSize()[1] : 200',
      'on': [
        {
          'update': 'isFinite(containerSize()[1]) ? containerSize()[1] : 200',
          'events': 'window:resize'
        }
      ]
    })
  }

  const spec = {
    $schema: 'https://vega.github.io/schema/vega/v5.json',
    description: chart.title,
    autosize: { 'type': 'fit', 'resize': true },
    data: [
      {
        name: 'table',
        url: `/${chart.db}.csv?sql=${query}&${query_string}`,
        format: { 'type': 'csv', 'parse': 'auto' }
      }
    ],
    signals: defaultSignals,
    ...chart.display
  };

  vegaEmbed(el, spec);
}

function renderVegaLiteChart(el, chart, query_string, full_height) {
  const query = encodeURIComponent(chart.query)
  const spec = {
    $schema: 'https://vega.github.io/schema/vega-lite/v5.json',
    description: chart.title,
    width: 'container',
    height: full_height ? 'container' : undefined,
    view: { stroke: null },
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
      format: { 'type': 'csv' }
    },
    ...chart.display
  };

  vegaEmbed(el, spec);
}

async function renderMetricChart(el, chart, query_string, full_height) {
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

async function renderTableChart(el, chart, query_string, full_height) {
  const query = encodeURIComponent(chart.query)
  const results = await fetch(`/${chart.db}.json?sql=${query}&${query_string}`)
  const data = await results.json()

  const thead = document.createElement('thead')
  const thead_tr = document.createElement('tr')
  data.columns.forEach(col => {
    const thead_th = document.createElement('th')
    thead_th.innerHTML = col
    thead_tr.appendChild(thead_th)
  })
  thead.appendChild(thead_tr)

  const tbody = document.createElement('tbody')
  data.rows.forEach(row => {
    const tbody_tr = document.createElement('tr')
    row.forEach(col => {
      const tbody_td = document.createElement('td')
      tbody_td.innerHTML = col
      tbody_tr.appendChild(tbody_td)
    })
    tbody.appendChild(tbody_tr)
  })

  const table = document.createElement('table')
  table.appendChild(thead)
  table.appendChild(tbody)

  const wrapper = document.createElement('div')
  wrapper.style.width = '100%'
  wrapper.style.height = '100%'
  wrapper.style.overflow = 'auto'
  wrapper.appendChild(table)

  document.querySelector(el).appendChild(wrapper)
}

async function renderChart(el, chart, query_string, full_height = false) {
  renderers = new Map()
  renderers.set('vega', renderVegaChart)
  renderers.set('vega-lite', renderVegaLiteChart)
  renderers.set('metric', renderMetricChart)
  renderers.set('table', renderTableChart)

  render = renderers.get(chart.library)
  if (render) {
    await render(el, chart, query_string, full_height)
  }
}
