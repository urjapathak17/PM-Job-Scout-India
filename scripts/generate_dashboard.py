# FILE 2: scripts/generate_dashboard.py
# Copy everything below this line for your second file

import json
import os
from datetime import datetime, timedelta
from jinja2 import Template

def generate_dashboard():
    """Generate beautiful HTML dashboard from jobs data"""
    
    # Load jobs data
    jobs_file = 'data/jobs.json'
    jobs = []
    
    if os.path.exists(jobs_file):
        try:
            with open(jobs_file, 'r') as f:
                jobs = json.load(f)
        except json.JSONDecodeError:
            jobs = []
    
    # Calculate statistics
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    new_today = len([j for j in jobs if j.get('date_found') == today])
    new_yesterday = len([j for j in jobs if j.get('date_found') == yesterday])
    
    companies = list(set(j.get('company', 'Unknown') for j in jobs if j.get('company')))
    cities = list(set(j.get('location', 'Unknown').split(',')[0].strip() for j in jobs if j.get('location')))
    
    # Sort jobs by date (newest first)
    jobs.sort(key=lambda x: x.get('date_found', '1900-01-01'), reverse=True)
    
    # HTML template
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 Product Manager Jobs Dashboard</title>
    <meta name="description" content="Automated daily Product Manager job search from ATS career sites in India">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
        }
        
        .header {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 40px;
            text-align: center;
            position: relative;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="20" cy="20" r="2" fill="rgba(255,255,255,0.1)"/><circle cx="80" cy="40" r="1.5" fill="rgba(255,255,255,0.1)"/><circle cx="40" cy="80" r="1" fill="rgba(255,255,255,0.1)"/></svg>');
        }
        
        .header-content {
            position: relative;
            z-index: 1;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 700;
        }
        
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
            margin-bottom: 5px;
        }
        
        .update-time {
            font-size: 0.9rem;
            opacity: 0.7;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8fafc;
        }
        
        .stat-card {
            background: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: 1px solid rgba(0,0,0,0.05);
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
        }
        
        .stat-label {
            color: #64748b;
            font-size: 1rem;
            font-weight: 500;
        }
        
        .jobs-section {
            padding: 40px;
        }
        
        .section-header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .section-title {
            font-size: 2rem;
            color: #1e293b;
            margin-bottom: 10px;
            font-weight: 600;
        }
        
        .section-subtitle {
            color: #64748b;
            font-size: 1.1rem;
        }
        
        .jobs-grid {
            display: grid;
            gap: 25px;
        }
        
        .job-card {
            background: white;
            border: 2px solid #f1f5f9;
            border-radius: 15px;
            padding: 30px;
            transition: all 0.3s ease;
            position: relative;
        }
        
        .job-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            border-color: #667eea;
        }
        
        .job-card.new-job {
            border-color: #10b981;
            background: linear-gradient(135deg, #f0fdf4, #ffffff);
        }
        
        .job-card.new-job::before {
            content: 'NEW';
            position: absolute;
            top: 15px;
            right: 15px;
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .job-title {
            font-size: 1.4rem;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 12px;
            line-height: 1.3;
        }
        
        .job-company {
            color: #667eea;
            font-weight: 600;
            font-size: 1.1rem;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
        }
        
        .job-location {
            color: #64748b;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }
        
        .job-snippet {
            color: #475569;
            line-height: 1.6;
            margin-bottom: 20px;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .job-actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .apply-btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            text-decoration: none;
            padding: 12px 24px;
            border-radius: 10px;
            font-weight: 600;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .apply-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }
        
        .job-date {
            color: #94a3b8;
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        .no-jobs {
            text-align: center;
            padding: 80px 20px;
            color: #64748b;
        }
        
        .no-jobs h3 {
            font-size: 1.5rem;
            margin-bottom: 10px;
        }
        
        .footer {
            background: #1e293b;
            color: white;
            padding: 40px;
            text-align: center;
        }
        
        .footer-content {
            max-width: 600px;
            margin: 0 auto;
        }
        
        .footer h3 {
            margin-bottom: 15px;
            font-size: 1.2rem;
        }
        
        .footer p {
            opacity: 0.8;
            margin-bottom: 10px;
        }
        
        .github-link {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }
        
        .github-link:hover {
            text-decoration: underline;
        }
        
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .stats {
                grid-template-columns: repeat(2, 1fr);
                padding: 30px 20px;
            }
            
            .jobs-section {
                padding: 30px 20px;
            }
            
            .job-card {
                padding: 20px;
            }
            
            .job-actions {
                flex-direction: column;
                gap: 15px;
                align-items: stretch;
            }
            
            .apply-btn {
                text-align: center;
                justify-content: center;
            }
        }
        
        .icon {
            margin-right: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="header-content">
                <h1>🎯 Product Manager Jobs</h1>
                <p>Automated daily search from ATS career sites across India</p>
                <div class="update-time">Last updated: {{ last_updated }}</div>
            </div>
        </header>
        
        <section class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ total_jobs }}</div>
                <div class="stat-label">Total Jobs Tracked</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ new_today }}</div>
                <div class="stat-label">New Today</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ unique_companies }}</div>
                <div class="stat-label">Companies</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ unique_cities }}</div>
                <div class="stat-label">Cities</div>
            </div>
        </section>
        
        <section class="jobs-section">
            <div class="section-header">
                <h2 class="section-title">Latest Opportunities</h2>
                <p class="section-subtitle">Curated from Workday, Greenhouse, Lever, and 12+ other ATS platforms</p>
            </div>
            
            <div class="jobs-grid">
                {% if jobs %}
                    {% for job in jobs %}
                    <div class="job-card {% if job.date_found == today %}new-job{% endif %}">
                        <h3 class="job-title">{{ job.title }}</h3>
                        <div class="job-company">
                            <span class="icon">🏢</span>
                            {{ job.company }}
                        </div>
                        <div class="job-location">
                            <span class="icon">📍</span>
                            {{ job.location }}
                        </div>
                        {% if job.snippet and job.snippet != 'No description available' %}
                        <div class="job-snippet">{{ job.snippet }}</div>
                        {% endif %}
                        <div class="job-actions">
                            <a href="{{ job.link }}" target="_blank" class="apply-btn">
                                Apply Now 
                                <span>→</span>
                            </a>
                            <div class="job-date">
                                Found: {{ job.date_found }}
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <div class="no-jobs">
                        <h3>🔍 No jobs found yet</h3>
                        <p>The automation will start finding opportunities soon!</p>
                        <p>Jobs are searched daily at 8:00 AM IST from major ATS platforms.</p>
                    </div>
                {% endif %}
            </div>
        </section>
        
        <footer class="footer">
            <div class="footer-content">
                <h3>🤖 Powered by GitHub Actions</h3>
                <p>This dashboard updates automatically every day at 8:00 AM IST</p>
                <p>Searching 15+ ATS career sites for authentic Product Manager opportunities</p>
                <p>
                    <a href="https://github.com" class="github-link">
                        View Source Code & Setup Instructions →
                    </a>
                </p>
            </div>
        </footer>
    </div>
</body>
</html>"""
    
    # Render the template
    template = Template(html_template)
    html_content = template.render(
        jobs=jobs[:100],  # Show latest 100 jobs
        total_jobs=len(jobs),
        new_today=new_today,
        unique_companies=len(companies),
        unique_cities=len(cities),
        today=today,
        last_updated=datetime.now().strftime('%B %d, %Y at %H:%M IST')
    )
    
    # Create docs directory and save HTML
    os.makedirs('docs', exist_ok=True)
    with open('docs/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Also create a simple jobs JSON API endpoint
    with open('docs/jobs.json', 'w', encoding='utf-8') as f:
        json.dump({
            'total_jobs': len(jobs),
            'new_today': new_today,
            'companies': len(companies),
            'cities': len(cities),
            'last_updated': datetime.now().isoformat(),
            'jobs': jobs[:50]  # Latest 50 for API
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Dashboard generated with {len(jobs)} jobs ({new_today} new today)")
    print(f"📊 Tracking {len(companies)} companies across {len(cities)} cities")

if __name__ == "__main__":
    generate_dashboard()

# END OF FILE 2
