function getDataUrl(chart, query_string, absolute_url) {
  const query = encodeURIComponent(chart.query)
  return `${absolute_url}${chart.db}.json?sql=${query}&${query_string}&_shape=objects`
}

function enableChartTooltip(chart_slug) {
  let tooltip = document.querySelector(`#chart-tooltip-${chart_slug}`)
  tooltip.style.visibility = 'visible'
}

async function renderVegaChart(chart_slug, chart, query_string, absolute_url, full_height) {
  const dataUrl = getDataUrl(chart, query_string, absolute_url)
  const results = await fetch(dataUrl)
  const data = await results.json()

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
        values: data.rows,
        format: { 'type': 'json' }
      }
    ],
    signals: defaultSignals,
    ...chart.display
  };

  const el = document.querySelector(`#chart-${chart_slug}`)
  vegaEmbed(el, spec)

  if (data.truncated) {
    enableChartTooltip(chart_slug)
  }
}

async function renderVegaLiteChart(chart_slug, chart, query_string, absolute_url, full_height) {
  const dataUrl = getDataUrl(chart, query_string, absolute_url)
  const results = await fetch(dataUrl)
  const data = await results.json()

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
      values: data.rows,
      format: { 'type': 'json' }
    },
    ...chart.display
  };

  const el = document.querySelector(`#chart-${chart_slug}`)
  vegaEmbed(el, spec)

  if (data.truncated) {
    enableChartTooltip(chart_slug)
  }
}

async function renderMetricChart(chart_slug, chart, query_string, absolute_url, full_height) {
  const dataUrl = getDataUrl(chart, query_string, absolute_url)
  const results = await fetch(dataUrl)
  const data = await results.json()
  const metric = data.rows[0][chart.display.field]

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

  const el = document.querySelector(`#chart-${chart_slug}`)
  el.appendChild(wrapper)

  if (data.truncated) {
    enableChartTooltip(chart_slug)
  }
}

async function renderTableChart(chart_slug, chart, query_string, absolute_url, full_height) {
  const dataUrl = getDataUrl(chart, query_string, absolute_url)
  const results = await fetch(dataUrl)
  const data = await results.json()

  const thead = document.createElement('thead')
  const thead_tr = document.createElement('tr')
  Object.keys(data.rows[0]).forEach(col => {
    const thead_th = document.createElement('th')
    thead_th.innerHTML = col
    thead_tr.appendChild(thead_th)
  })
  thead.appendChild(thead_tr)

  const tbody = document.createElement('tbody')
  data.rows.forEach(row => {
    const tbody_tr = document.createElement('tr')
    Object.values(row).forEach(col => {
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

  const el = document.querySelector(`#chart-${chart_slug}`)
  el.appendChild(wrapper)

  if (data.truncated) {
    enableChartTooltip(chart_slug)
  }
}

async function renderMapChart(chart_slug, chart, query_string, absolute_url, full_height) {
  document.addEventListener("DOMContentLoaded", async () => {
    const dataUrl = getDataUrl(chart, query_string, absolute_url)
    const results = await fetch(dataUrl)
    const data = await results.json()

    const wrapper = document.createElement('div')
    wrapper.style.width = '100%'
    wrapper.style.height = '100%'
    wrapper.style.minHeight = '200px'

    const el = document.querySelector(`#chart-${chart_slug}`)
    el.appendChild(wrapper)

    const map = L.map(wrapper, { zoom: 12 })

    const tiles = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      detectRetina: true,
      attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>'
    })
    map.addLayer(tiles)

    const options = chart.display || {}
    const latitude_column = options.latitude_column || 'latitude'
    const longitude_column = options.longitude_column || 'longitude'
    const show_latlng_popup = options.show_latlng_popup || false

    data.rows.forEach(row => {
      const marker = L.marker([row[latitude_column], row[longitude_column]])
      const popup = Object.entries(row)
        .filter(e => (e[0] === latitude_column || e[0] === longitude_column) ? show_latlng_popup : true)
        .reduce((acc, e) => `${acc}<span style="font-weight:bold;">${e[0]}:</span> ${e[1]}<br>`, '')
      marker.bindPopup(popup)
      map.addLayer(marker)
    })

    const coords = data.rows.map(row => [row[latitude_column], row[longitude_column]])
    const bounds = new L.LatLngBounds(coords)
    map.fitBounds(bounds)

    if (data.truncated) {
      enableChartTooltip(chart_slug)
    }
  })
}

async function renderChart(chart_slug, chart, query_string, absolute_url, full_height = false) {
  renderers = new Map()
  renderers.set('vega', renderVegaChart)
  renderers.set('vega-lite', renderVegaLiteChart)
  renderers.set('metric', renderMetricChart)
  renderers.set('table', renderTableChart)
  renderers.set('map', renderMapChart)

  render = renderers.get(chart.library)
  if (render) {
    await render(chart_slug, chart, query_string, absolute_url, full_height)
  }
}

function toggleFullscreen() {
  const el = document.querySelector("section.content")
  if (document.fullscreenElement) {
    document.exitFullscreen()
  } else {
    el.requestFullscreen()
  }
}

function autorefresh(minutes) {
  const timeout = Math.round(minutes * 60 * 1000)
  window.setTimeout(function () { window.location.reload() }, timeout)
}

vega.setRandom(vega.randomLCG(0))
