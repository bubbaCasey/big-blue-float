// Shared helpers for the Big Blue float pages.
// Pages read data/float.json, which a GitHub Action refreshes every 6 hours.

async function loadFloatData() {
  const res = await fetch('data/float.json', { cache: 'no-store' });
  if (!res.ok) throw new Error('Could not load data/float.json (HTTP ' + res.status + ')');
  return res.json();
}

function fmtLatLon(lat, lon) {
  const ns = lat < 0 ? 'S' : 'N';
  const ew = lon < 0 ? 'W' : 'E';
  return Math.abs(lat).toFixed(2) + '°' + ns + ', ' + Math.abs(lon).toFixed(2) + '°' + ew;
}

function fmtDate(iso) {
  return new Date(iso).toLocaleString('en-US', {
    timeZone: 'UTC', dateStyle: 'medium', timeStyle: 'short'
  }) + ' UTC';
}

// Marks the current page in the navigation bar.
function setActiveNav() {
  const here = location.pathname.split('/').pop() || 'tracking.html';
  document.querySelectorAll('nav a').forEach(a => {
    if (a.getAttribute('href') === here) a.classList.add('active');
  });
}
document.addEventListener('DOMContentLoaded', setActiveNav);
