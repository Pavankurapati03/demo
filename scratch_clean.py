import re

# 1. Update sales_forecasting.html
with open('portal/templates/sales_forecasting.html', 'r', encoding='utf-8') as f:
    sf_content = f.read()

# Remove view-overview block
sf_content = re.sub(r'<!--\s*===+\s*VIEW 0: EXECUTIVE / FORECAST OVERVIEW.*?</div>\s*<!--\s*/#view-overview\s*-->', '', sf_content, flags=re.DOTALL)
# Make view-target1 active
sf_content = sf_content.replace('id="view-target1" class="sales-view" style="display:none;"', 'id="view-target1" class="sales-view active"')
sf_content = sf_content.replace('id="view-target1" class="sales-view"', 'id="view-target1" class="sales-view active"')

# Update JS in sales_forecasting.html
old_sf_js = """    function switchSalesView(viewId, btn) {
      document.querySelectorAll('.dash-tab-pill').forEach(b => b.classList.remove('active'));
      if (btn) {
        btn.classList.add('active');
      } else {
        const tabMap = { 'overview': 0, 'target1': 1, 'target2': 2 };
        const pills = document.querySelectorAll('.dash-tab-pill');
        if (tabMap[viewId] !== undefined && pills[tabMap[viewId]]) {
          pills[tabMap[viewId]].classList.add('active');
        }
      }
      document.querySelectorAll('.sales-view').forEach(v => v.style.display = 'none');
      const targetView = document.getElementById('view-' + viewId);
      if (targetView) targetView.style.display = 'block';
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Direct deep-linking support via query parameters (?target=target1 or ?target=target2)
    document.addEventListener('DOMContentLoaded', () => {
      const urlParams = new URLSearchParams(window.location.search);
      const targetParam = urlParams.get('target');
      if (targetParam === 'target1') {
        switchSalesView('target1', document.querySelectorAll('.dash-tab-pill')[1]);
      } else if (targetParam === 'target2') {
        switchSalesView('target2', document.querySelectorAll('.dash-tab-pill')[2]);
      }
    });"""

new_sf_js = """    function switchSalesView(viewId) {
      document.querySelectorAll('.sales-view').forEach(v => v.style.display = 'none');
      const targetView = document.getElementById('view-' + viewId);
      if (targetView) targetView.style.display = 'block';
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Direct deep-linking support via query parameters (?target=target1 or ?target=target2)
    document.addEventListener('DOMContentLoaded', () => {
      const urlParams = new URLSearchParams(window.location.search);
      const targetParam = urlParams.get('target');
      if (targetParam === 'target2') {
        switchSalesView('target2');
      } else {
        switchSalesView('target1');
      }
    });"""

sf_content = sf_content.replace(old_sf_js, new_sf_js)

with open('portal/templates/sales_forecasting.html', 'w', encoding='utf-8') as f:
    f.write(sf_content)

print("sales_forecasting.html updated successfully")
