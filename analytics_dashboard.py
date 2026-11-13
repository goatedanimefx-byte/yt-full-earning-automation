#!/usr/bin/env python3
"""
Analytics Dashboard - Visual charts of performance
Generates HTML dashboard with charts
"""

import json
from pathlib import Path
from datetime import datetime
from memory_core import get_memory

OUTPUT_DIR = Path(__file__).parent / "outputs" / "dashboard"

class AnalyticsDashboard:
    def __init__(self):
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.memory = get_memory()
    
    def generate_dashboard(self) -> Path:
        """Generate HTML dashboard with all analytics."""
        
        # Get data
        analytics = self.memory.get_all_analytics()
        total_videos = len(analytics)
        avg_views = self.memory.get_avg_views()
        total_revenue = self.memory.get_total_revenue()
        best_topics = self.memory.get_best_topics()
        recent_mistakes = self.memory.get_recent_mistakes()
        
        # Prepare chart data
        views_data = [a.get("views", 0) for a in analytics]
        labels = [a.get("topic", f"Video {i+1}")[:15] for i, a in enumerate(analytics)]
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Documentary Engine Analytics</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; }}
        h1 {{ text-align: center; margin-bottom: 30px; color: #22c55e; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: #1e293b; padding: 20px; border-radius: 12px; text-align: center; }}
        .stat-value {{ font-size: 32px; font-weight: bold; color: #22c55e; }}
        .stat-label {{ color: #94a3b8; margin-top: 5px; }}
        .charts {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .chart-box {{ background: #1e293b; padding: 20px; border-radius: 12px; }}
        .chart-box h3 {{ margin-bottom: 15px; color: #f8fafc; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ color: #94a3b8; }}
        .positive {{ color: #22c55e; }}
        .negative {{ color: #ef4444; }}
    </style>
</head>
<body>
    <h1>📊 Documentary Engine Analytics</h1>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{total_videos}</div>
            <div class="stat-label">Total Videos</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{int(avg_views)}</div>
            <div class="stat-label">Avg Views</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${total_revenue:.2f}</div>
            <div class="stat-label">Total Revenue</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(recent_mistakes)}</div>
            <div class="stat-label">Mistakes Logged</div>
        </div>
    </div>
    
    <div class="charts">
        <div class="chart-box">
            <h3>📈 Views Per Video</h3>
            <canvas id="viewsChart"></canvas>
        </div>
        <div class="chart-box">
            <h3>🏆 Best Performing Topics</h3>
            <canvas id="topicsChart"></canvas>
        </div>
    </div>
    
    <div class="chart-box" style="margin-top: 20px;">
        <h3>📝 Recent Mistakes & Fixes</h3>
        <table>
            <tr><th>Date</th><th>Type</th><th>Description</th><th>Fix Applied</th></tr>
"""
        
        for m in recent_mistakes[:5]:
            html += f"""<tr>
                <td>{m.get('date', '')[:10]}</td>
                <td>{m.get('type', '')}</td>
                <td>{m.get('description', '')[:50]}</td>
                <td>{m.get('fix_applied', '')[:50]}</td>
            </tr>
"""
        
        html += """</table>
    </div>
    
    <script>
        const viewsCtx = document.getElementById('viewsChart').getContext('2d');
        new Chart(viewsCtx, {
            type: 'bar',
            data: {
                labels: """ + json.dumps(labels) + """,
                datasets: [{
                    label: 'Views',
                    data: """ + json.dumps(views_data) + """,
                    backgroundColor: '#22c55e'
                }]
            },
            options: { responsive: true, plugins: { legend: { display: false } } }
        });
        
        const topicsCtx = document.getElementById('topicsChart').getContext('2d');
        new Chart(topicsCtx, {
            type: 'doughnut',
            data: {
                labels: """ + json.dumps([t[0] for t in best_topics]) + """,
                datasets: [{
                    data: """ + json.dumps([t[1] for t in best_topics]) + """,
                    backgroundColor: ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6']
                }]
            }
        });
    </script>
</body>
</html>"""
        
        output_path = self.output_dir / "dashboard.html"
        output_path.write_text(html)
        
        print(f"Dashboard: {output_path}")
        return output_path

if __name__ == "__main__":
    dash = AnalyticsDashboard()
    dash.generate_dashboard()
    print("Analytics Dashboard Ready")